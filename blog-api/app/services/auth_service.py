"""认证业务层：登录 / 登出 / token 黑名单 / 登录防爆破"""
from __future__ import annotations

import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthException, TooManyRequestsException
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.services.cache import (
    K_LOGIN_FAIL,
    K_TOKEN_BLACKLIST,
    K_TOKEN_INVALID_BEFORE,
    cache,
    make_key,
)


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    # 统一报错文案，不区分「用户不存在 / 密码错」，避免账号枚举
    if not user or not verify_password(password, user.hashed_password):
        raise AuthException("用户名或密码错误")
    if not user.is_active:
        raise AuthException("账号已被禁用")
    return user


# ---------------- 登录防爆破 ----------------
def _fail_key(username: str, ip: str) -> str:
    return make_key(K_LOGIN_FAIL, username=(username or "").lower()[:50], ip=ip)


def login_failures(username: str, ip: str) -> int:
    try:
        return int(cache.get(_fail_key(username, ip)) or 0)
    except (TypeError, ValueError):
        return 0


def _bump_failures(username: str, ip: str) -> int:
    key = _fail_key(username, ip)
    n = cache.incr(key)
    if n is None:
        # Redis 不可用：降级为不限制（宁可放开也不能把自己锁在门外）
        return 0
    if n == 1:
        cache.expire(key, settings.LOGIN_FAIL_WINDOW_SECONDS)
    elif n >= settings.LOGIN_MAX_FAILURES:
        # 达阈值后把 TTL 补足为完整锁定时长
        cache.expire(key, settings.LOGIN_LOCK_SECONDS)
    return n


def clear_login_failures(username: str, ip: str) -> None:
    cache.delete(_fail_key(username, ip))


def login(db: Session, username: str, password: str, ip: str = "unknown") -> dict:
    if login_failures(username, ip) >= settings.LOGIN_MAX_FAILURES:
        raise TooManyRequestsException("登录失败次数过多，请稍后再试")

    try:
        user = authenticate(db, username, password)
    except AuthException:
        _bump_failures(username, ip)
        raise

    clear_login_failures(username, ip)
    user.last_login_at = datetime.now()
    db.commit()

    token, jti, expires_in = create_access_token(
        subject=user.id, extra={"username": user.username}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user,
    }


def logout(token: str) -> None:
    """把 jti 加入黑名单，剩余有效期内不再可用"""
    payload = decode_access_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return
    ttl = int(exp - datetime.now().timestamp())
    if ttl > 0:
        cache.set(make_key(K_TOKEN_BLACKLIST, jti=jti), "1", ttl=ttl)


def is_token_blacklisted(jti: str) -> bool:
    return cache.exists(make_key(K_TOKEN_BLACKLIST, jti=jti))


def invalidate_user_tokens(user_id: int) -> None:
    """吊销该用户此前签发的全部 token（改密 / 踢下线）。

    只记一个「失效时间戳」，比逐个 jti 拉黑更省空间；
    TTL 覆盖 token 最长有效期，过期后自动清理。
    """
    ttl = max(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 3600)
    cache.set(
        make_key(K_TOKEN_INVALID_BEFORE, user_id=user_id), str(int(time.time())), ttl=ttl
    )


def is_token_stale(user_id: int, iat) -> bool:
    """token 是否早于「吊销时间戳」（Redis 不可用时视为不失效）"""
    raw = cache.get(make_key(K_TOKEN_INVALID_BEFORE, user_id=user_id))
    if not raw:
        return False
    try:
        invalid_before = int(raw)
        issued = int(float(iat or 0))
    except (TypeError, ValueError):
        return False
    return issued < invalid_before


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.hashed_password):
        raise AuthException("原密码不正确")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    # 改密后旧 token 立即失效（接口文案承诺「请重新登录」，行为必须一致）
    invalidate_user_tokens(user.id)


def update_user(db: Session, user: User, data: dict) -> User:
    for k, v in data.items():
        if v is not None and hasattr(user, k):
            setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user
