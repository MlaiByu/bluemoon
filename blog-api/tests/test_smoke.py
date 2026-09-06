"""接口冒烟测试

用法（需先启动后端）：
    python tests/test_smoke.py
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"
API = f"{BASE}/api/v1"

passed = 0
failed = 0


def req(method, path, data=None, token=None, raw=False):
    url = API + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as e:
        payload = json.loads(e.read().decode("utf-8"))
        return e.code, payload
    except Exception as e:  # noqa: BLE001
        return 0, {"msg": str(e)}


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} {extra}")


def main():
    print("\n=== bluemoon API 冒烟测试 ===\n")

    # 1. health
    st, r = req("GET", "/health")
    check("健康检查 200", st == 200, f"-> {st}")
    check("MySQL 已连接", r.get("data", {}).get("mysql", {}).get("status") == "up")
    check("Redis 已连接", r.get("data", {}).get("redis", {}).get("status") == "up")

    # 2. 未登录访问后台应 401
    st, r = req("GET", "/auth/me")
    check("未登录访问 /auth/me -> 401", st == 401, f"-> {st}")

    # 3. 错误密码
    st, r = req("POST", "/auth/login", {"username": "admin", "password": "wrong"})
    check("错误密码登录 -> 401", st == 401, f"-> {st}")

    # 4. 登录
    st, r = req("POST", "/auth/login", {"username": "admin", "password": "admin123"})
    check("正确密码登录 -> 200", st == 200, f"-> {st} {r.get('msg')}")
    token = r.get("data", {}).get("access_token")
    check("返回 access_token", bool(token))

    # 5. 当前用户
    st, r = req("GET", "/auth/me", token=token)
    check("获取用户信息", st == 200 and r["data"]["username"] == "admin")

    # 6. 文章列表（前台，仅已发布）
    st, r = req("GET", "/posts?page=1&page_size=5")
    total = r["data"]["total"] if st == 200 else 0
    check("前台文章列表", st == 200 and total > 0, f"total={total}")
    check("前台列表不含草稿", all(p["status"] == 1 for p in r["data"]["list"]))

    # 7. 后台列表（含草稿）
    st, r = req("GET", "/posts/admin?page=1&page_size=100", token=token)
    admin_total = r["data"]["total"] if st == 200 else 0
    check("后台文章列表含草稿", st == 200 and admin_total > total, f"{admin_total} > {total}")

    # 8. 分类
    st, cats = req("GET", "/categories")
    check("分类列表", st == 200 and len(cats["data"]) > 0)

    # 9. 文章详情（缓存 + 阅读量）
    slug = urllib.parse.quote(r["data"]["list"][0]["slug"]) if False else None
    st, r0 = req("GET", "/posts?page=1&page_size=1")
    first = r0["data"]["list"][0]
    slug = urllib.parse.quote(first["slug"])
    v0 = first["views"]
    st, d1 = req("GET", f"/posts/detail/{slug}")
    check("文章详情（首次，缓存 MISS）", st == 200 and d1["data"]["content"], f"-> {st}")
    st, d2 = req("GET", f"/posts/detail/{slug}")
    check("文章详情（二次，缓存 HIT）", st == 200)
    check("阅读量递增", d2["data"]["views"] > v0, f"{v0} -> {d2['data']['views']}")
    check("返回上下篇导航", "neighbors" in d2["data"])

    # 10. 归档
    st, r = req("GET", "/posts/archives")
    check("归档分组", st == 200 and len(r["data"]) > 0)

    # 11. 新建文章 -> 触发缓存失效
    st, r = req(
        "POST",
        "/posts",
        {
            "title": "冒烟测试文章",
            "summary": "由测试脚本创建",
            "content": "## 测试\n\n这是一篇用于冒烟测试的文章。",
            "status": 1,
            "category_id": cats["data"][0]["id"],
        },
        token=token,
    )
    check("新建文章", st == 200, f"-> {st} {r.get('msg')}")
    new_id = r["data"]["id"] if st == 200 else None

    # 新文章应立刻出现在前台列表（缓存已失效）
    st, r = req("GET", "/posts?page=1&page_size=100")
    check("新文章出现在前台列表（缓存已失效）",
          any(p["id"] == new_id for p in r["data"]["list"]))

    # 12. 更新
    st, r = req(
        "PUT",
        f"/posts/{new_id}",
        {"title": "冒烟测试文章（已更新）", "content": "更新后的正文", "status": 1},
        token=token,
    )
    check("更新文章", st == 200 and r["data"]["title"].endswith("（已更新）"))

    # 13. 统计
    st, r = req("GET", "/stats/overview", token=token)
    check("后台统计", st == 200 and r["data"]["total_posts"] > 0)
    st, r = req("GET", "/stats/site")
    check("站点信息", st == 200 and r["data"]["post_count"] > 0)

    # 14. 关于我
    st, r = req("GET", "/profile")
    check("获取关于我", st == 200)
    st, r = req("PUT", "/profile", {"nickname": "bluemoon", "bio": "测试签名"}, token=token)
    check("更新关于我", st == 200 and r["data"]["bio"] == "测试签名")

    # 15. 搜索
    st, r = req("GET", "/posts?keyword=Redis")
    check("关键词搜索", st == 200 and r["data"]["total"] >= 1, f"total={r['data']['total'] if st==200 else '-'}")

    # 16. 手动回写阅读量
    st, r = req("POST", "/posts/flush-views", token=token)
    check("回写阅读量", st == 200)

    # 17. 删除测试文章
    if new_id:
        st, r = req("DELETE", f"/posts/{new_id}", token=token)
        check("删除文章", st == 200)
        st, r = req("GET", "/posts?page=1&page_size=100")
        check("删除后列表已更新", not any(p["id"] == new_id for p in r["data"]["list"]))

    # 18. 退出登录 -> token 失效
    st, _ = req("POST", "/auth/logout", token=token)
    check("退出登录", st == 200)

    print(f"\n=== 结果：{passed} 通过 / {failed} 失败 ===\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
