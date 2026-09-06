"""初始化数据库：建库、建用户、建表、可选灌入演示数据

用法：
    python scripts/init_db.py            # 建库 + 建用户 + 建表 + 种子数据
    python scripts/init_db.py --no-seed  # 只建表，不灌数据
    python scripts/init_db.py --drop     # 先删表再重建（危险）
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymysql  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import Category, Post, Profile, User  # noqa: F401,E402
from app.utils.markdown import count_words  # noqa: E402
from app.utils.slug import slugify  # noqa: E402

# 引导用的高权限账号（默认 root 空密码，仅本地开发）
ADMIN_USER = os.getenv("MYSQL_ADMIN_USER", "root")
ADMIN_PASSWORD = os.getenv("MYSQL_ADMIN_PASSWORD", "")

OK = "  [OK] "
WARN = "  [!!] "


def ensure_database_and_user() -> None:
    """以 root 身份创建数据库与业务账号"""
    print(f"\n[1/4] 连接 MySQL {settings.MYSQL_HOST}:{settings.MYSQL_PORT} (as {ADMIN_USER})")
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            charset="utf8mb4",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"{WARN}无法连接 MySQL：{exc}")
        print("       请确认 MySQL 已启动，或设置 MYSQL_ADMIN_USER / MYSQL_ADMIN_PASSWORD")
        sys.exit(1)

    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
        )
        print(f"{OK}数据库 `{settings.MYSQL_DB}` 就绪")

        if settings.MYSQL_USER != ADMIN_USER:
            cur.execute(
                "CREATE USER IF NOT EXISTS %s@'%%' IDENTIFIED WITH mysql_native_password BY %s",
                (settings.MYSQL_USER, settings.MYSQL_PASSWORD),
            )
            cur.execute(
                "ALTER USER %s@'%%' IDENTIFIED WITH mysql_native_password BY %s",
                (settings.MYSQL_USER, settings.MYSQL_PASSWORD),
            )
            cur.execute(f"GRANT ALL PRIVILEGES ON `{settings.MYSQL_DB}`.* TO %s@'%%'", (settings.MYSQL_USER,))
            cur.execute("FLUSH PRIVILEGES")
            print(f"{OK}用户 `{settings.MYSQL_USER}` 已创建并授权")
    conn.close()


def ensure_tables(drop: bool = False) -> None:
    print(f"\n[2/4] 建表（{settings.MYSQL_DB}）")
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
    if drop:
        Base.metadata.drop_all(engine)
        print(f"{OK}已删除旧表")
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        rows = conn.execute(text("SHOW TABLES")).fetchall()
    print(f"{OK}表已就绪：{', '.join(r[0] for r in rows)}")
    engine.dispose()


def seed(drop: bool = False) -> None:
    from datetime import datetime, timedelta

    from sqlalchemy.orm import Session, sessionmaker

    from app.models.post import PostStatus

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db: Session = SessionLocal()

    print("\n[3/4] 初始化管理员与站点资料")
    admin = db.query(User).filter(User.username == "admin").first()
    if admin is None:
        admin = User(
            username="admin",
            nickname="bluemoon",
            email="admin@bluemoon.dev",
            hashed_password=get_password_hash("admin123"),
            bio="保持好奇，保持热爱。",
            is_superuser=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"{OK}管理员已创建：admin / admin123  （请尽快修改密码！）")
    else:
        print(f"{WARN}管理员 admin 已存在，跳过")

    if db.query(Profile).filter(Profile.id == 1).first() is None:
        db.add(
            Profile(
                id=1,
                nickname=settings.BLOG_AUTHOR,
                bio=settings.BLOG_DESCRIPTION,
                content=(
                    "## 你好，我是 bluemoon\n\n"
                    "这里是我的个人博客，用来记录**技术笔记**、**读书思考**和一些生活碎片。\n\n"
                    "### 我在做什么\n\n"
                    "- 后端：Python / FastAPI / MySQL / Redis\n"
                    "- 前端：Vue 3 / Element Plus\n"
                    "- 正在折腾：把想法快速变成能跑起来的东西\n\n"
                    "### 联系我\n\n"
                    "欢迎通过邮箱或 GitHub 找到我。\n"
                ),
                location="中国",
                email="admin@bluemoon.dev",
                github="https://github.com/",
            )
        )
        db.commit()
        print(f"{OK}站点资料已初始化")

    print("\n[4/4] 灌入演示文章")
    if db.query(Post).count() > 0 and not drop:
        print(f"{WARN}文章表非空，跳过演示数据")
    else:
        cats = [
            Category(name="技术笔记", slug="tech", description="踩坑与总结", sort_order=30),
            Category(name="生活随笔", slug="life", description="琐碎但真实", sort_order=20),
            Category(name="读书观影", slug="reading", description="输入与输出", sort_order=10),
        ]
        for c in cats:
            if not db.query(Category).filter(Category.slug == c.slug).first():
                db.add(c)
        db.commit()

        cat_map = {c.slug: c for c in db.query(Category).all()}
        demo = [
            {
                "title": "从零搭建一个 FastAPI + Vue3 博客",
                "cat": "tech",
                "tags": ["Python", "FastAPI", "Vue3"],
                "cover": "",
                "summary": "记录后端分层、Redis 缓存策略与前端工程化的一次完整实践。",
                "content": """## 为什么要自己写博客

市面上的博客平台很多，但自己搭一遍才能真正理解**请求是怎么走的**、**缓存什么时候失效**。

