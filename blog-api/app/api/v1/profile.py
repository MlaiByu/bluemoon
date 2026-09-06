"""关于我 / 站点资料"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.response import success
from app.models.user import User
from app.schemas.profile import ProfileIn, ProfileOut
from app.services import stats_service
from app.services.cache import cache, make_key

router = APIRouter(prefix="/profile", tags=["关于我"])


@router.get("", summary="获取关于我")
def get_profile(db: Session = Depends(get_db)):
    profile = stats_service.get_profile(db)
    data = ProfileOut.model_validate(profile).model_dump(mode="json")
    # 注入管理员头像（前台展示用，不从 profile 表读取）
    admin = db.query(User).filter(User.is_superuser == True, User.is_active == True).first()
    if admin:
        data["avatar"] = admin.avatar
    return success(data)


@router.put("", summary="更新关于我")
def update_profile(
    payload: ProfileIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    data = payload.model_dump(exclude_unset=True)
    profile = stats_service.update_profile(db, data)
    resp = ProfileOut.model_validate(profile).model_dump(mode="json")
    # 注入管理员头像
    admin = db.query(User).filter(User.is_superuser == True, User.is_active == True).first()
    if admin:
        resp["avatar"] = admin.avatar
    return success(resp, msg="已保存")
