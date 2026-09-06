"""全局配置（pydantic-settings v2）"""
from functools import lru_cache
from pathlib import Path
from typing import List

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
    DEBUG: bool = True
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

    # ---------- Security ----------
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ---------- Upload ----------
    UPLOAD_DIR: str = "static/uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    ALLOWED_IMAGE_EXT: str = "jpg,jpeg,png,gif,webp,bmp,svg"

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
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