## 技术选型

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | FastAPI + SQLAlchemy 2.0 |
| 数据库 | MySQL 8（utf8mb4） |
| 缓存 | Redis |

## 缓存策略

文章详情和列表是最容易被反复查询的数据，非常适合放 Redis：

```python
def get_or_set(key, producer, ttl=300):
    cached = cache.get_json(key)
    if cached is not None:
        return cached
    value = producer()
    cache.set_json(key, value, ttl)
    return value
```

关键是**写操作后要让缓存失效**：

- 修改文章 → 删 `bm:post:detail:{slug}`
- 新增/删除 → 清 `bm:post:list:*` 前缀

## 小结

先跑起来，再慢慢打磨。
""",
            },
            {
                "title": "Redis 缓存的三个常见坑",
                "cat": "tech",
                "summary": "缓存穿透、击穿、雪崩，以及我在这个项目里的处理方式。",
                "content": """## 缓存穿透

查询一个**根本不存在**的 id，缓存永远不命中，请求直接打到数据库。

> 解决方案：空值也缓存（短 TTL）+ 参数校验。

```python
value = producer()
if value is None:
    cache.set(key, "", ttl=60)   # 缓存空值
```

## 缓存击穿

某个热点 key 过期的瞬间，大量请求同时打到数据库。

## 缓存雪崩

大量 key 在同一时刻过期。解决办法是给 TTL 加随机抖动。

## 这个项目怎么做的

- 不存在的文章返回 404，不缓存
- Redis 挂了自动降级直连 MySQL
- 列表缓存按前缀批量清理
""",
            },
            {
                "title": "MySQL 8 免安装版的正确打开方式",
                "cat": "tech",
                "summary": "下载 zip、写 my.ini、初始化数据目录，三步搞定。",
                "content": """## 1. 准备配置文件

```ini
[mysqld]
basedir=D:/mysql8
datadir=D:/mysql8/data
port=3306
character-set-server=utf8mb4
default_authentication_plugin=mysql_native_password
```

注意 Windows 下路径用**正斜杠**。

## 2. 初始化

```bash
mysqld --defaults-file=D:/mysql8/my.ini --initialize-insecure
```

`--initialize-insecure` 会让 root 初始密码为空，仅适合本地开发。

## 3. 启动

写一个 `start-mysql.bat`，双击即可。
""",
            },
            {
                "title": "深夜写代码的一点感想",
                "cat": "life",
                "summary": "安静的时候，思路反而最清楚。",
                "content": """凌晨的键盘声很轻，思路却格外清楚。

白天被打断的思路，到了夜里总能续上。大概是因为终于没有人找你改需求了。

> 写代码最好的状态：你知道下一步要做什么，而且它刚好能跑通。

记录于此，写给未来的自己。
""",
            },
            {
                "title": "《人类简史》读后：想象的力量",
                "cat": "reading",
                "cover": "",
                "summary": "国家、金钱、公司，都是我们共同相信的故事。",
                "content": """## 核心观点

赫拉利认为，智人之所以能统治地球，是因为我们具备**讨论虚构事物**的能力。

## 让印象最深的例子

- 金钱：一张纸本身没有价值，但所有人都相信它有价值
- 国家：边界是画在地图上的，但人们愿意为它付出生命
- 公司：一个法律虚构的"人"，却能拥有财产

## 一点疑问

作者把"快乐"归结为生化机制，这个解释是不是过于简化了？
""",
            },
        ]

        now = datetime.now()
        for i, d in enumerate(demo):
            post = Post(
                title=d["title"],
                slug=slugify(d["title"]),
                summary=d["summary"],
                content=d["content"],
                cover=d.get("cover") or None,
                status=PostStatus.PUBLISHED,
                is_top=(i == 0),
                category_id=cat_map[d["cat"]].id,
                author_id=admin.id,
                word_count=count_words(d["content"]),
                published_at=now - timedelta(days=(len(demo) - i) * 3),
                created_at=now - timedelta(days=(len(demo) - i) * 3),
            )
            post.views = (len(demo) - i) * 17
            db.add(post)

        # 一篇草稿
        draft = Post(
            title="（草稿）关于博客的下一步计划",
            slug=slugify("关于博客的下一步计划"),
            summary="还没写完，先存个草稿。",
            content="## TODO\n\n- [ ] 全文搜索\n- [ ] RSS 订阅\n- [ ] 评论系统\n",
            status=PostStatus.DRAFT,
            category_id=cat_map["tech"].id,
            author_id=admin.id,
            word_count=count_words("## TODO 全文搜索 RSS 订阅 评论系统"),
        )
        db.add(draft)
        db.commit()
        print(f"{OK}已灌入 {len(demo)} 篇已发布文章 + 1 篇草稿")

    db.close()
    engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="bluemoon 数据库初始化")
    parser.add_argument("--drop", action="store_true", help="先删除所有表再重建")
    parser.add_argument("--no-seed", action="store_true", help="不灌入演示数据")
    args = parser.parse_args()

    print("=" * 56)
    print("  bluemoon blog - 数据库初始化")
    print(f"  MySQL {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
    print("=" * 56)

    ensure_database_and_user()
    ensure_tables(drop=args.drop)
    if not args.no_seed:
        seed(drop=args.drop)

    from app.services.cache import cache

    if cache.available:
        cache.flush_all()
        print(f"{OK}已清空 Redis 缓存")
    print("\n完成！接下来：python run.py\n")


if __name__ == "__main__":
    main()
