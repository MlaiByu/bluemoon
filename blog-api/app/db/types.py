"""自定义 SQLAlchemy 类型"""
from enum import IntEnum
from typing import Any, Optional

from sqlalchemy import Integer
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class IntEnumType(TypeDecorator):
    """把 IntEnum 以 int 形式写入数据库

    PyMySQL 按 `type(value)` 精确匹配编码器，IntEnum 会落到字符串分支，
    导致 `Incorrect integer value: 'PostStatus.PUBLISHED'`。
    """

    impl = Integer
    cache_ok = True

    def __init__(self, enum_class: Optional[type] = None):
        super().__init__()
        self.enum_class = enum_class

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, IntEnum):
            return int(value)
        return int(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        if value is None or self.enum_class is None:
            return value
        try:
            return self.enum_class(int(value))
        except ValueError:
            return value
