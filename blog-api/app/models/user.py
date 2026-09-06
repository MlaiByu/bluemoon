"""用户（管理员）模型"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin


class User(Base, PKMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = ({"comment": "用户/管理员表"},)

    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="用户名"
    )
    email: Mapped[str | None] = mapped_column(String(120), nullable=True, comment="邮箱")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="头像URL")
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="简介")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否管理员"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最近登录时间"
    )

    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        back_populates="author", lazy="dynamic"
    )

    @property
    def display_name(self) -> str:
        return self.nickname or self.username

    def __repr__(self) -> str:
        return f"<User {self.username}>"
