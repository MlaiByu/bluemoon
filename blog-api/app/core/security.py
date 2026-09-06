"""密码哈希 + JWT 签发/校验"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------- 密码 ----------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---------------- JWT ----------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: Any,
    expires_delta: Optional[timedelta] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> tuple[str, str, int]:
    """返回 (token, jti, expires_in_seconds)"""
    expire = _now() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    jti = uuid.uuid4().hex
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": _now(),
        "jti": jti,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    expires_in = int((expire - _now()).total_seconds())
    return token, jti, expires_in


def decode_access_token(token: str) -> Dict[str, Any]:
    """校验并解析 token，失败抛 AuthException"""
    from app.core.exceptions import AuthException

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise AuthException("登录凭证无效或已过期")
    if payload.get("type") != "access":
        raise AuthException("登录凭证类型错误")
    if not payload.get("sub"):
        raise AuthException("登录凭证无效")
    return payload
