"""全局配置（pydantic-settings v2）"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# blog-api/ 根目录
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- App ----------
    APP_NAME: str = "bluemoon blog"
    APP_ENV: str = "development"
    # 默认关闭；本地开发如需 SQL/请求细节，在 .env 里显式设 DEBUG=true
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---------- MySQL ----------
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "bluemoon"
    MYSQL_PASSWORD: str = "bluemoon123"
    MYSQL_DB: str = "bluemoon"
    MYSQL_ECHO: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            f"?charset=utf8mb4"
        )

    @property
    def DATABASE_URL_ADMIN(self) -> str:
        """不带库名，用于建库 / 建用户"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/?charset=utf8mb4"
        )

    # ---------- Redis ----------
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = True

    CACHE_TTL_POST_DETAIL: int = 600
    CACHE_TTL_POST_LIST: int = 300
    CACHE_TTL_STATS: int = 120

    # ---------- 阅读量统计 ----------
    # 有效阅读门槛（秒）：用户进入文章并持续阅读满该时长，阅读数 +1
    VIEW_READ_THRESHOLD_SECONDS: int = 5
    # 同一访客（按 IP 识别）对同一文章的去重窗口（秒）：窗口内重复进入不重复计数
    VIEW_DEDUP_TTL_SECONDS: int = 300
    # Redis 中累积到该增量后批量回写 MySQL
    VIEW_FLUSH_THRESHOLD: int = 10

    # ---------- Security ----------
    # 开发环境默认值可直接使用；生产环境由 _validate_production_secrets 强制拒绝默认值
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ---------- 登录防爆破 ----------
    # 同一「用户名 + 来源 IP」在窗口内的失败次数达到上限后，锁定 LOGIN_LOCK_SECONDS 秒
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_FAIL_WINDOW_SECONDS: int = 300
    LOGIN_LOCK_SECONDS: int = 300

    # ---------- 反向代理信任 ----------
    # 只有来源 IP 在此白名单内时，才采信 X-Forwarded-For / X-Real-IP。
    # 留空 = 完全不信任任何转发头（直连部署的正确默认值）——
    # 否则任何客户端都能靠伪造 XFF 绕过按 IP 的去重与限流。
    # 例：TRUSTED_PROXIES=127.0.0.1,::1
    TRUSTED_PROXIES: str = ""

    @property
    def trusted_proxies_set(self) -> set:
        return {p.strip() for p in self.TRUSTED_PROXIES.split(",") if p.strip()}

    # ---------- Upload ----------
    # 历史遗留：旧的上传根目录，仅用于识别历史 URL，新上传不再使用
    # （新布局为 static/avatar/、static/gallery/、static/{Y}/{M}/{D}/uploads/post/）
    UPLOAD_DIR: str = "static/uploads"

    # ---------- 头像历史 ----------
    # 每个用户保留的历史头像数量上限（超出后按时间从旧到新清理，当前使用的头像不清理）
    AVATAR_HISTORY_LIMIT: int = 20
    # 历史头像保留天数，0 表示不按时间清理（仅受数量上限约束）
    AVATAR_HISTORY_TTL_DAYS: int = 0
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    # 注意：不要放开 svg —— /static 与站点同源托管，带脚本的 SVG 会变成存储型 XSS。
    # 需要矢量图时请先在服务端清洗，或改为下发到独立域名。
    ALLOWED_IMAGE_EXT: str = "jpg,jpeg,png,gif,webp,bmp"
    # 图片像素上限（宽 × 高），超过即拒绝：防「解压炸弹」（几十 KB 的 PNG 解出几 GB 位图）
    # 5000 万像素约等于 7000×7000，远超站点任何合法用途
    IMAGE_MAX_PIXELS: int = 50_000_000
    # 图库列表（/upload/images）的响应缓存时长（秒）：该接口要扫盘 + 查引用，代价高
    CACHE_TTL_IMAGE_LIST: int = 60


    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def static_path(self) -> Path:
        return BASE_DIR / "static"

    @property
    def allowed_ext_set(self) -> set:
        return {e.strip().lower() for e in self.ALLOWED_IMAGE_EXT.split(",") if e.strip()}

    # ---------- Blog ----------
    BLOG_TITLE: str = "Bluemoon"
    BLOG_SUBTITLE: str = "一个安静写字的地方"
    BLOG_DESCRIPTION: str = "个人博客"
    BLOG_AUTHOR: str = "bluemoon"
    BLOG_ICP: str = ""
    FRONTEND_URL: str = "http://127.0.0.1:5173"

    # ---------- Frontend (SPA fallback) ----------
    # 前端构建产物目录（history 模式路由回退用），相对路径基于 blog-api/
    FRONTEND_DIST: str = "../blog-web/dist"

    @property
    def frontend_dist_path(self) -> Path:
        p = Path(self.FRONTEND_DIST)
        return p if p.is_absolute() else (BASE_DIR / p).resolve()

    # ---------- CORS ----------
    # 默认只放行本地前端；生产环境请通过 .env 显式配置实际域名
    CORS_ORIGINS: str = "http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _validate_production_secrets(self):
        """生产环境硬校验：禁止默认密钥与 CORS 通配符。

        仅在 APP_ENV == "production" 时触发，开发环境行为完全不变。
        """
        if self.APP_ENV == "production":
            if self.SECRET_KEY == "change-me" or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "生产环境 SECRET_KEY 必须是 >=32 位的随机串，禁止使用默认值"
                )
            if "*" in self.cors_origins_list:
                raise ValueError("生产环境禁止 CORS 通配符")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
