"""分类 schema"""
from pydantic import Field

from app.schemas.common import ORMModel


class CategoryBrief(ORMModel):
    id: int
    name: str
    slug: str


class CategoryOut(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    sort_order: int = 0
    post_count: int = 0


class CategoryIn(ORMModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = 0
