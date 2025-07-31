from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class ReceiptResponse(BaseModel):
    id: int
    purchased_at: Optional[datetime]=None
    merchant_name: Optional[str] =None
    total_amount: Optional[float] = None
    file_path: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True  # This replaces orm_mode
    }
    
    @field_validator("purchased_at", mode="before")
    def parse_date(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%m/%d/%Y")
            except ValueError:
                return None
        return value


class ReceiptListResponse(BaseModel):
    receipts: list[ReceiptResponse]
    total: int
