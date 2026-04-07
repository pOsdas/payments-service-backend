from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: int
    user_id: int
    balance: Decimal
    created_at: datetime
    updated_at: datetime
