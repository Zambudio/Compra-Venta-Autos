from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.users.models import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole


class LogoutResponse(BaseModel):
    success: bool = True
