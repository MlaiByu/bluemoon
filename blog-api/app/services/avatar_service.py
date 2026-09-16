"""头像历史业务层：归档 / 查询 / 恢复 / 清理

存储约定：
- 头像文件统一存放在站点级目录 static/avatar/，与图库（static/gallery/）、
  文章图片（日期目录）物理隔离，便于单独备份、迁移与清理；
- 更换头像不删除旧文件，而是归档为历史头像（user_avatars 表记录）；
- 清理策略（app.core.config）：
  - AVATAR_HISTORY_LIMIT：每个用户保留的历史数量上限（当前头像不清理）；
  - AVATAR_HISTORY_TTL_DAYS：历史保留天数，0 表示不按时间清理，仅受数量上限约束。
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException, NotFoundException
from app.models.user import User
from app.models.user_avatar import UserAvatar
from app.services import image_service

logger = logging.getLogger("bluemoon")


def _delete_avatar_file(url: str) -> bool:
    """删除头像文件（路径非法或文件缺失时静默跳过）。"""
    try:
        target = image_service.resolve_image_path(url)
    except BizException:
        return False
    if not target.is_file():
        return False
    try:
        target.unlink()
    except OSError:
        return False
    # 目录可能整体变空，清理到 static 根为止（只删空目录）
    image_service.cleanup_empty_dirs(target, settings.static_path)
    return True


def serialize_avatar(item: UserAvatar, current_url: str | None = None) -> Dict[str, Any]:
    """序列化一条历史头像记录。"""
    is_current = bool(item.is_current) or (current_url is not None and item.url == current_url)
    return {
        "id": item.id,
        "url": item.url,
        "filename": item.filename,
        "size": item.size,
        "is_current": is_current,
        "uploaded_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None,
    }


def list_avatars(db: Session, user: User) -> List[Dict[str, Any]]:
    """查询用户的历史头像列表，按上传时间倒序。"""
    stmt = (
        select(UserAvatar)
        .where(UserAvatar.user_id == user.id)
        .order_by(UserAvatar.created_at.desc(), UserAvatar.id.desc())
    )
    items = db.execute(stmt).scalars().all()
    return [serialize_avatar(i, user.avatar) for i in items]


def add_avatar(
    db: Session,
    user: User,
    url: str,
    filename: str,
    size: int,
) -> Dict[str, Any]:
    """新增头像并设为当前使用：旧头像归档保留（不删除文件），随后执行清理策略。"""
    # 1. 旧记录全部标记为非当前
    db.query(UserAvatar).filter(
        UserAvatar.user_id == user.id, UserAvatar.is_current.is_(True)
    ).update({UserAvatar.is_current: False})

    # 2. 写入新记录并设为当前
    item = UserAvatar(
        user_id=user.id,
        url=url,
        filename=filename,
        size=size,
        is_current=True,
    )
    db.add(item)
    user.avatar = url
    db.commit()
    db.refresh(item)

    # 3. 按数量 / 时间策略清理多余历史
    prune_avatars(db, user)

    return serialize_avatar(item, user.avatar)


def restore_avatar(db: Session, user: User, avatar_id: int) -> Dict[str, Any]:
    """从历史头像中恢复一张为当前头像。"""
    item = db.get(UserAvatar, avatar_id)
    if item is None or item.user_id != user.id:
        raise NotFoundException("头像记录不存在")

    db.query(UserAvatar).filter(
        UserAvatar.user_id == user.id, UserAvatar.is_current.is_(True)
    ).update({UserAvatar.is_current: False})

    item.is_current = True
    user.avatar = item.url
    db.commit()
    db.refresh(item)
    return serialize_avatar(item, user.avatar)


def delete_avatar(db: Session, user: User, avatar_id: int) -> None:
    """删除一条历史头像（当前使用的头像不可删除，请先切换到其他头像）。"""
    item = db.get(UserAvatar, avatar_id)
    if item is None or item.user_id != user.id:
        raise NotFoundException("头像记录不存在")
    if item.is_current or item.url == user.avatar:
        raise BizException("当前使用的头像不能删除，请先更换或恢复其他头像")

    url = item.url
    db.execute(delete(UserAvatar).where(UserAvatar.id == item.id))
    db.commit()
    _delete_avatar_file(url)


def prune_avatars(db: Session, user: User) -> int:
    """按数量上限与过期天数清理历史头像，返回清理条数。

    当前使用的头像（is_current=True）永远保留；
    AVATAR_HISTORY_TTL_DAYS > 0 时额外清理超过保留天数的历史。
    """
    removed = 0

    # 1. 按时间过期清理
    ttl_days = getattr(settings, "AVATAR_HISTORY_TTL_DAYS", 0) or 0
    if ttl_days > 0:
        deadline = datetime.now() - timedelta(days=ttl_days)
        expired = (
            db.query(UserAvatar)
            .filter(
                UserAvatar.user_id == user.id,
                UserAvatar.is_current.is_(False),
                UserAvatar.created_at < deadline,
            )
            .all()
        )
        for item in expired:
            url = item.url
            db.delete(item)
            db.flush()
            _delete_avatar_file(url)
            removed += 1

    # 2. 按数量上限清理（保留最新的 N 条，当前头像不计入被清理范围）
    limit = getattr(settings, "AVATAR_HISTORY_LIMIT", 0) or 0
    if limit > 0:
        total = (
            db.query(UserAvatar.id).filter(UserAvatar.user_id == user.id).count()
        )
        if total > limit:
            overflow = (
                db.query(UserAvatar)
                .filter(UserAvatar.user_id == user.id, UserAvatar.is_current.is_(False))
                .order_by(UserAvatar.created_at.asc(), UserAvatar.id.asc())
                .limit(total - limit)
                .all()
            )
            for item in overflow:
                url = item.url
                db.delete(item)
                db.flush()
                _delete_avatar_file(url)
                removed += 1

    if removed:
        db.commit()
        logger.info("pruned %s historical avatars for user %s", removed, user.id)
    return removed
