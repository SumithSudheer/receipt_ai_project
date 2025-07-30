import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ReceiptFile, Receipt
from app.ocr_service import extract_text_from_pdf
from app.gemini_ai import extract_entities_with_gemini

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/process_v5/{file_id}")
async def process_receipt(file_id: int, db: Session = Depends(get_db)):
    # Fetch file
    receipt_file = db.query(ReceiptFile).filter(ReceiptFile.id == file_id).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not receipt_file.is_valid:
        raise HTTPException(status_code=400, detail="File is not validated as a PDF")

    if not os.path.exists(receipt_file.file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    # OCR Extraction
    raw_text = extract_text_from_pdf(receipt_file.file_path)

    # AI Entity Extraction
    entities = extract_entities_with_gemini(raw_text)

    # Store in Receipt table
    receipt = Receipt(
        purchased_at=entities.get("purchased_at"),
        merchant_name=entities.get("merchant_name"),
        total_amount=entities.get("total_amount"),
        file_path=receipt_file.file_path,
        raw_text=raw_text
    )
    db.add(receipt)
    receipt_file.is_processed = True
    db.commit()
    db.refresh(receipt)

    return {
        "message": "Receipt processed successfully",
        "receipt_id": receipt.id,
        "merchant_name": receipt.merchant_name,
        "total_amount": receipt.total_amount,
        "purchased_at": receipt.purchased_at
    }
