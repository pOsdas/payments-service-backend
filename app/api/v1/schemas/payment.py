from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Amount must be greater than 0")
        return value


class PaymentWebhookResponse(BaseModel):
    message: str
    transaction_id: str
    account_id: int
    user_id: int
    amount: Decimal
    balance: Decimal
    created: bool