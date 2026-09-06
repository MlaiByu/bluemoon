"""分类业务层"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException
from app.models.category import Category
from app.models.post import Post, PostStatus
from app.services.cache import K_CATEGORIES, cache, invalidate_taxonomy, make_key
from app.utils.slug import slugify, unique_slug


def _cat_counts(db: Session) -> dict:
    rows = db.execute(
        select(Post.category_id, func.count(Post.id))
        .where(Post.status == PostStatus.PUBLISHED, Post.category_id.isnot(None))
        .group_by(Post.category_id)
    ).all()
    return {r[0]: r[1] for r in rows}


# ---------------- 分类 ----------------
def list_categories(db: Session, with_count: bool = True) -> List[dict]:
    cache_key = make_key(K_CATEGORIES)

    def _producer():
        cats = db.query(Category).order_by(Category.sort_order.desc(), Category.id.asc()).all()
        counts = _cat_counts(db) if with_count else {}
        return [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "sort_order": c.sort_order,
                "post_count": counts.get(c.id, 0),
            }
            for c in cats
        ]

    return cache.get_or_set(cache_key, _producer, ttl=settings.CACHE_TTL_STATS)


def create_category(db: Session, name: str, slug: Optional[str], description: Optional[str], sort_order: int = 0) -> Category:
    base = slugify(slug or name) or "cat"

    def exists(s: str) -> bool:
        return db.query(db.query(Category.id).filter(Category.slug == s).exists()).scalar()

    cat = Category(
        name=name.strip(),
        slug=unique_slug(base, exists),
        description=description,
        sort_order=sort_order,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    invalidate_taxonomy()
    return cat


def update_category(db: Session, cat_id: int, name: str, slug: Optional[str], description: Optional[str], sort_order: int) -> Category:
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise NotFoundException("分类不存在")
    cat.name = name.strip()
    if slug and slug != cat.slug:
        def exists(s: str) -> bool:
            return db.query(
                db.query(Category.id).filter(Category.slug == s, Category.id != cat_id).exists()
            ).scalar()

        cat.slug = unique_slug(slugify(slug) or "cat", exists)
    cat.description = description
    cat.sort_order = sort_order
    db.commit()
    db.refresh(cat)
    invalidate_taxonomy()
    return cat


def delete_category(db: Session, cat_id: int) -> None:
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise NotFoundException("分类不存在")
    used = (
        db.query(func.count(Post.id))
        .filter(Post.category_id == cat_id, Post.status == PostStatus.PUBLISHED)
        .scalar()
        or 0
    )
    if used:
        raise ConflictException(f"该分类下还有 {used} 篇已发布文章，无法删除")
    db.delete(cat)
    db.commit()
    invalidate_taxonomy()
