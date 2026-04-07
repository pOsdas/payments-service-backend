from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.schemas.payment import (
    PaymentResponse,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)
from app.core.config import get_settings
from app.core.models import Account, Payment, User
from app.services.webhook import is_valid_webhook_signature


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


@router.post(
    "/webhook",
    response_model=PaymentWebhookResponse,
)
async def process_payment_webhook(
    payload: PaymentWebhookRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentWebhookResponse:
    settings = get_settings()

    is_valid = is_valid_webhook_signature(
        account_id=payload.account_id,
        amount=payload.amount,
        transaction_id=payload.transaction_id,
        user_id=payload.user_id,
        secret_key=settings.payment_webhook_secret,
        signature=payload.signature,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    existing_payment_stmt = select(Payment).where(
        Payment.transaction_id == payload.transaction_id
    )
    existing_payment_result = await session.execute(existing_payment_stmt)
    existing_payment = existing_payment_result.scalar_one_or_none()

    if existing_payment is not None:
        account_stmt = select(Account).where(Account.id == existing_payment.account_id)
        account_result = await session.execute(account_stmt)
        existing_account = account_result.scalar_one()

        return PaymentWebhookResponse(
            message="Transaction already processed",
            transaction_id=existing_payment.transaction_id,
            account_id=existing_payment.account_id,
            user_id=existing_payment.user_id,
            amount=existing_payment.amount,
            balance=existing_account.balance,
            created=False,
        )

    try:
        user_stmt = select(User).where(User.id == payload.user_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        account_stmt = select(Account).where(
            Account.user_id == payload.user_id,
            Account.external_id == payload.account_id,
        )
        account_result = await session.execute(account_stmt)
        account = account_result.scalar_one_or_none()

        if account is None:
            account = Account(
                user_id=payload.user_id,
                external_id=payload.account_id,
                balance=payload.amount,
            )
            session.add(account)
            await session.flush()
        else:
            account.balance += payload.amount

        payment = Payment(
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            account_id=account.id,
            amount=payload.amount,
        )
        session.add(payment)
        await session.flush()

        await session.commit()

    except HTTPException:
        await session.rollback()
        raise

    except IntegrityError:
        await session.rollback()

        existing_payment_stmt = select(Payment).where(
            Payment.transaction_id == payload.transaction_id
        )
        existing_payment_result = await session.execute(existing_payment_stmt)
        existing_payment = existing_payment_result.scalar_one_or_none()

        if existing_payment is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not process transaction due to concurrent update",
            )

        account_stmt = select(Account).where(Account.id == existing_payment.account_id)
        account_result = await session.execute(account_stmt)
        existing_account = account_result.scalar_one()

        return PaymentWebhookResponse(
            message="Transaction already processed",
            transaction_id=existing_payment.transaction_id,
            account_id=existing_payment.account_id,
            user_id=existing_payment.user_id,
            amount=existing_payment.amount,
            balance=existing_account.balance,
            created=False,
        )

    except Exception:
        await session.rollback()
        raise

    return PaymentWebhookResponse(
        message="Payment processed successfully",
        transaction_id=payment.transaction_id,
        account_id=account.id,
        user_id=payment.user_id,
        amount=payment.amount,
        balance=account.balance,
        created=True,
    )