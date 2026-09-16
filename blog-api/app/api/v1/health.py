"""健康检查"""
from fastapi import APIRouter, Depends

from app import __version__
from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.response import success
from app.db.session import check_db
from app.models.user import User
from app.services.cache import cache

router = APIRouter(tags=["系统"])


@router.get("/health", summary="健康检查")
def health():
    """探活接口：只回状态，不暴露内部细节。

    连接串 / 异常原文（可能含主机名、账号）只在 DEBUG 下返回 ——
    该接口无需鉴权，生产环境把异常原文吐出去等于免费送攻击面信息。
    """
    db_ok, db_detail = check_db()
    redis_ok, redis_detail = cache.ping()
    data = {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": __version__,
        "mysql": "up" if db_ok else "down",
        "redis": "up" if redis_ok else "down",
    }
    if settings.DEBUG:
        data["env"] = settings.APP_ENV
        data["detail"] = {"mysql": db_detail, "redis": redis_detail}
    return success(data)


@router.get("/cache/info", summary="Redis 缓存状态（管理员）")
def cache_info(_: User = Depends(get_current_admin)):
    return success({"enabled": settings.REDIS_ENABLED, **cache.info()})
