"""认证业务层：登录 / 登出 / token 黑名单"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthException
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.services.cache import K_TOKEN_BLACKLIST, cache, make_key


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthException("用户名或密码错误")
    if not user.is_active:
        raise AuthException("账号已被禁用")
    return user


def login(db: Session, username: str, password: str) -> dict:
    user = authenticate(db, username, password)

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


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.hashed_password):
        raise AuthException("原密码不正确")
    user.hashed_password = get_password_hash(new_password)
    db.commit()


def update_user(db: Session, user: User, data: dict) -> User:
    for k, v in data.items():
        if v is not None and hasattr(user, k):
            setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user
