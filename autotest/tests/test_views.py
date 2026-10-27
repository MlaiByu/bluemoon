"""阅读上报与去重 —— 本系统最独特的业务设计（三层去重的服务端层）

被测契约（post_service.record_view）：
1. 只有「已发布」文章计数；草稿 / 不存在的文章软拒绝：
   返回 counted=False, views=0（不抛 404，便于前端静默处理）
2. 同一 IP 对同一文章在 VIEW_DEDUP_TTL_SECONDS（默认 300s）窗口内只计一次，
   Redis SET NX EX 原子加锁实现；Redis 不可用时降级为直接 +1（不防刷但不丢计数）
3. 返回 {"counted": 本次是否计入, "views": 当前阅读数}

测试可行性说明：去重的 key 是 IP+文章 ID。每条用例都通过工厂新建文章
（ID 全局唯一），不存在历史 dedup key 残留，重复运行用例依然稳定。

数据安全说明（README 三件套的显式让步）：
阅读主链路必须用发布态文章（草稿不计阅读量），因此本文件会把测试文章
短暂置为 status=1 —— 标题仍带 [autotest] 标记，用例结束立即改回草稿
（把前台暴露窗口压到秒级），fixture teardown 再统一删除。
"""
import allure
import pytest

from apis.post_api import PostApi


@pytest.fixture(scope="module")
def redis_online(bare_client):
    """去重依赖 Redis SET NX EX；Redis 降级时后端直接 +1，去重用例不适用。

    环境不满足 = skip（不是这次要测的问题），与 fail 语义分清。
    """
    data = bare_client.get("/health").json()["data"]
    if data.get("redis") != "up":
        pytest.skip("Redis 未在线，服务端去重层降级，去重用例不适用")
    return True


def _demote_to_draft(admin_client, post: dict) -> None:
    """把发布态测试文章改回草稿，压缩前台暴露窗口（用例主体的最后一步）。"""
    payload = {**post["payload"], "status": 0}
    resp = PostApi(admin_client).update(post["id"], payload)
    assert resp.json()["code"] == 0, f"测试文章改回草稿失败：{resp.text}"


@allure.feature("阅读统计")
@pytest.mark.crud
class TestViewRecording:
    def test_view_counted_for_published(self, admin_client, draft_post_factory):
        """正向：发布态文章上报 → counted=True，views 至少 +1；随后立即改回草稿"""
        post = draft_post_factory(status=1)
        api = PostApi(admin_client)
        try:
            resp = api.record_view(post["id"])
            body = resp.json()
            assert body["code"] == 0
            data = body["data"]
            assert data["counted"] is True, f"首次上报应计数：{data}"
            assert data["views"] >= 1, f"计数后 views 应至少为 1：{data}"
        finally:
            _demote_to_draft(admin_client, post)

    def test_view_rejected_for_draft(self, admin_client, draft_post_factory):
        """契约：草稿不计阅读量 —— 软拒绝（counted=False），不抛 404"""
        post = draft_post_factory()  # 默认 status=0
        resp = PostApi(admin_client).record_view(post["id"])
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["counted"] is False, f"草稿不应计阅读量：{body}"
        assert body["data"]["views"] == 0

    def test_view_nonexistent_post_soft_reject(self, admin_client):
        """契约：不存在的文章软拒绝 —— 与草稿同一响应形态（counted=False, views=0）

        用远超自增序列的 ID（10 亿）保证"不存在"这个前提稳定成立。
        """
        resp = PostApi(admin_client).record_view(10**9)
        body = resp.json()
        assert body["code"] == 0
        assert body["data"] == {"counted": False, "views": 0}


@allure.feature("阅读统计")
@pytest.mark.security
class TestViewDedup:
    """同 IP 5 分钟窗口去重 —— 防刷阅读量的服务端兜底

    测试进程所有请求同源（127.0.0.1 / CI runner IP），
    同一文章连续多次上报正好落在同一个 IP 去重窗口内。
    """

    def test_repeated_views_deduped_within_window(
        self, admin_client, bare_client, draft_post_factory, redis_online
    ):
        """核心用例：第 1 次上报计数，窗口内重复上报全部拦截且 views 不变"""
        post = draft_post_factory(status=1)
        api = PostApi(admin_client)
        try:
            first = api.record_view(post["id"]).json()["data"]
            assert first["counted"] is True, f"首次上报应计数：{first}"
            assert first["views"] >= 1

            # 同 IP 窗口内重复上报：被 SET NX EX 锁拦截
            for i in range(2, 4):
                again = api.record_view(post["id"]).json()["data"]
                assert again["counted"] is False, (
                    f"第 {i} 次上报不应计数 —— 去重失效，阅读数可被刷！"
                )
                assert again["views"] == first["views"], (
                    f"被去重拦截的上报不得改变 views：{again} vs {first}"
                )
        finally:
            _demote_to_draft(admin_client, post)

    def test_dedup_is_per_post(self, admin_client, bare_client, draft_post_factory, redis_online):
        """去重粒度是 IP+文章：同 IP 对另一篇文章的上报应正常计数"""
        post = draft_post_factory(status=1)
        api = PostApi(admin_client)
        try:
            data = api.record_view(post["id"]).json()["data"]
            assert data["counted"] is True, (
                f"新文章不应受其他文章去重锁影响（key 是 IP+post_id）：{data}"
            )
        finally:
            _demote_to_draft(admin_client, post)
