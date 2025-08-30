import cv2
import re
import numpy as np
from fastapi import UploadFile
import easyocr
from transformers import pipeline
from accelerate import Accelerator

# Initialize HuggingFace Accelerator
accelerator = Accelerator()
device = 0 if accelerator.device.type == "cuda" else -1  # pipeline uses -1 for CPU

# Load HuggingFace NER model with Accelerate
ner_pipeline = pipeline(
    "ner",
    model="Davlan/xlm-roberta-base-ner-hrl",
    grouped_entities=True,
    device=device
)

# Load EasyOCR reader (English + Kannada)
reader = easyocr.Reader(['en', 'kn'])

def imageToString(uploadFile: UploadFile, doc: str):
    file_bytes = np.frombuffer(uploadFile.file.read(), np.uint8)
    im = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # ===== PREPROCESSING =====
    im = cv2.resize(im, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # ===== OCR with EasyOCR =====
    results = reader.readtext(gray, detail=0)
    text = "\n".join(results)

    print("===== RAW OCR TEXT =====")
    print(text)
    print("========================")

    if doc.lower() == 'aadhar card':
        return aadhar_text(text)


def aadhar_text(text: str):
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # --- Extract Name using HuggingFace NER ---
    name = None
    entities = ner_pipeline(text)
    candidates = []
    for ent in entities:
        if ent['entity_group'] in ["PER", "PERSON"]:
            candidate = re.sub(r"[^A-Za-z\s]", "", ent['word']).strip()
            if len(candidate.split()) >= 2:
                candidates.append(candidate)

    if candidates:
        # Pick longest name candidate
        name = max(candidates, key=len)

    # Fallback: line above DOB
    if not name:
        for i, line in enumerate(lines):
            if "dob" in line.lower() or "date of birth" in line.lower():
                if i > 0:
                    possible_name = re.sub(r"[^A-Za-z\s]", "", lines[i - 1]).strip()
                    if len(possible_name.split()) >= 2:
                        name = possible_name
                        break

    if name:
        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r"[^A-Za-z\s]", "", name).strip()

    # --- Extract DOB ---
    dob = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text)

    # --- Extract Gender ---
    gender = None
    if re.search(r"\bmale\b", text, re.IGNORECASE):
        gender = "Male"
    elif re.search(r"\bfemale\b", text, re.IGNORECASE):
        gender = "Female"

    # --- Extract Aadhaar Number ---
    aadhaar_no = None
    aadhaar_match = re.findall(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", text)
    if aadhaar_match:
        aadhaar_no = re.sub(r"\D", "", aadhaar_match[0])

    print("===== Extracted Aadhaar Fields =====")
    result = {
        "name": name,
        "dob": dob.group() if dob else None,
        "gender": gender,
        "AadharNo": aadhaar_no
    }
    print(result)
    print("===================================")

    return result
