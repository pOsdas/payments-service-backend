# app/api/v1/schemas/payment.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.core.models.outbox_event import OutboxEventStatus
from app.core.models.payment import PaymentCurrency, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)
    currency: PaymentCurrency
    description: str = Field(..., min_length=1, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class PaymentCreateResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: Decimal
    currency: PaymentCurrency
    description: str
    metadata_json: dict[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None


class OutboxEventPayload(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: PaymentCurrency
    description: str
    metadata: dict[str, Any]
    webhook_url: str


class OutboxEventResponse(BaseModel):
    id: UUID
    event_type: str
    aggregate_id: UUID
    payload: dict[str, Any]
    status: OutboxEventStatus
    attempts: int
    last_error: str | None
    created_at: datetime
    published_at: datetime | None