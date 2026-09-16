# -*- coding: utf-8 -*-
"""端到端验证：图库长期存储 + 头像独立目录 + 历史头像归档/恢复/清理。

场景：
1. 图库上传 → 落在长期目录 static/gallery/（非日期目录），且出现在图库列表
2. 图库图片被文章引用后删文 → 文件仍保留（长期资产不被随文清理）
3. 头像上传 → 落在独立目录 static/avatar/，不出现在图库列表
4. 更换头像 → 旧头像文件保留（归档）+ 历史列表按时间倒序 + is_current 标记正确
5. 从历史恢复 → users.avatar 切回旧 URL，旧文件依然存在
6. 删除历史头像 → 非当前可删、当前不可删
7. 数量上限：超过 AVATAR_HISTORY_LIMIT 时，最旧的非当前头像被清理
"""
import io
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_date_layout import BASE, STATIC, make_png, url_to_path  # noqa: E402


def upload_avatar(s, color):
    r = s.post(f"{BASE}/auth/avatar",
               files={"file": ("a.png", io.BytesIO(make_png(color)), "image/png")})
    r.raise_for_status()
    return r.json()["data"]


def history(s):
    r = s.get(f"{BASE}/auth/avatars")
    r.raise_for_status()
    return r.json()["data"]


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
    r.raise_for_status()
    s.headers["Authorization"] = "Bearer " + r.json()["data"]["access_token"]
    print("[0] login OK")

    # ---------- 1. 图库长期存储 ----------
    r = s.post(f"{BASE}/upload/image", params={"scope": "gallery"},
               files={"file": ("g.png", io.BytesIO(make_png((60, 200, 90))), "image/png")})
    r.raise_for_status()
    g_url = r.json()["data"]["url"]
    print("[1] gallery upload:", g_url)
    assert g_url.startswith("/static/gallery/"), g_url
    urls = {it["url"] for it in s.get(f"{BASE}/upload/images").json()["data"]}
    assert g_url in urls, "gallery image should be listed"
    print("[1] gallery image in long-term dir & listed OK")

    # ---------- 2. 长期资产不被随文清理 ----------
    r = s.post(f"{BASE}/posts", json={"title": "LONGTERM-TEST", "content": f"![g]({g_url})", "status": 1})
    r.raise_for_status()
    pid = r.json()["data"]["id"]
    r = s.delete(f"{BASE}/posts/{pid}")
    r.raise_for_status()
    assert os.path.exists(url_to_path(g_url)), "gallery image must survive post delete"
    print("[2] gallery image survives post delete OK")

    # ---------- 3. 头像独立目录 ----------
    a1 = upload_avatar(s, (30, 80, 200))
    url1 = a1["url"]
    print("[3] avatar upload:", url1)
    assert url1.startswith("/static/avatar/"), url1
    urls = {it["url"] for it in s.get(f"{BASE}/upload/images").json()["data"]}
    assert url1 not in urls, "avatar must NOT appear in gallery list"
    print("[3] avatar in isolated dir & hidden from gallery OK")

    # ---------- 4. 更换头像归档 ----------
    a2 = upload_avatar(s, (220, 40, 120))
    url2 = a2["url"]
    assert os.path.exists(url_to_path(url1)), "old avatar file must be archived, not deleted"
    hist = history(s)
    assert len(hist) >= 2, hist
    assert hist[0]["url"] == url2 and hist[0]["is_current"] is True, hist
    assert any(h["url"] == url1 and h["is_current"] is False for h in hist), hist
    times = [h["uploaded_at"] for h in hist]
    assert times == sorted(times, reverse=True), "history must be sorted desc by upload time"
    print(f"[4] avatar archived OK (history={len(hist)}, desc sorted)")

    # ---------- 5. 从历史恢复 ----------
    old_item = next(h for h in hist if h["url"] == url1)
    r = s.post(f"{BASE}/auth/avatar/restore", json={"id": old_item["id"]})
    r.raise_for_status()
    assert r.json()["data"]["user"]["avatar"] == url1, r.json()
    assert os.path.exists(url_to_path(url2)), "previous avatar should remain archived"
    hist2 = history(s)
    cur = [h for h in hist2 if h["is_current"]]
    assert len(cur) == 1 and cur[0]["url"] == url1, hist2
    print("[5] restore from history OK")

    # ---------- 6. 删除历史头像（当前不可删） ----------
    cur_item = cur[0]
    r = s.delete(f"{BASE}/auth/avatar/{cur_item['id']}")
    assert r.json().get("code") != 0, "current avatar must not be deletable"
    other = next(h for h in hist2 if h["url"] == url2)
    r = s.delete(f"{BASE}/auth/avatar/{other['id']}")
    assert r.status_code == 200, r.text
    assert not os.path.exists(url_to_path(url2)), "deleted history avatar file should be removed"
    print("[6] delete history avatar OK (current protected)")

    # ---------- 7. 数量上限清理 ----------
    limit = 3
    for i in range(limit + 2):  # 再传 5 张，触发上限清理
        upload_avatar(s, (i * 40 % 255, 90, 160))
    hist3 = history(s)
    assert len(hist3) <= limit, f"history should be capped at {limit}, got {len(hist3)}"
    assert sum(1 for h in hist3 if h["is_current"]) == 1, hist3
    print(f"[7] history capped at {limit} OK (current kept)")

    # 清理：删除本次测试产生的头像与图库图片
    for h in history(s):
        s.delete(f"{BASE}/auth/avatar/{h['id']}")
    s.delete(f"{BASE}/upload/image", params={"url": g_url})
    print("[8] test data cleaned")

    print("\nALL AVATAR/LONGTERM CHECKS PASSED")


if __name__ == "__main__":
    main()
