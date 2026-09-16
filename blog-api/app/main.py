"""FastAPI 应用入口"""
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app import __version__
from app.api.seo import router as seo_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import SessionLocal, check_db
from app.models.post import Post, PostStatus
from app.services import seo_service
from app.services.cache import cache, flush_view_deltas

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("bluemoon")

# SPA 路径中文章详情的匹配（用于注入文章级 SEO）
_POST_PATH_RE = re.compile(r"^post/([^/]+)/?$")

# 可长期缓存（immutable）的静态路径特征：文件名含时间戳 / 日期目录 / 长期资产目录 / 衍生档
_IMMUTABLE_PATH_RES = (
    re.compile(r"^\d{8}\d{6}_"),          # 时间戳前缀文件名，如 20260913102530_ab12cd34.jpg
    re.compile(r"(?:^|/)gallery/"),        # 图库长期资产
    re.compile(r"(?:^|/)avatar/"),         # 头像（换头像换文件名，URL 天然失效）
    re.compile(r"(?:^|/)uploads/"),        # 随文资源（日期目录 / 旧作用域）
    re.compile(r"@(?:1024|400)\.webp$"),   # WebP 衍生档
)


def _is_immutable_static(path: str) -> bool:
    name = str(path).replace("\\", "/").rsplit("/", 1)[-1]
    norm = str(path).replace("\\", "/")
    return any(r.search(name) or r.search(norm) for r in _IMMUTABLE_PATH_RES)


# index.html 文本缓存：内容仅在 mtime 变化（重新构建）时失效，
# 避免每次 SPA 回退都读盘 + 解码一次
_index_cache: dict[str, tuple[float, str]] = {}


