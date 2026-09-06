"""文章业务层：列表/详情/增删改/归档 + Redis 缓存"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import match as mysql_match
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException
from app.core.response import clamp_page_size, paginated
from app.models.category import Category
from app.models.post import Post, PostStatus
from app.schemas.post import PostIn
from app.services import image_service
from app.services.cache import (
    K_POST_DETAIL,
    K_POST_DETAIL_ID,
    K_POST_LIST,
    K_POST_VIEW_LOCK,
    K_POST_VIEWS,
    cache,
    hash_key,
    invalidate_post,
    make_key,
)
from app.utils.markdown import count_words, make_summary
from app.utils.slug import slugify, unique_slug

logger = logging.getLogger("bluemoon")

# 阅读量在 Redis 累积到该阈值后回写 MySQL
VIEW_FLUSH_THRESHOLD = 10


# ---------------- 序列化 ----------------
def serialize_post(post: Post, with_content: bool = True) -> Dict[str, Any]:
    """把 Post ORM 对象转成可 JSON 序列化的 dict"""
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "summary": post.summary,
        "content": post.content if with_content else None,
        "cover": post.cover,
        "status": post.status,
        "is_top": bool(post.is_top),
        "views": post.views,
        "word_count": post.word_count,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "category_id": post.category_id,
        "category": (
            {"id": post.category.id, "name": post.category.name, "slug": post.category.slug}
            if post.category
            else None
        ),
        "author": (
            {
                "id": post.author.id,
                "username": post.author.username,
                "nickname": post.author.nickname,
                "avatar": post.author.avatar,
            }
            if post.author
            else None
        ),
    }


def _base_query(db: Session):
    return (
        select(Post)
        .options(selectinload(Post.category))
        .options(selectinload(Post.author))
    )


def _apply_order(stmt, order_by: str):
    """按 order_by 排序：views=热度、latest=创建时间、default=置顶+发布时间"""
    if order_by == "views":
        return stmt.order_by(Post.views.desc(), Post.id.desc())
    if order_by == "latest":
        return stmt.order_by(Post.created_at.desc(), Post.id.desc())
    # default：置顶优先，其次按发布时间倒序
    return stmt.order_by(Post.is_top.desc(), Post.published_at.desc(), Post.id.desc())


# ---------------- 列表 ----------------
def list_posts(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[int] = None,
    order_by: str = "default",
) -> Dict[str, Any]:
    page = max(page, 1)
    page_size = clamp_page_size(page_size)
    params = {
        "page": page,
        "page_size": page_size,
        "keyword": keyword or "",
        "category_id": category_id,
        "status": status,
        "order_by": order_by,
    }
    cache_key = make_key(K_POST_LIST, hash=hash_key(params))

    def _producer() -> Dict[str, Any]:
        stmt = _base_query(db)
        count_stmt = select(func.count(Post.id))

        if keyword:
            # 中文全文检索：依赖 posts 表的 ngram FULLTEXT 索引 ft_search。
            # 用 MySQL 方言的 match() 生成 MATCH ... AGAINST 表达式（默认 NATURAL LANGUAGE MODE）：
            # 同一表达式对象可在 WHERE / ORDER BY 间安全复用且参数自动绑定，
            # 避免手写 text() 的两个坑——TextClause 没有 .desc() 方法、
            # .params() 每次返回副本导致 WHERE 与 ORDER BY 的绑定参数不共享。
            match_expr = mysql_match(
                Post.title, Post.summary, Post.content, against=keyword
            )
            stmt = stmt.where(match_expr)
            count_stmt = count_stmt.where(match_expr)
            # 搜索时按相关度排序，而非发布时间
            stmt = stmt.order_by(match_expr.desc(), Post.id.desc())
        if category_id:
            stmt = stmt.where(Post.category_id == category_id)
            count_stmt = count_stmt.where(Post.category_id == category_id)
        if status is not None:
            stmt = stmt.where(Post.status == status)
            count_stmt = count_stmt.where(Post.status == status)

        total = db.execute(count_stmt).scalar() or 0
        # 有关键字时已在上面按相关度排序；否则按指定排序
        if not keyword:
            stmt = _apply_order(stmt, order_by)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        posts = db.execute(stmt).scalars().unique().all()

        items = [serialize_post(p, with_content=False) for p in posts]
        # 视图数叠加 Redis 中未落库的增量
        for it in items:
            it["views"] = current_views(it["id"], it["views"])
        return paginated(items, total, page, page_size)

    return cache.get_or_set(cache_key, _producer, ttl=settings.CACHE_TTL_POST_LIST)


# ---------------- 详情 ----------------
def current_views(post_id: int, base_views: int) -> int:
    """MySQL 中的基数 + Redis 中尚未回写的增量"""
    if not cache.available:
        return base_views
    delta = cache.get(make_key(K_POST_VIEWS, id=post_id))
    try:
        return base_views + int(delta or 0)
    except (TypeError, ValueError):
        return base_views


def incr_views(db: Session, post_id: int) -> None:
    """阅读量 +1；Redis 累积到阈值后批量回写 MySQL"""
    if not cache.available:
        # 降级：直接写库
        db.query(Post).filter(Post.id == post_id).update({Post.views: Post.views + 1})
        db.commit()
        return

    key = make_key(K_POST_VIEWS, id=post_id)
    try:
        value = cache.incr(key)
        if value is None:
            return
        cache.expire(key, 86400)  # 防止 key 永久残留
        if value >= VIEW_FLUSH_THRESHOLD:
            raw = cache.getset(key, 0)
            # GETSET 会清掉 TTL，需要重新设置
            cache.expire(key, 86400)
            try:
                delta = int(raw or 0)
            except (TypeError, ValueError):
                delta = 0
            if delta > 0:
                db.query(Post).filter(Post.id == post_id).update(
                    {Post.views: Post.views + delta}
                )
                db.commit()
                # 视图变化 → 详情与列表缓存失效
                invalidate_post(post_id=post_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("incr_views failed, fallback to db: %s", exc)
        db.query(Post).filter(Post.id == post_id).update({Post.views: Post.views + 1})
        db.commit()


# 同一 IP 对同一文章的防刷锁时长（秒）
VIEW_LOCK_TTL = 300  # 5 分钟内不重复计数


def record_view(db: Session, post_id: int, ip: str) -> bool:
    """
    上报一次有效阅读。

    防刷规则：
    - 同一 IP 对同一文章 5 分钟内只计一次
    - Redis 不可用时降级为直接 +1（不防刷）
    - 返回 True 表示本次计为有效阅读，False 表示被防刷拦截
    """
    # 1. 文章存在性校验
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        return False

    if not cache.available:
        # Redis 不可用，降级直接 +1
        incr_views(db, post_id)
        return True

    lock_key = make_key(K_POST_VIEW_LOCK, post_id=post_id, ip=ip)

    # 2. 检查防刷锁：如果已存在，说明 5 分钟内已经计过
    if cache.get(lock_key):
        return False

    # 3. 设置防刷锁（先加锁再加阅读量，防止并发穿透）
    cache.set(lock_key, "1", ttl=VIEW_LOCK_TTL)

    # 4. 阅读量 +1
    incr_views(db, post_id)
    return True


def get_post_by_id(db: Session, post_id: int, with_content: bool = True) -> Optional[Post]:
    stmt = _base_query(db).where(Post.id == post_id)
    return db.execute(stmt).scalars().unique().first()


def get_post_by_slug(
    db: Session, slug: str, allow_draft: bool = False
) -> Optional[Post]:
    stmt = _base_query(db).where(Post.slug == slug)
    post = db.execute(stmt).scalars().unique().first()
    if post is None:
        return None
    if not allow_draft and post.status != PostStatus.PUBLISHED:
        return None
    return post


def get_post_detail_cached(db: Session, slug: str, allow_draft: bool = False) -> Dict[str, Any]:
    """带缓存的文章详情（视图数为实时值）"""
    cache_key = make_key(K_POST_DETAIL, slug=slug)

    def _producer() -> Optional[Dict[str, Any]]:
        post = get_post_by_slug(db, slug, allow_draft=allow_draft)
        if post is None:
            return None
        return serialize_post(post, with_content=True)

    data = cache.get_or_set(cache_key, _producer, ttl=settings.CACHE_TTL_POST_DETAIL)
    if data is None:
        return None
    data = dict(data)
    data["views"] = current_views(data["id"], data.get("views", 0))
    return data


# ---------------- 写操作 ----------------
def _ensure_unique_slug(db: Session, raw_slug: Optional[str], title: str, exclude_id: int | None = None) -> str:
    base = slugify(raw_slug or title) or "post"

    def exists(s: str) -> bool:
        q = db.query(Post.id).filter(Post.slug == s)
        if exclude_id:
            q = q.filter(Post.id != exclude_id)
        return db.query(q.exists()).scalar()

    return unique_slug(base, exists)


def _set_published_at(post: Post, status: int) -> None:
    if status == PostStatus.PUBLISHED and post.published_at is None:
        post.published_at = datetime.now()
    if status == PostStatus.DRAFT:
        post.published_at = None


def create_post(db: Session, payload: PostIn, author_id: Optional[int] = None) -> Post:
    if payload.category_id is not None:
        cat = db.query(Category).filter(Category.id == payload.category_id).first()
        if not cat:
            raise NotFoundException("分类不存在")

    slug = _ensure_unique_slug(db, payload.slug, payload.title)
    post = Post(
        title=payload.title.strip(),
        slug=slug,
        summary=(payload.summary or "").strip() or make_summary(payload.content),
        content=payload.content or "",
        cover=payload.cover,
        status=payload.status,
        is_top=payload.is_top,
        category_id=payload.category_id,
        author_id=author_id,
        word_count=count_words(payload.content or ""),
    )
    _set_published_at(post, payload.status)

    db.add(post)
    db.commit()
    db.refresh(post)
    invalidate_post(slug=post.slug, post_id=post.id)
    return post


def update_post(db: Session, post_id: int, payload: PostIn) -> Post:
    post = get_post_by_id(db, post_id)
    if post is None:
        raise NotFoundException("文章不存在")

    old_slug = post.slug
    if payload.category_id is not None:
        cat = db.query(Category).filter(Category.id == payload.category_id).first()
        if not cat:
            raise NotFoundException("分类不存在")

    old_image_urls = image_service.extract_post_image_urls(post)

    post.title = payload.title.strip()
    if payload.slug and payload.slug != old_slug:
        post.slug = _ensure_unique_slug(db, payload.slug, payload.title, exclude_id=post_id)
    elif not payload.slug:
        post.slug = _ensure_unique_slug(db, None, payload.title, exclude_id=post_id)

    post.summary = (payload.summary or "").strip() or make_summary(payload.content)
    post.content = payload.content or ""
    post.cover = payload.cover
    post.is_top = payload.is_top
    post.category_id = payload.category_id
    post.word_count = count_words(post.content)
    # 注意：这里与 _set_published_at 逻辑有意不同——仅当「草稿 → 发布」时才补发布时间，
    # 已发布文章再次保存不会重置/补写 published_at（保持历史行为，勿合并）
    was_published = post.status == PostStatus.PUBLISHED
    post.status = payload.status
    if not was_published and payload.status == PostStatus.PUBLISHED and post.published_at is None:
        post.published_at = datetime.now()
    if payload.status == PostStatus.DRAFT:
        post.published_at = None

    db.commit()
    db.refresh(post)

    # 同步清理：编辑后不再被引用（且无其他文章引用）的文章图片随文删除
    try:
        image_service.sync_post_images(db, post, old_image_urls)
    except Exception as exc:  # noqa: BLE001
        logger.warning("sync post images after update failed: %s", exc)

    invalidate_post(slug=old_slug)
    invalidate_post(slug=post.slug, post_id=post.id)
    return post


def delete_post(db: Session, post_id: int) -> None:
    post = get_post_by_id(db, post_id)
    if post is None:
        raise NotFoundException("文章不存在")
    slug = post.slug
    # 删除前先提取本文引用的文章图片，删文后同步清理其独占的图片文件
    image_urls = image_service.extract_post_image_urls(post)
    db.delete(post)
    db.commit()
    try:
        image_service.remove_post_images(db, image_urls, post_id=post_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("remove post images after delete failed: %s", exc)
    invalidate_post(slug=slug, post_id=post_id)


# ---------------- 归档 ----------------
def list_archive(db: Session) -> List[Dict[str, Any]]:
    """按 年-月 分组（仅已发布）"""
    stmt = (
        _base_query(db)
        .where(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc(), Post.id.desc())
    )
    posts = db.execute(stmt).scalars().unique().all()

    buckets: Dict[str, Dict[str, Any]] = {}
    for p in posts:
        dt = p.published_at or p.created_at
        key = f"{dt.year}-{dt.month:02d}"
        bucket = buckets.setdefault(
            key, {"year": dt.year, "month": dt.month, "count": 0, "posts": []}
        )
        item = serialize_post(p, with_content=False)
        item["views"] = current_views(item["id"], item["views"])
        bucket["posts"].append(item)
        bucket["count"] += 1

    return sorted(buckets.values(), key=lambda b: (b["year"], b["month"]), reverse=True)


def get_neighbors(db: Session, post_id: int) -> Dict[str, Any]:
    """上一篇 / 下一篇"""
    prev_row = (
        db.query(Post.id, Post.title, Post.slug)
        .filter(Post.status == PostStatus.PUBLISHED, Post.id < post_id)
        .order_by(Post.id.desc())
        .first()
    )
    next_row = (
        db.query(Post.id, Post.title, Post.slug)
        .filter(Post.status == PostStatus.PUBLISHED, Post.id > post_id)
        .order_by(Post.id.asc())
        .first()
    )
    return {
        "prev": {"id": prev_row[0], "title": prev_row[1], "slug": prev_row[2]} if prev_row else None,
        "next": {"id": next_row[0], "title": next_row[1], "slug": next_row[2]} if next_row else None,
    }
