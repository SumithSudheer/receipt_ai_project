import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ReceiptFile
from PyPDF2 import PdfReader

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/validate/{file_id}")
async def validate_receipt(file_id: int, db: Session = Depends(get_db)):
    # Fetch file record
    receipt_file = db.query(ReceiptFile).filter(ReceiptFile.id == file_id).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(receipt_file.file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    try:
        # Try reading PDF to validate
        reader = PdfReader(receipt_file.file_path)
        _ = len(reader.pages)  # Access pages to confirm it's valid
        receipt_file.is_valid = True
        receipt_file.invalid_reason = None
    except Exception as e:
        receipt_file.is_valid = False
        receipt_file.invalid_reason = str(e)

    db.commit()
    db.refresh(receipt_file)

    return {
        "file_id": receipt_file.id,
        "is_valid": receipt_file.is_valid,
        "invalid_reason": receipt_file.invalid_reason
    }
