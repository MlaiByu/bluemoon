"""站点统计业务层"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.category import Category
from app.models.post import Post, PostStatus
from app.models.profile import Profile
from app.models.user import User
from app.services import image_service
from app.services.cache import K_PROFILE, K_SITE, K_STATS, cache, make_key
from app.services.post_service import current_views


def _total_views(db: Session) -> int:
    base = db.query(func.coalesce(func.sum(Post.views), 0)).scalar() or 0
    # 加上 Redis 中未落库的增量
    if cache.available:
        for key in cache.keys("post:views:*"):
            try:
                base += int(cache.get(key) or 0)
            except (TypeError, ValueError):
                continue
    return int(base)


def site_info(db: Session) -> Dict[str, Any]:
    """前台页脚 / 首页头部展示的站点信息"""

    def _producer():
        post_count = (
            db.query(func.count(Post.id)).filter(Post.status == PostStatus.PUBLISHED).scalar() or 0
        )
        return {
            "title": settings.BLOG_TITLE,
            "subtitle": settings.BLOG_SUBTITLE,
            "description": settings.BLOG_DESCRIPTION,
            "author": settings.BLOG_AUTHOR,
            "icp": settings.BLOG_ICP,
            "post_count": post_count,
            "category_count": db.query(func.count(Category.id)).scalar() or 0,
            "total_views": _total_views(db),
            # 首页首屏 banner：取图库最新一张。前端 Home.vue 的 bannerSrc 优先用它，
            # 从而不必等 getImages() 全量返回才发起 banner 图片请求（改善 LCP）。
            "banner": image_service.latest_gallery_image(),
        }

    return cache.get_or_set(make_key(K_SITE), _producer, ttl=settings.CACHE_TTL_STATS)


def overview(db: Session) -> Dict[str, Any]:
    """后台仪表盘数据"""

    def _producer():
        total_posts = db.query(func.count(Post.id)).scalar() or 0
        published = (
            db.query(func.count(Post.id)).filter(Post.status == PostStatus.PUBLISHED).scalar() or 0
        )
        drafts = total_posts - published
        today = datetime.now().date()
        week_ago = datetime.now() - timedelta(days=7)

        new_this_week = (
            db.query(func.count(Post.id)).filter(Post.created_at >= week_ago).scalar() or 0
        )

        # 近 7 天发布趋势
        trend: List[Dict[str, Any]] = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time())
            end = start + timedelta(days=1)
            cnt = (
                db.query(func.count(Post.id))
                .filter(Post.created_at >= start, Post.created_at < end)
                .scalar()
                or 0
            )
            trend.append({"date": day.strftime("%m-%d"), "count": cnt})

        # 分类分布
        cat_rows = (
            db.query(Category.name, func.count(Post.id))
            .join(Post, Post.category_id == Category.id)
            .filter(Post.status == PostStatus.PUBLISHED)
            .group_by(Category.id, Category.name)
            .all()
        )
        # 热门文章 Top5
        top_posts = (
            db.query(Post.id, Post.title, Post.slug, Post.views)
            .filter(Post.status == PostStatus.PUBLISHED)
            .order_by(Post.views.desc(), Post.id.desc())
            .limit(5)
            .all()
        )

        return {
            "total_posts": total_posts,
            "published": published,
            "drafts": drafts,
            "new_this_week": new_this_week,
            "category_count": db.query(func.count(Category.id)).scalar() or 0,
            "total_views": _total_views(db),
            "trend": trend,
            "category_dist": [{"name": r[0], "value": r[1]} for r in cat_rows],
            "top_posts": [
                {
                    "id": r[0],
                    "title": r[1],
                    "slug": r[2],
                    "views": current_views(r[0], r[3]),
                }
                for r in top_posts
            ],
        }

    return cache.get_or_set(
        make_key(K_STATS, kind="overview"), _producer, ttl=settings.CACHE_TTL_STATS
    )


def get_profile(db: Session) -> Profile:
    profile = db.query(Profile).filter(Profile.id == 1).first()
    if profile is None:
        profile = Profile(id=1, nickname=settings.BLOG_AUTHOR)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # 注入管理员头像（前台展示用）
    admin = db.query(User).filter(User.is_superuser == True, User.is_active == True).first()
    if admin and admin.avatar:
        profile.avatar = admin.avatar  # type: ignore[attr-defined]

    return profile


def update_profile(db: Session, data: dict) -> Profile:
    profile = get_profile(db)
    for k, v in data.items():
        if v is not None and hasattr(profile, k):
            setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    cache.delete(make_key(K_SITE))
    cache.delete(make_key(K_PROFILE))
    return profile
