"""用户 / 认证 schema"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class UserBrief(ORMModel):
    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None


class UserOut(ORMModel):
    id: int
    username: str
    email: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    bio: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    last_login_at: datetime | None = None
    created_at: datetime


class LoginIn(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ChangePasswordIn(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_strength(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("密码不能为空白字符")
        return v


class UserUpdateIn(BaseModel):
    nickname: str | None = None
    email: str | None = None
    avatar: str | None = None
    bio: str | None = None
