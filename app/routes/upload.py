import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ReceiptFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Insert metadata in DB
    receipt_file = ReceiptFile(
        file_name=file.filename,
        file_path=file_path,
        is_valid=False,  # Default: not validated yet
        invalid_reason=None,
        is_processed=False
    )

    db.add(receipt_file)
    db.commit()
    db.refresh(receipt_file)

    return {
        "message": "File uploaded successfully",
        "file_id": receipt_file.id,
        "file_name": receipt_file.file_name,
        "file_path": receipt_file.file_path
    }
