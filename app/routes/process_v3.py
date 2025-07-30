import os
import re
import fitz
import pytesseract
from PIL import Image
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ReceiptFile, Receipt

router = APIRouter()

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def pdf_to_image(pdf_path):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap()
    img_path = pdf_path.replace(".pdf", ".png")
    pix.save(img_path)
    return img_path

def extract_text_with_tesseract(img_path):
    image = Image.open(img_path)
    return pytesseract.image_to_string(image)

def extract_fields(text):
    # Find merchant name: first non-empty line, avoid keywords
    lines = text.splitlines()
    merchant_name = "Unknown"
    for line in lines:
        if line.strip() and not re.search(r"(date|ref|invoice|total|amount|number|bill|receipt)", line, re.I):
            merchant_name = line.strip()
            break

    # Find all date patterns
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    purchased_at = date_match.group(1) if date_match else None

    # Find all amount-looking numbers
    amounts = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d{2})", text)
    total_amount = 0
    if amounts:
        try:
            total_amount = max(float(a.replace(",", "")) for a in amounts)
        except:
            total_amount = 0

    return {
        "merchant_name": merchant_name,
        "purchased_at": purchased_at,
        "total_amount": total_amount
    }

@router.post("/process_v3/{file_id}")
async def process_v3(file_id: int, db: Session = Depends(get_db)):
    receipt_file = db.query(ReceiptFile).filter(ReceiptFile.id == file_id).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not receipt_file.is_valid:
        raise HTTPException(status_code=400, detail="File is not validated as a PDF")
    if not os.path.exists(receipt_file.file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    # Convert PDF to image
    img_path = pdf_to_image(receipt_file.file_path)

    # OCR text
    raw_text = extract_text_with_tesseract(img_path)

    # Local rule-based extraction
    fields = extract_fields(raw_text)

    # Store in DB
    receipt = Receipt(
        merchant_name=fields["merchant_name"],
        purchased_at=fields["purchased_at"],
        total_amount=fields["total_amount"],
        file_path=receipt_file.file_path,
        raw_text=raw_text
    )
    db.add(receipt)
    receipt_file.is_processed = True
    db.commit()
    db.refresh(receipt)

    return {
        "message": "Processed locally using Tesseract + rule-based extraction",
        "receipt_id": receipt.id,
        "merchant_name": fields["merchant_name"],
        "total_amount": fields["total_amount"],
        "purchased_at": fields["purchased_at"]
    }
