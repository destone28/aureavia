from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = None
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    status: UserStatus | None = None
    fcm_token: str | None = None


class UserResponse(UserBase):
    id: UUID
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)
