"""公共 schema"""
from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """允许从 SQLAlchemy 对象直接构造"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 10


class PageResult(BaseModel, Generic[T]):
    list: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0
    has_prev: bool = False
    has_next: bool = False
