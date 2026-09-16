# -*- coding: utf-8 -*-
"""一次性迁移：图库长期化 + 清理测试数据 + 补建头像历史基线。

执行内容：
1. 把旧日期目录里的真实图库图片迁入长期目录 static/gallery/，
   并同步改写 posts.cover / posts.content 中的引用（若存在）；
2. 删除本轮验证脚本产生的测试图片文件与测试历史记录；
3. 恢复 admin 的真实头像（验证脚本曾覆盖），并为其补建一条历史记录（is_current=True）。
"""
import shutil

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.post import Post
from app.models.user import User
from app.models.user_avatar import UserAvatar

STATIC = settings.static_path

# 1) 迁移旧日期目录中的图库图片 → 长期目录 static/gallery/
OLD_GALLERY = STATIC / "2026" / "09" / "07" / "uploads" / "gallery"
NEW_GALLERY = STATIC / "gallery"
NEW_GALLERY.mkdir(parents=True, exist_ok=True)

moved = []
if OLD_GALLERY.is_dir():
    for f in sorted(OLD_GALLERY.glob("*")):
        if not f.is_file():
            continue
        dst = NEW_GALLERY / f.name
        if not dst.exists():
            shutil.move(str(f), str(dst))
        old_url = f"/static/2026/09/07/uploads/gallery/{f.name}"
        new_url = f"/static/gallery/{f.name}"
        moved.append((old_url, new_url))
        print("[migrate]", old_url, "->", new_url)

    # 清理迁移后残留的空目录（只删空目录）
    cur = OLD_GALLERY
    while cur != STATIC and cur.is_dir() and not any(cur.iterdir()):
        cur.rmdir()
        cur = cur.parent

db = SessionLocal()
try:
    # 1b) 同步改写文章中的引用
    if moved:
        for post in db.query(Post).all():
            changed = False
            content = post.content or ""
            cover = post.cover
            for old_url, new_url in moved:
                if old_url in content:
                    content = content.replace(old_url, new_url)
                    changed = True
                if cover == old_url:
                    cover = new_url
                    changed = True
            if changed:
                post.content = content
                post.cover = cover
                print("[rewrite post]", post.id)
        db.commit()

    # 2) 清理测试历史记录（仅清理本轮测试产生的时间戳文件）
    test_prefixes = (
        "avatar_20260908001459", "avatar_20260908001613",
        "avatar_20260908001641", "avatar_20260908011146",
    )
    test_rows = db.query(UserAvatar).all()
    for row in test_rows:
        if any(p in row.url for p in test_prefixes):
            p = STATIC / row.url.replace("/static/", "")
            if p.is_file():
                p.unlink()
            db.delete(row)
            print("[clean row]", row.url)
    db.commit()

    # 清理测试产生的图片文件
    test_files = [
        STATIC / "2026/09/08/uploads/post/20260908001543_0f646c25.png",
        STATIC / "gallery/20260908001543_03973254.png",
    ]
    for p in test_files:
        if p.is_file():
            p.unlink()
            print("[clean file]", p.name)

    # 3) 恢复真实头像并补建历史基线
    real_avatar = "/static/avatar/avatar_20260907210400_c61cb71a.jpg"
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        admin.avatar = real_avatar
        exists = db.query(UserAvatar).filter(UserAvatar.url == real_avatar).first()
        if not exists:
            f = STATIC / real_avatar.replace("/static/", "")
            db.add(UserAvatar(
                user_id=admin.id,
                url=real_avatar,
                filename=f.name,
                size=f.stat().st_size if f.is_file() else 0,
                is_current=True,
            ))
        else:
            exists.is_current = True
        db.commit()
        print("[restore avatar]", real_avatar)
    db.execute(text("SELECT 1"))
finally:
    db.close()

print("MIGRATION DONE")
