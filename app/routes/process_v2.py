import os
import re
import json
import fitz  # PyMuPDF
from PIL import Image
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from transformers import DonutProcessor, VisionEncoderDecoderModel

from app.database import SessionLocal
from app.models import ReceiptFile, Receipt

router = APIRouter()

# Load Donut model and processor once
processor = DonutProcessor.from_pretrained("katanaml-org/invoices-donut-model-v1")
model = VisionEncoderDecoderModel.from_pretrained("katanaml-org/invoices-donut-model-v1")

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/process_v2/{file_id}")
async def process_v2(file_id: int, db: Session = Depends(get_db)):
    # Fetch file from DB
    receipt_file = db.query(ReceiptFile).filter(ReceiptFile.id == file_id).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not receipt_file.is_valid:
        raise HTTPException(status_code=400, detail="File is not validated as a PDF")

    if not os.path.exists(receipt_file.file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    # Convert PDF -> Image (first page)
    doc = fitz.open(receipt_file.file_path)
    pix = doc[0].get_pixmap()
    img_path = receipt_file.file_path.replace(".pdf", ".png")
    pix.save(img_path)

    # OCR using Donut
    image = Image.open(img_path).convert("RGB")
    pixel_values = processor(image, return_tensors="pt").pixel_values

    output_ids = model.generate(pixel_values, max_length=1024)
    result_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    # Prepare parsed_data
    parsed_data = {"raw_output": result_text}

    # Regex-based extraction from Donut tags
    def extract_tag(tag):
        match = re.search(fr"<{tag}>(.*?)</{tag}>", result_text)
        return match.group(1).strip() if match else None

    # Extract fields
    purchased_at = extract_tag("s_date") or extract_tag("s_document_date")
    merchant_name = extract_tag("s_invoice_no") or extract_tag("s_supplier") or "Unknown"

    # Extract last gross worth as total amount
    amount_matches = re.findall(r"<s_item_gross_worth>(.*?)</s_item_gross_worth>", result_text)
    total_amount = amount_matches[-1].strip() if amount_matches else "0"

    # Convert amount to float
    try:
        total_amount = float(total_amount.replace(",", "").replace("$", ""))
    except:
        total_amount = 0.0

    # Save to DB
    receipt = Receipt(
        purchased_at=purchased_at,
        merchant_name=merchant_name,
        total_amount=total_amount,
        file_path=receipt_file.file_path,
        raw_text=json.dumps(parsed_data)  # full raw_output stored for debugging
    )
    db.add(receipt)

    # Mark file as processed
    receipt_file.is_processed = True

    db.commit()
    db.refresh(receipt)

    return {
        "message": "Receipt processed with AI successfully",
        "receipt_id": receipt.id,
        "merchant_name": merchant_name,
        "total_amount": total_amount,
        "purchased_at": purchased_at,
        "raw_tags": parsed_data["raw_output"][:500] + "..."  # preview first 500 chars
    }
