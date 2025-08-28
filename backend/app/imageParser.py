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
    binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    cv2.imwrite('temp_image.png', binary_image)
    text = image_to_string(binary_image)
    print(text)
    if(doc == 'Aadhar Card'):
        return aadhar_text(text)
    

def aadhar_text(text: str):
    adhaar_no = re.search(r"\b\d{4}\s\d{4}\s\d{4}", text)
    dob = re.search(r"DOB[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})", text)
    gender = re.search(r"(Male|Female)", text)
    name = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3})\b", text)
    print("dob:", dob)
    print(gender)
    print("Adhaar:", adhaar_no)
    print("name", name)
    if dob or gender or adhaar_no or name:
        return "error"
    return {
        "dob": dob.group() if dob else None,
        "gender": gender.group() if gender else None,
        "name": name.group() if name else None,
        "AadharNo": adhaar_no.group() if adhaar_no else None
    }

# def panCard_text(text: str):
#     dob = re.search(r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text)
#     pan_no = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])", text, re.IGNORECASE)

#     print("dob:",dob)
#     print("pan no:", pan_no)
#     if dob == None or pan_no == None:
#         return "error"
#     return {
#         "dob": dob.group() if dob else None,
#         "pan no": pan_no.group() if pan_no else None
#     }
