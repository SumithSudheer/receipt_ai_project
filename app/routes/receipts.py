from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Receipt
from app.schemas import ReceiptResponse, ReceiptListResponse

router = APIRouter(prefix="/receipts", tags=["Receipts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# ✅ GET /receipts -> Paginated list of receipts
@router.get("/", response_model=ReceiptListResponse)
def list_receipts(
    skip: int = 0,
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    total = db.query(Receipt).count()
    receipts = db.query(Receipt).offset(skip).limit(limit).all()
    return {"receipts": receipts, "total": total}

# ✅ GET /receipts/{id} -> Single receipt details
@router.get("/{id}", response_model=ReceiptResponse)
def get_receipt(id: int, db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.id == id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt
