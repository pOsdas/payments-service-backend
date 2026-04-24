from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.payment import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentDetailResponse,
)
from app.api.deps import verify_api_key
from app.core.db_helper import db_helper
from app.services.payment import create_payment, get_payment_by_id


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment_endpoint(
    body: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> PaymentCreateResponse:
    payment = await create_payment(
        session=session,
        data=body,
        idempotency_key=idempotency_key,
    )

    return PaymentCreateResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment_endpoint(
    payment_id: UUID,
    session: AsyncSession = Depends(db_helper.session_getter),
) -> PaymentDetailResponse:
    payment = await get_payment_by_id(
        session=session,
        payment_id=payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return PaymentDetailResponse.model_validate(payment)