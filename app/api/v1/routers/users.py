from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.schemas.user import UserMeResponse
from app.core.models import User


router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserMeResponse,
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )