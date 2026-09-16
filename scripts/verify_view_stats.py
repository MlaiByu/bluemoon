#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阅读次数统计 —— 端到端验证脚本

验证目标：
  1. 阅读满 VIEW_READ_THRESHOLD_SECONDS（默认 5 秒）上报一次 → 阅读数 +1
  2. 去重窗口（默认 5 分钟）内重复上报 → 不计入，阅读数不变
  3. 窗口过期后的新一次有效阅读 → 继续 +1（能累加，不会被永久锁死）
  4. 详情接口返回的阅读数与上报结果一致（Redis 增量 + MySQL 基数）
  5. 不存在的文章上报 → 安全返回，不产生脏数据

用法：
    # 后端跑在 8000（默认）
    .venv\\Scripts\\python.exe scripts\\verify_view_stats.py
    # 指定端口（例如另起 8001 实例时不干扰现有服务）
    .venv\\Scripts\\python.exe scripts\\verify_view_stats.py --base http://127.0.0.1:8001/api/v1

注意：脚本会临时删除 Redis 中的去重锁来模拟「窗口过期」，不会改动文章正文 / 阅读数基线。
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blog-api"))

DEFAULT_BASE = "http://127.0.0.1:8000/api/v1"

_passed = 0
_failed = 0


def check(name: str, ok: bool, detail: str = "") -> bool:
    global _passed, _failed
    if ok:
        _passed += 1
        print(f"  [PASS] {name}" + (f"  ({detail})" if detail else ""))
    else:
        _failed += 1
        print(f"  [FAIL] {name}" + (f"  ({detail})" if detail else ""))
    return ok


def req(base: str, method: str, path: str, body: dict | None = None):
    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"raw": raw}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE, help="API 基地址")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    print("=" * 62)
    print("阅读次数统计 端到端验证")
    print(f"API: {base}")
    print("=" * 62)

    # 0. 服务可用性 + 配置
    try:
        st, r = req(base, "GET", "/posts?page=1&page_size=1")
    except Exception as exc:  # noqa: BLE001
        print(f"无法连接后端：{exc}")
        print("请先启动后端（start-all.bat），或加 --base 指向已运行的实例。")
        return 1
    if not check("后端可访问", st == 200, f"HTTP {st}"):
        return 1

    from app.core.config import settings  # noqa: E402
    from app.services.cache import K_POST_VIEW_LOCK, cache, make_key  # noqa: E402

    threshold = settings.VIEW_READ_THRESHOLD_SECONDS
    dedup_ttl = settings.VIEW_DEDUP_TTL_SECONDS
    check("有效阅读门槛为 5 秒", threshold == 5, f"VIEW_READ_THRESHOLD_SECONDS={threshold}")
    print(f"  [INFO] 去重窗口 VIEW_DEDUP_TTL_SECONDS={dedup_ttl}s")

    first = r["data"]["list"][0]
    post_id = first["id"]
    slug = urllib.parse.quote(first["slug"])
    print(f"\n[测试文章] id={post_id} slug={first['slug']}")

    # 1. 基线阅读数（走详情接口，含 Redis 未回写增量）
    st, d = req(base, "GET", f"/posts/detail/{slug}")
    if not check("读取文章详情", st == 200, f"HTTP {st}"):
        return 1
    base_views = d["data"]["views"]
    print(f"  [INFO] 基线阅读数 = {base_views}")

    # 2. 首次有效阅读（模拟阅读满 5 秒后上报）
    st, v = req(base, "POST", f"/posts/{post_id}/view")
    ok = st == 200 and v["data"]["counted"] is True
    check("首次上报计入", ok, f"counted={v['data'].get('counted')}")
    v1 = v["data"]["views"]
    check("阅读数 +1", v1 == base_views + 1, f"{base_views} -> {v1}")

    # 3. 去重窗口内重复上报（重复进入 / 重复触发 5 秒）→ 不应累加
    st, v = req(base, "POST", f"/posts/{post_id}/view")
    ok = st == 200 and v["data"]["counted"] is False
    check("窗口内重复上报被去重", ok, f"counted={v['data'].get('counted')}")
    v2 = v["data"]["views"]
    check("阅读数未重复累加", v2 == v1, f"{v1} -> {v2}")

    # 连续 3 次刷新式上报也不应增长
    for _ in range(3):
        req(base, "POST", f"/posts/{post_id}/view")
    st, v = req(base, "POST", f"/posts/{post_id}/view")
    check("连续上报仍不增长", v["data"]["views"] == v1, f"views={v['data']['views']}")

    # 4. 模拟去重窗口过期（清掉 Redis 锁）后再次有效阅读 → 继续累加
    lock_key = make_key(K_POST_VIEW_LOCK, post_id=post_id, ip="127.0.0.1")
    cache.delete(lock_key)
    st, v = req(base, "POST", f"/posts/{post_id}/view")
    ok = st == 200 and v["data"]["counted"] is True
    check("窗口过期后可再次计入", ok, f"counted={v['data'].get('counted')}")
    v3 = v["data"]["views"]
    check("阅读数继续 +1", v3 == v1 + 1, f"{v1} -> {v3}")

    # 5. 详情接口返回的阅读数与上报结果一致
    st, d = req(base, "GET", f"/posts/detail/{slug}")
    check("详情接口阅读数同步", d["data"]["views"] == v3, f"detail={d['data']['views']} vs report={v3}")

    # 6. 不存在的文章 → 安全返回
    st, v = req(base, "POST", "/posts/99999999/view")
    check("不存在的文章安全返回", st == 200 and v["data"]["counted"] is False,
          f"HTTP {st}, counted={v['data'].get('counted')}")

    # 7. 清理：把本次验证产生的锁删掉，避免影响后续手工测试
    cache.delete(lock_key)

    print("\n" + "=" * 62)
    print(f"结果：{_passed} 项通过，{_failed} 项失败")
    print("=" * 62)
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
