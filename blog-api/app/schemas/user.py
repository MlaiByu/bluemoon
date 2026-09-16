"""用户 / 认证 schema"""
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

# 轻量邮箱校验（不引入 email-validator 依赖）：够用即可，避免装库只为一条正则
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


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
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_strength(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("密码不能为空白字符")
        # 至少包含两类字符（字母 / 数字 / 符号），挡住 "11111111" 这类弱口令
        classes = sum(
            bool(re.search(p, v)) for p in (r"[A-Za-z]", r"\d", r"[^A-Za-z0-9]")
        )
        if classes < 2:
            raise ValueError("密码需同时包含字母、数字或符号中的至少两类")
        return v


class UserUpdateIn(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=120)
    avatar: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v
