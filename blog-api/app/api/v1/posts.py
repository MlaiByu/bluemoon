"""文章接口"""
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_admin, get_db, get_optional_user
from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.core.response import success
from app.models.post import Post, PostStatus
from app.models.user import User
from app.schemas.post import PostIn
from app.services import post_service, stats_service
from app.services.cache import flush_view_deltas

router = APIRouter(prefix="/posts", tags=["文章"])


@router.get("", summary="文章列表（分页）")
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, description="标题/摘要/正文 模糊搜索"),
    category_id: int | None = Query(None),
    order_by: str = Query("default", pattern="^(default|views|latest)$"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """前台只返回已发布；后台（带 token）可传 status 查看全部"""
    status = PostStatus.PUBLISHED if current_user is None else None
    return post_service.list_posts(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        category_id=category_id,
        status=status,
        order_by=order_by,
    )


@router.get("/admin", summary="后台文章列表（含草稿）")
def list_posts_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None),
    category_id: int | None = Query(None),
    status: int | None = Query(None, ge=0, le=1),
    order_by: str = Query("default", pattern="^(default|views|latest)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return post_service.list_posts(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        category_id=category_id,
        status=status,
        order_by=order_by,
    )


@router.get("/archives", summary="归档（按年月分组）")
def archives(db: Session = Depends(get_db)):
    return success(post_service.list_archive(db))


def _xml_escape(s: str | None) -> str:
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


@router.get("/rss", summary="RSS 2.0 订阅源")
def rss_feed(request: Request, db: Session = Depends(get_db)):
    """生成 RSS 2.0 XML（仅已发布文章，按发布时间倒序取前 20 篇）"""
    site_url = settings.FRONTEND_URL.rstrip("/")
    stmt = (
        select(Post)
        .where(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc(), Post.id.desc())
        .limit(20)
    )
    items = db.execute(stmt).scalars().all()

    def item_xml(p: Post) -> str:
        link = f"{site_url}/#/post/{p.slug}"
        pub = (p.published_at or p.created_at)
        pub_str = pub.strftime("%a, %d %b %Y %H:%M:%S +0800") if pub else ""
        desc = _xml_escape(p.summary or "")
        return (
            f"    <item>\n"
            f"      <title>{_xml_escape(p.title)}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid isPermaLink=\"false\">{p.id}</guid>\n"
            f"      <pubDate>{pub_str}</pubDate>\n"
            f"      <description>{desc}</description>\n"
            f"    </item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{_xml_escape(settings.BLOG_TITLE or 'Bluemoon')}</title>\n"
        f"    <link>{site_url}/</link>\n"
        f"    <description>{_xml_escape(settings.BLOG_DESCRIPTION or '')}</description>\n"
        f"    <language>zh-CN</language>\n"
        f"    <lastBuildDate>{(items[0].published_at or items[0].created_at).strftime('%a, %d %b %Y %H:%M:%S +0800') if items else ''}</lastBuildDate>\n"
        + "\n".join(item_xml(p) for p in items)
        + "\n  </channel>\n</rss>\n"
    )
    return Response(content=xml, media_type="application/rss+xml")


@router.get("/detail/{slug}", summary="文章详情（按 slug）")
def detail(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    allow_draft = current_user is not None and current_user.is_superuser
    data = post_service.get_post_detail_cached(db, slug, allow_draft=allow_draft)
    if data is None:
        raise NotFoundException("文章不存在或未发布")
    data["views"] = post_service.current_views(data["id"], data.get("views", 0))
    data["neighbors"] = post_service.get_neighbors(db, data["id"])
    return success(data)


@router.post("/{post_id}/view", summary="上报有效阅读")
def record_view(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    ip: str = Depends(client_ip),
):
    """
    前端在用户阅读满 10 秒后调用此接口上报阅读量。
    后端通过 IP + 文章 ID 做 5 分钟防刷，避免重复计数。
    """
    counted = post_service.record_view(db, post_id, ip)
    return success({"counted": counted})


@router.get("/{post_id}", summary="文章详情（按 ID，后台用）")
def detail_by_id(
    post_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    post = post_service.get_post_by_id(db, post_id)
    if post is None:
        raise NotFoundException("文章不存在")
    data = post_service.serialize_post(post, with_content=True)
    data["views"] = post_service.current_views(post.id, post.views)
    return success(data)


@router.post("", summary="新建文章")
def create(
    payload: PostIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    post = post_service.create_post(db, payload, author_id=current_user.id)
    return success(
        post_service.serialize_post(post, with_content=True), msg="文章已创建"
    )


@router.put("/{post_id}", summary="更新文章")
def update(
    post_id: int,
    payload: PostIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    post = post_service.update_post(db, post_id, payload)
    return success(post_service.serialize_post(post, with_content=True), msg="文章已更新")


@router.delete("/{post_id}", summary="删除文章")
def delete(
    post_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    post_service.delete_post(db, post_id)
    return success(msg="文章已删除")


@router.post("/flush-views", summary="手动回写阅读量到 MySQL")
def flush_views(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    n = flush_view_deltas(db)
    return success({"flushed": n}, msg=f"已回写 {n} 篇文章的阅读量")
