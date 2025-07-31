from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from datetime import datetime
from .database import Base

class ReceiptFile(Base):
    __tablename__ = "receipt_file"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    is_valid = Column(Boolean, default=False)
    invalid_reason = Column(String, nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Receipt(Base):
    __tablename__ = "receipt"
    id = Column(Integer, primary_key=True, index=True)
    purchased_at = Column(DateTime, nullable=True)
    merchant_name = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True)
    file_path = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
