"""Redis 缓存封装

设计要点：
1. 所有 key 统一前缀 `bm:`，便于管理与批量清理
2. Redis 不可用时**静默降级**——缓存失败不能影响主流程
3. 提供 get_json / set_json / delete / delete_prefix / incr / getset 等常用操作
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable, Iterable, List, Optional

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger("bluemoon")

PREFIX = "bm:"

# ---- key 命名空间 ----
# 详情缓存必须带 scope（pub / draft）：草稿只有管理员可见，
# 若与公开详情共用同一个 key，管理员预览一次草稿就会把未发布内容
# 写进公共缓存，匿名访客在 TTL 内可直接读到。
K_POST_DETAIL = "post:detail:{scope}:{slug}"
K_POST_DETAIL_ID = "post:detail:id:{id}"
# 列表缓存带「版本号」，站点级失效只需 INCR 版本号，
# 不必 SCAN 遍历删除全部列表 key（后者在 key 量大时是 O(N) 阻塞操作）。
K_POST_LIST = "post:list:v{ver}:{hash}"
K_POST_LIST_VER = "post:list:ver"
# 兼容旧名（历史 key 仍在 Redis 中，靠 TTL 自然过期）
K_POST_LIST_PREFIX = "post:list:"
K_POST_VIEWS = "post:views:{id}"
K_POST_VIEW_LOCK = "post:view:lock:{post_id}:{ip}"
K_STATS = "stats:{kind}"
K_SITE = "site:info"
K_CATEGORIES = "tax:categories"
K_TOKEN_BLACKLIST = "token:blacklist:{jti}"
# 改密时间戳：早于该时间签发的 token 一律失效（免去逐条拉黑 jti）
K_TOKEN_INVALID_BEFORE = "token:invalid-before:{user_id}"
# 登录失败计数（按 用户名+IP）
K_LOGIN_FAIL = "auth:fail:{username}:{ip}"
K_PROFILE = "site:profile"
K_IMAGE_LIST = "upload:images:{scope}"


def make_key(pattern: str, **kwargs: Any) -> str:
    return PREFIX + pattern.format(**kwargs)


def hash_key(params: dict) -> str:
    """把查询参数序列化成稳定的短哈希，用于列表缓存 key"""
    raw = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


class Cache:
    """Redis 客户端包装，带降级"""

    def __init__(self) -> None:
        self._client: Optional[Redis] = None
        self._available: bool = False
        self._init_client()

    # ---------- 生命周期 ----------
    def _init_client(self) -> None:
        if not settings.REDIS_ENABLED:
            logger.info("Redis disabled by config, cache degraded to no-op")
            return
        try:
            self._client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
            )
            self._client.ping()
            self._available = True
            logger.info(
                "Redis connected: %s:%s db=%s",
                settings.REDIS_HOST,
                settings.REDIS_PORT,
                settings.REDIS_DB,
            )
        except Exception as exc:  # noqa: BLE001
            self._available = False
            logger.warning("Redis unavailable (%s), cache degraded to no-op", exc)

    @property
    def available(self) -> bool:
        return self._available

    @property
    def client(self) -> Optional[Redis]:
        return self._client if self._available else None

    def _safe(self, fn: Callable[[], Any], default: Any = None) -> Any:
        if not self._available or self._client is None:
            return default
        try:
            return fn()
        except RedisError as exc:
            logger.warning("Redis error: %s (degraded)", exc)
            return default

    # ---------- 基础操作 ----------
    def ping(self) -> tuple[bool, str]:
        if not self._available:
            return False, "disabled"
        try:
            self._client.ping()  # type: ignore[union-attr]
            return True, "up"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)[:200]

    def get(self, key: str) -> Optional[str]:
        return self._safe(lambda: self._client.get(key))  # type: ignore[union-attr]

    def mget(self, keys: list[str]) -> List[Optional[str]]:
        """批量取值：一次往返替代 N 次 get（列表 / 归档的阅读增量叠加用）"""
        if not keys:
            return []
        return list(
            self._safe(lambda: self._client.mget(keys), [None] * len(keys))  # type: ignore[union-attr]
            or [None] * len(keys)
        )

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        def _fn():
            if ttl and ttl > 0:
                return self._client.setex(key, ttl, value)  # type: ignore[union-attr]
            return self._client.set(key, value)  # type: ignore[union-attr]

        return bool(self._safe(_fn, False))

    def delete(self, *keys: str) -> int:
        keys = [k for k in keys if k]
        if not keys:
            return 0
        return int(self._safe(lambda: self._client.delete(*keys), 0))  # type: ignore[union-attr]

    def delete_prefix(self, prefix: str) -> int:
        """按前缀清理（如文章列表缓存）。生产数据量大时建议换 SCAN，见 README"""
        full = PREFIX + prefix if not prefix.startswith(PREFIX) else prefix

        def _fn() -> int:
            keys = list(self._client.scan_iter(match=full + "*", count=200))  # type: ignore[union-attr]
            if not keys:
                return 0
            return self._client.delete(*keys)  # type: ignore[union-attr]

        return int(self._safe(_fn, 0))

    def exists(self, key: str) -> bool:
        return bool(self._safe(lambda: self._client.exists(key), False))  # type: ignore[union-attr]

    def expire(self, key: str, ttl: int) -> bool:
        return bool(self._safe(lambda: self._client.expire(key, ttl), False))  # type: ignore[union-attr]

    def ttl(self, key: str) -> int:
        return int(self._safe(lambda: self._client.ttl(key), -2))

    # ---------- 计数 ----------
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        return self._safe(lambda: self._client.incrby(key, amount))  # type: ignore[union-attr]

    def getset(self, key: str, value: Any) -> Optional[str]:
        return self._safe(lambda: self._client.getset(key, value))  # type: ignore[union-attr]

    def setex_if_absent(self, key: str, ttl: int, value: Any = 1) -> bool:
        return bool(
            self._safe(lambda: self._client.set(key, value, nx=True, ex=ttl), False)  # type: ignore[union-attr]
        )

    # ---------- JSON ----------
    def get_json(self, key: str) -> Any:
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.delete(key)
            return None

    def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            raw = json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            logger.warning("cache set_json serialize failed: %s", exc)
            return False
        return self.set(key, raw, ttl)

    # ---------- 高级：get_or_set ----------
    def get_or_set(
        self, key: str, producer: Callable[[], Any], ttl: Optional[int] = 300
    ) -> Any:
        """缓存命中直接返回，否则调用 producer 并写入缓存"""
        cached = self.get_json(key)
        if cached is not None:
            logger.debug("cache HIT %s", key)
            return cached
        logger.debug("cache MISS %s", key)
        value = producer()
        if value is not None:
            self.set_json(key, value, ttl)
        return value

    def keys(self, pattern: str) -> List[str]:
        full = PREFIX + pattern if not pattern.startswith(PREFIX) else pattern
        return list(self._safe(lambda: list(self._client.scan_iter(match=full, count=100)), []))  # type: ignore[union-attr]

    def flush_all(self) -> int:
        """清空本项目前缀下的所有 key（不影响同实例其他业务）"""
        return self.delete_prefix("")

    def info(self) -> dict:
        ok, detail = self.ping()
        if not ok:
            return {"status": "down", "detail": detail}
        try:
            n = len(self.keys("*"))
        except Exception:  # noqa: BLE001
            n = -1
        return {"status": "up", "keys": n}


# 全局单例
cache = Cache()


# ---------------- 业务级缓存失效 ----------------
def list_version() -> int:
    """当前列表缓存版本号（key 里带版本，失效只需自增）"""
    try:
        return int(cache.get(make_key(K_POST_LIST_VER)) or 0)
    except (TypeError, ValueError):
        return 0


def bump_list_version() -> None:
    """列表缓存整体失效：自增版本号，旧 key 靠 TTL 自然过期"""
    cache.incr(make_key(K_POST_LIST_VER))


def _invalidate_site_level() -> None:
    """清理站点级缓存：列表 / 分类 / 统计 / 站点信息（文章、分类变更时共用）"""
    bump_list_version()
    # 分类的 post_count 会跟着变，一并失效
    cache.delete(K_CATEGORIES)
    cache.delete(make_key(K_STATS, kind="overview"))
    cache.delete(make_key(K_STATS, kind="public"))
    cache.delete(make_key(K_SITE))


def invalidate_post(
    slug: str | None = None, post_id: int | None = None, site_level: bool = True
) -> None:
    """文章变更时清理相关缓存。

    site_level=False 用于「草稿保存」这类不影响任何公开视图的场景：
    详情缓存仍要清（草稿内容变了），但列表 / 统计 / 站点缓存无需整片失效。
    """
    keys = []
    if slug:
        # 公开与草稿两个命名空间都要清，避免旧值残留
        keys.append(make_key(K_POST_DETAIL, scope="pub", slug=slug))
        keys.append(make_key(K_POST_DETAIL, scope="draft", slug=slug))
    if post_id:
        keys.append(make_key(K_POST_DETAIL_ID, id=post_id))
    if keys:
        cache.delete(*keys)
    if site_level:
        _invalidate_site_level()


def invalidate_image_list() -> None:
    """图库列表缓存失效（上传 / 删除后调用）"""
    cache.delete(make_key(K_IMAGE_LIST, scope="all"))


def invalidate_taxonomy() -> None:
    """分类变更"""
    _invalidate_site_level()


def flush_view_deltas(db) -> int:
    """把 Redis 里累积的阅读量增量回写到 MySQL

    返回实际回写的文章数。文章详情页每 N 次访问触发一次。
    """
    from app.models.post import Post

    if not cache.available:
        return 0

    keys: Iterable[str] = cache.keys("post:views:*")
    total = 0
    flushed_ids: list[int] = []
    for key in keys:
        try:
            post_id = int(key.rsplit(":", 1)[-1])
        except ValueError:
            continue
        raw = cache.getset(key, 0)
        try:
            delta = int(raw or 0)
        except (TypeError, ValueError):
            delta = 0
        if delta <= 0:
            continue
        db.query(Post).filter(Post.id == post_id).update(
            {Post.views: Post.views + delta}
        )
        flushed_ids.append(post_id)
        total += 1
    if total:
        db.commit()
        # 增量已落库，缓存里的基数随之过期：必须失效详情 / 列表 / 统计缓存，
        # 否则会用「旧基数 + 已清空的增量」算出偏小的阅读数。
        slugs = dict(db.query(Post.id, Post.slug).filter(Post.id.in_(flushed_ids)).all())
        for pid in flushed_ids:
            invalidate_post(slug=slugs.get(pid), post_id=pid)
    return total
