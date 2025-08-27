import cv2
from pytesseract import image_to_string
import re
from app.fileUpload import uploadImageIPFS

def imageToString(image):
    im = cv2.imread(image)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    cv2.imwrite('temp_image.png', binary_image)
    text = image_to_string(binary_image)
    print(text)
    print("cid:",uploadImageIPFS(image))
    adhaar_no = re.search(r"\b\d{4}\s\d{4}\s\d{4}", text)
    dob = re.search(r"DOB[:\-]?\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})", text)
    gender = re.search(r"(Male|Female)", text)
    name = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3})\b", text)
    print("dob:", dob)
    print(gender)
    print("Adhaar:", adhaar_no)
    print("name", name)

imageToString(r"C:\Users\sanma\OneDrive\Pictures\IMG_20250827_164556380.jpg")