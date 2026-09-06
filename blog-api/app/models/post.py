"""文章模型"""
from datetime import datetime
from enum import IntEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin
from app.db.types import IntEnumType


class PostStatus(IntEnum):
    DRAFT = 0
    PUBLISHED = 1


class Post(Base, PKMixin, TimestampMixin):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("slug", name="uk_posts_slug"),
        Index("idx_posts_status_published", "status", "published_at"),
        Index("idx_posts_category", "category_id"),
        {"comment": "文章表"},
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    slug: Mapped[str] = mapped_column(String(200), nullable=False, comment="URL 别名")
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="摘要")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Markdown 正文")
    cover: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="封面图URL")
    status: Mapped[int] = mapped_column(
        IntEnumType(PostStatus),
        nullable=False,
        default=PostStatus.DRAFT,
        comment="0草稿 1已发布",
    )
    is_top: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否置顶"
    )
    views: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="阅读量"
    )
    word_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="字数"
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="发布时间"
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, comment="分类ID"
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="作者ID"
    )

    category: Mapped["Category | None"] = relationship(  # noqa: F821
        back_populates="posts", lazy="joined"
    )
    author: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="posts", lazy="joined"
    )

    @property
    def is_published(self) -> bool:
        return self.status == PostStatus.PUBLISHED

    def __repr__(self) -> str:
        return f"<Post {self.id}:{self.title}>"
