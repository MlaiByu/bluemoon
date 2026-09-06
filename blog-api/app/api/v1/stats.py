"""站点信息与统计"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.core.response import success
from app.models.user import User
from app.services import stats_service
from app.services.cache import cache

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/site", summary="站点信息（前台）")
def site(db: Session = Depends(get_db)):
    return success(stats_service.site_info(db))


@router.get("/overview", summary="后台仪表盘数据")
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return success(stats_service.overview(db))


@router.post("/cache/flush", summary="清空 Redis 缓存（后台）")
def flush_cache(_: User = Depends(get_current_admin)):
    if not cache.available:
        return success({"flushed": 0}, msg="Redis 未启用，无需清理")
    n = cache.flush_all()
    return success({"flushed": n}, msg=f"已清空 {n} 个缓存键")
