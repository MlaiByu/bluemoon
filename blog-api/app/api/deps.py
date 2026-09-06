"""FastAPI 公共依赖"""
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthException, ForbiddenException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def client_ip(request: Request) -> str:
    """提取客户端真实 IP：优先取反向代理的 X-Forwarded-For 首段。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _load_user(db: Session, token: str) -> User:
    payload = decode_access_token(token)
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        raise AuthException("登录已失效，请重新登录")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise AuthException("用户不存在")
    if not user.is_active:
        raise AuthException("账号已被禁用")
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if not token:
        raise AuthException("请先登录")
    return _load_user(db, token)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise ForbiddenException("需要管理员权限")
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    """无 token 返回 None（前台草稿预览用）"""
    if not token:
        return None
    try:
        return _load_user(db, token)
    except AuthException:
        return None


__all__ = [
    "get_db",
    "get_current_user",
    "get_current_admin",
    "get_optional_user",
    "client_ip",
    "oauth2_scheme",
]
