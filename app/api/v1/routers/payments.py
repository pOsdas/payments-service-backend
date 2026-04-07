from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.schemas.payment import PaymentResponse
from app.core.models import Payment, User


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get(
    "/me",
    response_model=list[PaymentResponse],
)
async def get_my_payments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[PaymentResponse]:
    stmt = (
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
    )
    result = await session.execute(stmt)
    payments = result.scalars().all()

    return [
        PaymentResponse(
            id=payment.id,
            transaction_id=payment.transaction_id,
            user_id=payment.user_id,
            account_id=payment.account_id,
            amount=payment.amount,
            created_at=payment.created_at,
        )
        for payment in payments
    ]