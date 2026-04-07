from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_admin, get_db
from app.api.v1.schemas.user import (
    AdminAccountResponse,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    AdminUserWithAccountsResponse,
    UserMeResponse,
)
from app.core.models import User
from app.core.security import hash_password


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/me",
    response_model=UserMeResponse,
)
async def get_admin_me(
    current_admin: Annotated[User, Depends(get_current_admin)],
) -> UserMeResponse:
    return UserMeResponse(
        id=current_admin.id,
        email=current_admin.email,
        full_name=current_admin.full_name,
        is_admin=current_admin.is_admin,
        created_at=current_admin.created_at,
        updated_at=current_admin.updated_at,
    )


@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
async def get_users(
    _: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AdminUserResponse]:
    stmt = select(User).order_by(User.id.asc())
    result = await session.execute(stmt)
    users = result.scalars().all()

    return [
        AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]


@router.post(
    "/users",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: AdminUserCreateRequest,
    _: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUserResponse:
    existing_stmt = select(User).where(User.email == payload.email)
    existing_result = await session.execute(existing_stmt)
    existing_user = existing_result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_admin=payload.is_admin,
    )

    session.add(user)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )

    await session.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserResponse,
)
async def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    _: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUserResponse:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data:
        email_stmt = select(User).where(
            User.email == update_data["email"],
            User.id != user_id,
        )
        email_result = await session.execute(email_stmt)
        email_owner = email_result.scalar_one_or_none()

        if email_owner is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            )
        user.email = update_data["email"]

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]

    if "password" in update_data:
        user.hashed_password = hash_password(update_data["password"])

    if "is_admin" in update_data:
        user.is_admin = update_data["is_admin"]

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        )

    await session.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot delete themselves.",
        )

    await session.delete(user)
    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/users-with-accounts",
    response_model=list[AdminUserWithAccountsResponse],
)
async def get_users_with_accounts(
    _: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AdminUserWithAccountsResponse]:
    stmt = (
        select(User)
        .options(selectinload(User.accounts))
        .order_by(User.id.asc())
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    response: list[AdminUserWithAccountsResponse] = []

    for user in users:
        response.append(
            AdminUserWithAccountsResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_admin=user.is_admin,
                created_at=user.created_at,
                updated_at=user.updated_at,
                accounts=[
                    AdminAccountResponse(
                        id=account.id,
                        user_id=account.user_id,
                        external_id=account.external_id,
                        balance=account.balance,
                        created_at=account.created_at,
                        updated_at=account.updated_at,
                    )
                    for account in sorted(user.accounts, key=lambda acc: acc.id)
                ],
            )
        )

    return response