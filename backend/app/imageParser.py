import base64
import json
import cv2
import re
import numpy as np
from fastapi import UploadFile
import easyocr
from transformers import pipeline
from accelerate import Accelerator
from pyzbar import pyzbar
import zlib
import xml.etree.ElementTree as ET

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

    decoded = pyzbar.decode(im)
    print(decoded)
    raw_data = decoded[0].data.decode("utf-8")
    print(raw_data)
    paresed = None
    if raw_data.strip().startswith("<"):
        parsed = text
    
    parsed = json.loads(base64.b64decode(raw_data))
    print(parsed)


    # try:
    #     decompressed = zlib.decompress(raw_data, 16+zlib.MAX_WBITS)
    #     xml_data = decompressed.decode('utf-8')
    #     root = ET.fromstring(xml_data)
    #     print(root.attrib)
    # except Exception as e:
    #     print("Error:", e)

    # ===== PREPROCESSING =====
    im = cv2.resize(im, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # --- Increase contrast (CLAHE) ---
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

    # ===== OCR with EasyOCR =====
    results = reader.readtext(gray, detail=0)
    text = "\n".join(results)

    print("===== RAW OCR TEXT =====")
    print(text)
    print("========================")

    if doc.lower() == 'aadhar card':
        return aadhar_text(text)
    elif(doc == 'Pan Card'):
        return panCard_text(text)
    elif(doc == "Driver's License"):
        return DL_text(text)
    elif(doc == "Voter ID"):
        return voterID_text(text)


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

def panCard_text(text: str):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
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

    dob = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text)

    if not name:
        for i, line in enumerate(lines):
            if dob.group() in line.lower():
                for offset in [1, 2]:  # check 1 above, then 2 above
                    if i - offset >= 0:
                        possible_name = re.sub(r"[^A-Za-z\s]", "", lines[i - offset]).strip()
                        if len(possible_name.split()) >= 2:
                            name = possible_name
                            
                if name:
                    break

    if name:
        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r"[^A-Za-z\s]", "", name).strip()

    pan_no = None
    pan_match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])", text, re.IGNORECASE)
    if pan_match:
        pan_no = pan_match.group()
        
    print("===== Extracted Pan Crad Fields =====")
    result = {
        "name": name,
        "dob": dob.group() if dob else None,
        "Pan": pan_no,
    }
    print(result)
    print("===================================")
    return result

def DL_text(text: str):
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

    if not name:
        for i, line in enumerate(lines):
            if "name" in line.lower():
                possible_name = " ".join(lines[i+1:i+3])
                possible_name = re.sub(r"[^A-Za-z\s]", "", possible_name).strip()
                if len(possible_name.split()) >= 2:
                    name = possible_name
                    break

    if name:
        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r"[^A-Za-z\s]", "", name).strip()

    DLNoSearch = re.search(r"\b[A-Z]{2}\d{2}\s?\d{11}\b", text)

    dob = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text)    
    date = dob.group() if dob else None
    # date = date.removeprefix("D.O.B")
    address = re.search(r"ADDRESS[\s\S]+?(\d{6})", text, flags=re.DOTALL | re.IGNORECASE)


    result = {
        "name": name,
        "dob": date,
        "address": address.group() if address else None,
        "DL_no": DLNoSearch.group() if DLNoSearch else None
    }
    print("-------------------------------------------------------------------------------------")

    print("Ectracted Details:\n", result)

    print("-------------------------------------------------------------------------------------")

    return result


def voterID_text(text: str):

    voterID = re.search(r"\b[A-Z]{3}\d{8}\b", text)

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

    if not name:
        name_match = re.search(r"NAME\s+([A-Za-z]+\s+[A-Za-z]+)", text, flags=re.IGNORECASE)
        if name_match:
            name = name_match.group()

    dob = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text)  

    gender = re.search(r"\b(Male|Female)\b", text, re.IGNORECASE)
    if gender:
        gender = gender.group(1).capitalize()
    else:
        gender = None

    result = {
        "name": name,
        "dob": dob.group() if dob else None,
        "gender": gender,
        "voterId": voterID.group() if voterID else None
    }

    print("-------------------------------------------------------------------------------------")

    print("Ectracted Details:\n", result)

    print("-------------------------------------------------------------------------------------")

    return result
