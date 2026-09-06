"""文章 schema"""
from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from app.schemas.category import CategoryBrief
from app.schemas.common import ORMModel
from app.schemas.user import UserBrief


class PostIn(ORMModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(default=None, max_length=200)
    summary: Optional[str] = Field(default=None, max_length=500)
    content: str = Field(default="", description="Markdown 正文")
    cover: Optional[str] = Field(default=None, max_length=500)
    status: int = Field(default=1, ge=0, le=1, description="0草稿 1发布")
    is_top: bool = False
    category_id: Optional[int] = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None


class PostOut(ORMModel):
    """列表 / 详情通用输出（详情时 content 有值）"""

    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    content: Optional[str] = None
    cover: Optional[str] = None
    status: int = 1
    is_top: bool = False
    views: int = 0
    word_count: int = 0
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    category_id: Optional[int] = None
    category: Optional[CategoryBrief] = None
    author: Optional[UserBrief] = None


class ArchiveItem(ORMModel):
    """归档：按年月分组"""

    year: int
    month: int
    count: int
    posts: List[PostOut] = Field(default_factory=list)


class PostQuery(ORMModel):
    page: int = 1
    page_size: int = 10
    keyword: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[int] = None
    order_by: str = "default"  # default | views | latest
