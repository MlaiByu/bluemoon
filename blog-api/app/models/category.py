"""分类模型"""
from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin


class Category(Base, PKMixin, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uk_categories_slug"),
        {"comment": "分类表"},
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名")
    slug: Mapped[str] = mapped_column(String(100), nullable=False, comment="别名")
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="描述"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序值，越大越靠前"
    )

    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        back_populates="category", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
