"""健康检查"""
from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.core.response import success
from app.db.session import check_db
from app.services.cache import cache

router = APIRouter(tags=["系统"])


@router.get("/health", summary="健康检查")
def health():
    db_ok, db_detail = check_db()
    redis_ok, redis_detail = cache.ping()
    return success(
        {
            "status": "ok" if db_ok else "degraded",
            "app": settings.APP_NAME,
            "version": __version__,
            "env": settings.APP_ENV,
            "mysql": {"status": "up" if db_ok else "down", "detail": db_detail},
            "redis": {
                "status": "up" if redis_ok else "down",
                "detail": redis_detail,
                "enabled": settings.REDIS_ENABLED,
            },
        }
    )


@router.get("/cache/info", summary="Redis 缓存状态")
def cache_info():
    return success({"enabled": settings.REDIS_ENABLED, **cache.info()})
