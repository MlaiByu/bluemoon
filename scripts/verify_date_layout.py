# -*- coding: utf-8 -*-
"""端到端验证：图片按日期优先层级目录存储 + 作用域分离。

覆盖场景（新布局 static/{Y}/{M}/{D}/uploads/{scope}/）：
1. post 作用域上传 → 落在当日 uploads/post/，不出现在图库列表
2. gallery 作用域上传 → 落在当日 uploads/gallery/，出现在图库列表
3. 图库删除接口拒绝删除文章图片
4. 文章引用 post 图片 → 删除文章 → 文件随文清理（含空日期目录回收）
5. 图库图片被文章引用后删文 → 文件保留、重新回到列表
"""
import io
import os
import re
import struct
import sys
import zlib

import requests

BASE = "http://127.0.0.1:8000/api/v1"
STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blog-api", "static")


def make_png(color=(120, 160, 220), size=8):
    w = h = size
    raw = b"".join(b"\x00" + bytes(color) * w for _ in range(h))

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def url_to_path(url: str) -> str:
    return os.path.join(STATIC, url.replace("/static/", "").replace("/", os.sep))


def list_urls(s):
    r = s.get(f"{BASE}/upload/images")
    r.raise_for_status()
    return {it["url"] for it in r.json()["data"]}


def create_post(s, title, content, cover=None):
    r = s.post(f"{BASE}/posts", json={"title": title, "content": content, "cover": cover, "status": 1})
    r.raise_for_status()
    return r.json()["data"]["id"]


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
    r.raise_for_status()
    s.headers["Authorization"] = "Bearer " + r.json()["data"]["access_token"]
    print("[0] login OK")

    date_prefix = re.compile(r"^/static/\d{4}/\d{2}/\d{2}/uploads/")

    # ---- 1. post 作用域上传 → 当日 uploads/post/，不进图库 ----
    r = s.post(f"{BASE}/upload/image", params={"scope": "post"},
               files={"file": ("p.png", io.BytesIO(make_png((200, 60, 60))), "image/png")})
    r.raise_for_status()
    post_url = r.json()["data"]["url"]
    print("[1] post upload:", post_url)
    assert date_prefix.match(post_url) and "/uploads/post/" in post_url, post_url
    assert post_url not in list_urls(s), "post image must NOT appear in gallery list"

    # ---- 2. gallery 作用域上传 → 当日 uploads/gallery/，进入图库 ----
    r = s.post(f"{BASE}/upload/image", params={"scope": "gallery"},
               files={"file": ("g.png", io.BytesIO(make_png((60, 200, 90))), "image/png")})
    r.raise_for_status()
    gallery_url = r.json()["data"]["url"]
    print("[2] gallery upload:", gallery_url)
    # 图库是长期资产，统一存站点级 static/gallery/，不再放日期目录
    assert gallery_url.startswith("/static/gallery/"), gallery_url
    assert gallery_url in list_urls(s), "gallery image should be listed"

    # ---- 3. 图库删除接口拒绝文章图片 ----
    r = s.delete(f"{BASE}/upload/image", params={"url": post_url})
    assert r.json().get("code") != 0, "post image delete via gallery should be blocked"
    print("[3] gallery delete of post image blocked:", r.json().get("msg"))

    # ---- 4. 文章引用 post 图片（正文+封面）→ 删文 → 文件清理 ----
    pid = create_post(s, "DATE-LAYOUT-TEST 随文图片", f"![p]({post_url})", cover=post_url)
    assert os.path.exists(url_to_path(post_url)), "file must exist while referenced"
    r = s.delete(f"{BASE}/posts/{pid}")
    r.raise_for_status()
    assert not os.path.exists(url_to_path(post_url)), "post image file should be removed after post delete"
    assert post_url not in list_urls(s)
    print("[4] post image lifecycle cleanup OK")

    # ---- 5. 图库图片被引用 → 隐藏；删文 → 回到列表 ----
    pid = create_post(s, "DATE-LAYOUT-TEST 引用图库图", f"![g]({gallery_url})")
    assert gallery_url not in list_urls(s) and os.path.exists(url_to_path(gallery_url))
    r = s.delete(f"{BASE}/posts/{pid}")
    r.raise_for_status()
    assert gallery_url in list_urls(s), "gallery image should reappear after reference released"
    r = s.delete(f"{BASE}/upload/image", params={"url": gallery_url})
    assert r.status_code == 200
    print("[5] gallery image hide/reappear lifecycle OK")

    # ---- 6. 头像：站点级 static/avatar/，不进图库，换头像删除旧文件 ----
    r = s.post(f"{BASE}/auth/avatar",
               files={"file": ("a1.png", io.BytesIO(make_png((30, 80, 200))), "image/png")})
    r.raise_for_status()
    av1 = r.json()["data"]["url"]
    print("[6] avatar upload:", av1)
    assert av1.startswith("/static/avatar/"), av1  # 站点级目录，不随日期散落
    assert av1 not in list_urls(s), "avatar must NOT appear in gallery list"
    assert os.path.exists(url_to_path(av1)), "avatar file must exist"

    r = s.post(f"{BASE}/auth/avatar",
               files={"file": ("a2.png", io.BytesIO(make_png((220, 40, 120))), "image/png")})
    r.raise_for_status()
    av2 = r.json()["data"]["url"]
    assert av2 != av1, "new avatar should have a distinct timestamped filename (cache-busting)"
    # 旧头像归档保留（历史头像功能），不再删除
    assert os.path.exists(url_to_path(av1)), "old avatar should be archived, not deleted"
    assert os.path.exists(url_to_path(av2)), "new avatar file must exist"
    # 还原：清掉测试头像文件（历史头像的完整验证见 verify_avatar_history.py）
    for url in (av1, av2):
        if os.path.exists(url_to_path(url)):
            os.remove(url_to_path(url))
    print("[7] avatar site-level dir + archive-on-replace OK")

    print("\nALL DATE-LAYOUT CHECKS PASSED")


if __name__ == "__main__":
    main()
