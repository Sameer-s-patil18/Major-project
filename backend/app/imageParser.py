import cv2
from pytesseract import image_to_string
import re
from fastapi import UploadFile
import numpy as np

def imageToString(uploadFile: UploadFile, doc: str):
    file_bytes = np.frombuffer(uploadFile.file.read(), np.uint8)
    im = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    # im = cv2.imread(uploadFile)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    binary_image = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    cv2.imwrite('temp_image.png', binary_image)
    text = image_to_string(binary_image, lang="eng+kan+hin")
    print(text)
    if doc == 'Aadhar Card' :
        return aadhar_text(text)
    if doc == "Pan Card" :
       return panCard_text(text)
    if doc == "Driver's License":
        return DL_text(text)
    

def aadhar_text(text: str):
    adhaar_no = re.search(r"\b\d{4}\s\d{4}\s\d{4}", text)
    dob = re.search(r"DOB?\s[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})", text)
    gender = re.search(r"(Male|Female)", text)
    name = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if ("My Aadhaar" in line) or ("ನನ್ನ ಆಧಾರ್" in line):
            if i + 1 < len(lines):
                candidate = lines[i+1]
                # Filter out DOB / Gender type lines
                if not re.search(r"\d{2}[\/\-]\d{2}[\/\-]\d{4}", candidate) and not re.search(r"(Male|Female)", candidate, re.IGNORECASE):
                    name = candidate
            break
    print("dob:", dob)
    print(gender)
    print("Adhaar:", adhaar_no)
    print("name:", name)
    if dob == None or gender == None or adhaar_no == None or name == None:
        return "error"
    return {
        "text": text,
        "dob": dob.group(1) if dob else None,
        "gender": gender.group() if gender else None,
        "name": name, 
        "AadharNo": adhaar_no.group() if adhaar_no else None
    }



def panCard_text(text: str):
    dob = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text)
    pan_no = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])", text, re.IGNORECASE)

    print("dob:",dob)
    print("pan no:", pan_no)
    if dob == None or pan_no == None:
        return "error"
    return {
        "dob": dob.group() if dob else None,
        "pan no": pan_no.group() if pan_no else None
    }

def DL_text(text: str):
    name = re.search(r"NAME\s*:?\s*([A-Z\s]+)", text)
    dob = re.search(r"D\.?O\.?B\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{4})", text)
    print("name:", name)
    print("dob:", dob)
    if dob == None or name == None:
        return "error"
    return {
        "name": name.group(1) if name else None,
        "dob": dob.group(1) if dob else None,
    }