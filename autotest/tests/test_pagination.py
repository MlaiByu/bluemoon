"""分页参数边界 —— 边界值分析在查询接口上的应用

被测契约（app/api/v1/posts.py 的 Query 声明）：
- page:      ge=1
- page_size: ge=1, le=100
- 非法值 → FastAPI 422（统一封装下 code=422）

返回结构（PageResult）：list / total / page / page_size /
total_pages / has_prev / has_next —— 结构断言不断言业务数值，
真实库里文章数随时在变，用例必须对数据量不敏感。
"""
import allure
import pytest

from apis.post_api import PostApi


@allure.feature("分页边界")
@pytest.mark.crud
class TestPaginationValidation:
    """非法分页参数必须被 422 拦截（公开接口即可验证，校验先于鉴权依赖）"""

    def test_page_zero_rejected(self, bare_client):
        """page=0：低于下界 ge=1 → 422"""
        resp = PostApi(bare_client).list_public({"page": 0})
        assert resp.status_code == 422
        assert resp.json()["code"] == 422

    def test_page_size_zero_rejected(self, bare_client):
        """page_size=0：低于下界 ge=1 → 422"""
        resp = PostApi(bare_client).list_public({"page_size": 0})
        assert resp.status_code == 422
        assert resp.json()["code"] == 422

    def test_page_size_over_limit_rejected(self, bare_client):
        """page_size=101：超过上界 le=100 → 422"""
        resp = PostApi(bare_client).list_public({"page_size": 101})
        assert resp.status_code == 422
        assert resp.json()["code"] == 422

    def test_admin_list_page_zero_rejected(self, admin_client):
        """后台列表同一套分页契约：page=0 → 422（契约不应因视角不同而漂移）"""
        resp = PostApi(admin_client).list_admin({"page": 0})
        assert resp.status_code == 422
        assert resp.json()["code"] == 422


@allure.feature("分页边界")
@pytest.mark.crud
class TestPaginationStructure:
    def test_page_size_upper_boundary_accepted(self, bare_client):
        """page_size=100：恰好落在上界 → 合法，返回条数不超过 100"""
        resp = PostApi(bare_client).list_public({"page_size": 100})
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]["list"]) <= 100

    def test_page_result_structure(self, bare_client):
        """默认参数：返回完整分页结构，字段自洽（对数据量不敏感的断言写法）"""
        resp = PostApi(bare_client).list_public()
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        # 结构完整：七个字段一个不少
        for field in ("list", "total", "page", "page_size", "total_pages", "has_prev", "has_next"):
            assert field in data, f"分页结构缺字段 {field}"
        # 字段自洽：第一页的推导关系必须成立
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] >= len(data["list"])
        assert data["has_prev"] is False, "第一页不可能有上一页"
        assert data["has_next"] == (data["page"] < data["total_pages"]), "has_next 应等于 page < total_pages"
