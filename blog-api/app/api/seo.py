"""SEO 路由：sitemap.xml / robots.txt

为什么单独成一个 router：
这两个文件必须挂在**应用根路径**（`/sitemap.xml`、`/robots.txt`）——搜索引擎只认
站点根下的这两个文件名，放在 `/api/v1` 前缀下不会被识别。因此不能并入 api_router。

注册顺序要求：必须在 `register_spa_fallback()`（catch-all `/{full_path:path}`）之前，
否则会被 SPA 回退吃掉并返回 index.html。
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.post import Post, PostStatus
from app.services import seo_service

router = APIRouter(tags=["SEO"])


@router.get("/sitemap.xml", summary="站点地图", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)):
    """列出所有已发布文章 + 固定页面，供搜索引擎抓取"""
    rows = db.execute(
        select(Post.slug, Post.updated_at)
        .where(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc(), Post.id.desc())
    ).all()
    return Response(
        content=seo_service.sitemap_xml([(r[0], r[1]) for r in rows]),
        media_type="application/xml",
    )


@router.get("/robots.txt", summary="爬虫规则", include_in_schema=False)
def robots():
    """放行全站，屏蔽后台与 API，声明 sitemap 位置"""
    return Response(content=seo_service.robots_txt(), media_type="text/plain")
