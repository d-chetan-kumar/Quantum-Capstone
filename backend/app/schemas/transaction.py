from pydantic import BaseModel, Field, field_validator, model_validator, field_serializer
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List

class TransactionBase(BaseModel):
    transaction_type: str = Field(..., description="Type of transaction, e.g., TRANSFER, PAYMENT, CASH_IN, CASH_OUT, DEBIT")
    amount: float = Field(..., gt=0, description="Transaction amount must be greater than 0")
    sender_id: str = Field(..., description="Sender account identifier, e.g., C12345678")
    receiver_id: str = Field(..., description="Receiver account identifier, e.g., M98765432")
    location: Optional[str] = None
    is_simulated: bool = False

    @field_validator('sender_id', 'receiver_id', mode='before')
    @classmethod
    def sanitize_party_id(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("Account identifier cannot be empty or whitespace.")
        s = v.strip()
        if len(s) < 2 or len(s) > 64:
            raise ValueError("Account identifier must be between 2 and 64 characters.")
        return s

    @field_validator('transaction_type', mode='before')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"}
        if not v or not isinstance(v, str) or v.strip().upper() not in valid_types:
            raise ValueError(f"Invalid transaction_type. Must be one of {sorted(list(valid_types))}")
        return v.strip().upper()

    @model_validator(mode='after')
    def validate_different_parties(self):
        if self.sender_id == self.receiver_id:
            raise ValueError("Sender ID and Receiver ID cannot be identical.")
        return self

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    transaction_id: UUID
    timestamp: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer('timestamp', 'created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
