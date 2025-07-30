import os
import re
import fitz
import pytesseract
import layoutparser as lp
import cv2
from PIL import Image
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ReceiptFile, Receipt

router = APIRouter()

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

import pytesseract
from pytesseract import Output

def extract_layout(img_path):
    image = cv2.imread(img_path)
    data = pytesseract.image_to_data(image, output_type=Output.DICT)
    return data

def extract_text_blocks(data):
    blocks = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if text:
            blocks.append(text)
    return blocks

def extract_fields(text_blocks):
    full_text = "\n".join(text_blocks)

    # Merchant name: First non-empty block (avoid common words)
    merchant_name = "Unknown"
    for block in text_blocks:
        if block.strip() and not re.search(r"(date|invoice|total|amount|number|bill|receipt)", block, re.I):
            merchant_name = block.strip()
            break

    # Date
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', full_text)
    purchased_at = date_match.group(1) if date_match else None

    # Total amount (biggest numeric value)
    amounts = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d{2})", full_text)
    total_amount = max([float(a.replace(",", "")) for a in amounts], default=0)

    return {
        "merchant_name": merchant_name,
        "purchased_at": purchased_at,
        "total_amount": total_amount,
        "raw_text": full_text
    }

@router.post("/process_v4/{file_id}")
async def process_v4(file_id: int, db: Session = Depends(get_db)):
    receipt_file = db.query(ReceiptFile).filter(ReceiptFile.id == file_id).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not receipt_file.is_valid:
        raise HTTPException(status_code=400, detail="File is not validated as a PDF")
    if not os.path.exists(receipt_file.file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    # Convert PDF to image
    img_path = pdf_to_image(receipt_file.file_path)

    # Detect layout
    layout = extract_layout(img_path)
    text_blocks = extract_text_blocks(layout)

    # Extract fields
    fields = extract_fields(text_blocks)

    # Save to DB
    receipt = Receipt(
        merchant_name=fields["merchant_name"],
        purchased_at=fields["purchased_at"],
        total_amount=fields["total_amount"],
        file_path=receipt_file.file_path,
        raw_text=fields["raw_text"]
    )
    db.add(receipt)
    receipt_file.is_processed = True
    db.commit()
    db.refresh(receipt)

    return {
        "message": "Processed locally using Tesseract + LayoutParser",
        "receipt_id": receipt.id,
        "merchant_name": fields["merchant_name"],
        "total_amount": fields["total_amount"],
        "purchased_at": fields["purchased_at"]
    }
