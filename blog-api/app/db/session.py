"""数据库引擎与会话"""
from collections.abc import Iterator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.MYSQL_ECHO,
    pool_pre_ping=True,      # 自动重连（MySQL wait_timeout 兜底）
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, future=True
)


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：请求级会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db() -> tuple[bool, str]:
    """健康检查用：能否连上数据库"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "up"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:200]


def execute_sql_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(text(stmt))


def scalar_one(sql: str, **params: Any) -> Any:
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()
