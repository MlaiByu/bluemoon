# -*- coding: utf-8 -*-
"""端到端验证：旧布局 URL 兼容识别 + 共用图边界场景。

旧布局（重构前）的 URL 形式仍被生命周期逻辑识别：
- uploads/posts/YYYY/MM/DD/  （旧作用域优先）
- uploads/YYYY/MM/DD/        （最早遗留目录，视作随文管理）
覆盖场景：
1. 旧布局图片被文章独占引用 → 列表隐藏；删文后文件清理
2. 边界：两篇文章共用 → 删至最后一处引用才清理
3. 未被引用的独立图片正常展示、可管理
"""
import io
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_date_layout import BASE, STATIC, list_urls, url_to_path, create_post  # noqa: E402
from verify_date_layout import make_png  # noqa: E402


def place_legacy_image(name: str) -> str:
    """模拟旧布局遗留图片：写入 uploads/YYYY/MM/DD/ 日期目录。"""
    now = time.localtime()
    rel_dir = os.path.join(STATIC, "uploads", str(now.tm_year), f"{now.tm_mon:02d}", f"{now.tm_mday:02d}")
    os.makedirs(rel_dir, exist_ok=True)
    path = os.path.join(rel_dir, name)
    with open(path, "wb") as f:
        f.write(make_png((90, 90, 200)))
    return "/static/" + os.path.relpath(path, STATIC).replace(os.sep, "/")


def main():
    import requests  # noqa: F401

    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
    r.raise_for_status()
    s.headers["Authorization"] = "Bearer " + r.json()["data"]["access_token"]
    print("[0] login OK")

    # ---- 场景1：旧布局图片被文章引用 → 隐藏；删文后清理 ----
    url1 = place_legacy_image(f"legacy_solo_{int(time.time())}.png")
    pid1 = create_post(s, "LEGACY-COMPAT-TEST 独占", f"![x]({url1})")
    assert url1 not in list_urls(s), "referenced legacy img must be hidden from list"
    assert os.path.exists(url_to_path(url1)), "file must remain while referenced"
    r = s.delete(f"{BASE}/posts/{pid1}")
    r.raise_for_status()
    assert not os.path.exists(url_to_path(url1)), "legacy img file should be removed after post delete"
    print("[1] legacy-layout image lifecycle OK")

    # ---- 场景2：共用图 → 删至最后一处引用才清理 ----
    url2 = place_legacy_image(f"legacy_shared_{int(time.time())}.png")
    pid_a = create_post(s, "LEGACY-COMPAT-TEST 共用A", f"![a]({url2})")
    pid_b = create_post(s, "LEGACY-COMPAT-TEST 共用B", f"![b]({url2})")
    delete_post = s.delete
    r = delete_post(f"{BASE}/posts/{pid_a}")
    r.raise_for_status()
    assert os.path.exists(url_to_path(url2)), "shared img must remain while post B references it"
    r = delete_post(f"{BASE}/posts/{pid_b}")
    r.raise_for_status()
    assert not os.path.exists(url_to_path(url2)), "shared img cleaned after last reference gone"
    print("[2] shared legacy image retained until last reference deleted OK")

    # ---- 场景3：未引用的独立图片正常展示、可管理 ----
    url3 = place_legacy_image(f"legacy_orphan_{int(time.time())}.png")
    assert url3 in list_urls(s), "unreferenced independent img should be listed"
    r = s.delete(f"{BASE}/upload/image", params={"url": url3})
    assert r.status_code == 200 and url3 not in list_urls(s)
    print("[3] unreferenced independent image listed & manageable OK")

    print("\nALL LEGACY-COMPAT CHECKS PASSED")


if __name__ == "__main__":
    main()
