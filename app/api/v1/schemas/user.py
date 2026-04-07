from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserMeResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=255)
    is_admin: bool = False


class AdminUserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=255)
    is_admin: bool | None = None


class UserListResponseItem(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime