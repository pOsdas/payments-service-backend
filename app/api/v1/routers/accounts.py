from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.schemas.account import AccountResponse
from app.core.models import Account, User


router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "/me",
    response_model=list[AccountResponse],
)
async def get_my_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AccountResponse]:
    stmt = (
        select(Account)
        .where(Account.user_id == current_user.id)
        .order_by(Account.id.asc())
    )
    result = await session.execute(stmt)
    accounts = result.scalars().all()

    return [
        AccountResponse(
            id=account.id,
            user_id=account.user_id,
            external_id=account.external_id,
            balance=account.balance,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
        for account in accounts
    ]