def _read_index_cached(index_file: Path) -> str | None:
    try:
        mtime = index_file.stat().st_mtime
    except OSError:
        return None
    key = str(index_file)
    hit = _index_cache.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    text = seo_service.read_index(index_file)
    if text is not None:
        _index_cache[key] = (mtime, text)
    return text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动 / 关闭钩子"""
    logger.info("=" * 60)
    logger.info("%s v%s starting...", settings.APP_NAME, __version__)
    # 静态资源根目录（日期优先布局：日期目录与 uploads/ 子目录按需自动创建）
    settings.static_path.mkdir(parents=True, exist_ok=True)

    db_ok, detail = check_db()
    logger.info("MySQL  %s  %s", "OK " if db_ok else "FAIL", "" if db_ok else detail)
    ok, detail = cache.ping()
    logger.info("Redis  %s  %s", "OK " if ok else "DOWN(degraded)", detail if not ok else "")
    logger.info("Docs   http://127.0.0.1:%s/docs", settings.PORT)
    logger.info("=" * 60)

    yield

    # 关闭前把 Redis 里累积的阅读量回写 MySQL
    if cache.available:
        db = SessionLocal()
        try:
            n = flush_view_deltas(db)
            if n:
                logger.info("flushed view deltas for %s posts before shutdown", n)
        except Exception as exc:  # noqa: BLE001
            logger.warning("flush view deltas on shutdown failed: %s", exc)
        finally:
            db.close()
    logger.info("bye.")


class CachedStaticFiles(StaticFiles):
    """静态资源缓存策略。

    日期目录 / gallery / avatar 的文件名均含时间戳，内容不可变，可安全长期缓存。
    注意：头像依赖「换文件名」的既有约定来保证 URL 变化（缓存天然失效），
    切勿改为固定文件名 —— 否则 `immutable` 会让用户看不到新头像。

    其余路径（未来放入 static 的可变更文件，如 favicon、robots 等）
    只给 1 小时缓存，避免改不动。
    """

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        path = str(args[0]) if args else ""
        if _is_immutable_static(path):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            resp.headers["Cache-Control"] = "public, max-age=3600"
        return resp


def create_app() -> FastAPI:
    # 生产环境关闭交互式文档：/docs、/redoc、/openapi.json 无需鉴权，
    # 会把完整的接口与数据模型暴露出去
    is_prod = settings.APP_ENV == "production"
    app = FastAPI(
        title=settings.APP_NAME,
        description="个人博客后端 API（FastAPI + MySQL + Redis）",
        version=__version__,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 传输压缩：JSON / JS / CSS / HTML 统一 gzip（<1KB 的响应不压缩）
    # 注意：Starlette 的 GZipMiddleware 不按 content-type 过滤，图片也会走压缩判定；
    # 图片侧靠 CachedStaticFiles 的 immutable 长期缓存把重复请求降为 0 来抵消开销。
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    register_exception_handlers(app)
    app.include_router(api_router)

    # SEO 根级路由（/sitemap.xml、/robots.txt）：搜索引擎只认站点根路径，
    # 且必须注册在 SPA fallback 之前，否则会被 catch-all 吃掉
    app.include_router(seo_router)

    # 静态资源（上传的图片）——挂载前目录必须存在
    # 日期优先布局：日期目录与 uploads/ 子目录在上传时按需自动创建
    settings.static_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/static",
        CachedStaticFiles(directory=str(settings.static_path)),
        name="static",
    )

    # SPA fallback（history 模式）：必须注册在所有 API 路由与挂载之后，
    # 只接管未被匹配的 GET 请求；非 GET（API 405）不受影响
    register_spa_fallback(app)

    return app


def _render_index_html(index_file, full_path: str) -> str | None:
    """读取 index.html 并注入 SEO 元信息；不满足注入条件时返回 None（调用方降级为 FileResponse）

    - 文章页（/post/{slug}）注入该文章的 title / description / og:image
    - 其他页面注入站点级默认值

    微信、QQ 抓取分享预览时不执行 JS，只有服务端注入才能出卡片。
    """
    html_text = _read_index_cached(index_file)
    if html_text is None or not seo_service.has_marker(html_text):
        return None

    meta = seo_service.site_meta(full_path)
    m = _POST_PATH_RE.match(full_path or "")
    if m:
        db = SessionLocal()
        try:
            post = db.execute(
                select(Post).where(
                    Post.slug == m.group(1),
                    Post.status == PostStatus.PUBLISHED,
                )
            ).scalar_one_or_none()
            if post is not None:
                # 在 session 关闭前取属性，避免 detached 后访问报错
                meta = seo_service.post_meta(post)
        except Exception as exc:  # noqa: BLE001
            # 注入失败绝不能影响页面可用性，降级为站点级元信息
            logger.warning("seo inject failed for %s: %s", full_path, exc)
        finally:
            db.close()

    return seo_service.inject(html_text, meta)


def register_spa_fallback(app: FastAPI) -> None:
    """前端 history 路由回退：未匹配的 GET 请求返回 dist 内静态文件或 index.html"""
    dist = settings.frontend_dist_path
    index_file = dist / "index.html"

    # 用同步 def 而非 async def：注入 SEO 需要一次同步 DB 查询，
    # FastAPI 会把同步路由放进线程池执行，不会阻塞事件循环。
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if not index_file.is_file():
            # 未构建前端时保持明确的 404，而不是让 API 调用方收到 HTML
            raise HTTPException(status_code=404, detail="Frontend build not found")

        if full_path:
            candidate = (dist / full_path).resolve()
            # 防目录穿越：解析后必须仍位于 dist 目录内
            # （字符串前缀比较会被 dist-backup/ 这类同前缀目录骗过）
            if candidate.is_file() and candidate.is_relative_to(dist):
                # Vite 产物文件名含 hash → 内容不可变，可长期缓存
                return FileResponse(
                    candidate,
                    headers={"Cache-Control": "public, max-age=31536000, immutable"},
                )

        # index.html 必须每次校验，避免发版后用户长时间停留在旧版本
        no_cache = {"Cache-Control": "no-cache"}

        html_text = _render_index_html(index_file, full_path)
        if html_text is None:
            return FileResponse(index_file, headers=no_cache)
        return HTMLResponse(html_text, headers=no_cache)


app = create_app()
