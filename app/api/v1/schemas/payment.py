from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentResponse(BaseModel):
    id: int
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    created_at: datetime


class PaymentWebhookRequest(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=128)
    user_id: int
    account_id: int
    amount: Decimal
    signature: str = Field(min_length=64, max_length=64)