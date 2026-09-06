"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import SessionLocal, check_db
from app.services.cache import cache, flush_view_deltas

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("bluemoon")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动 / 关闭钩子"""
    logger.info("=" * 60)
    logger.info("%s v%s starting...", settings.APP_NAME, __version__)
    settings.upload_path.mkdir(parents=True, exist_ok=True)
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


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="个人博客后端 API（FastAPI + MySQL + Redis）",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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

    register_exception_handlers(app)
    app.include_router(api_router)

    # 静态资源（上传的图片）——挂载前目录必须存在
    settings.static_path.mkdir(parents=True, exist_ok=True)
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(settings.static_path)), name="static")

    # SPA fallback（history 模式）：必须注册在所有 API 路由与挂载之后，
    # 只接管未被匹配的 GET 请求；非 GET（API 405）不受影响
    register_spa_fallback(app)

    return app


def register_spa_fallback(app: FastAPI) -> None:
    """前端 history 路由回退：未匹配的 GET 请求返回 dist 内静态文件或 index.html"""
    dist = settings.frontend_dist_path
    index_file = dist / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if not index_file.is_file():
            # 未构建前端时保持明确的 404，而不是让 API 调用方收到 HTML
            raise HTTPException(status_code=404, detail="Frontend build not found")
        if full_path:
            candidate = (dist / full_path).resolve()
            # 防目录穿越：解析后必须仍位于 dist 目录内
            if candidate.is_file() and str(candidate).startswith(str(dist)):
                return FileResponse(candidate)
        return FileResponse(index_file)


app = create_app()
