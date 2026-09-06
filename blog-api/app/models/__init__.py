"""统一导入所有模型，保证 Base.metadata 完整（建表 / Alembic 用）"""
from app.db.base import Base
from app.models.category import Category
from app.models.post import Post, PostStatus
from app.models.profile import Profile
from app.models.user import User

__all__ = ["Base", "Category", "Post", "PostStatus", "Profile", "User"]
