"""用户历史头像模型

用户更换头像时不再删除旧文件，而是归档保留：
- 每个头像文件对应一条记录（URL / 文件名 / 大小 / 是否当前使用）；
- 支持查询历史列表（按 created_at 倒序）与从历史恢复为当前头像；
- 数量上限与过期清理策略见 app.core.config 的 AVATAR_HISTORY_* 配置。
"""
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin


class UserAvatar(Base, PKMixin, TimestampMixin):
    __tablename__ = "user_avatars"
    __table_args__ = (
        Index("idx_user_avatars_user_created", "user_id", "created_at"),
        Index("idx_user_avatars_user_current", "user_id", "is_current"),
        {"comment": "用户历史头像表"},
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False, comment="头像URL")
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="文件名")
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="文件大小(字节)")
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否为当前使用的头像"
    )

    user: Mapped["User"] = relationship(back_populates="avatars")  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserAvatar {self.id} user={self.user_id} current={self.is_current}>"
