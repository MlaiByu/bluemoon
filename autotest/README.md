# 接口自动化测试（autotest/）

针对本仓库 [blog-api](../blog-api)（FastAPI + MySQL + Redis）后端的接口自动化测试框架。

> 定位：与被测系统**同仓演进**——接口变更和用例变更出现在同一个 PR 里，
> 从结构上消灭「被测系统改了、测试没跟上」的用例漂移（测试左移的工程落地）。

## 框架分层

```
autotest/
tests/        用例层：只表达业务语义（登录成功/草稿不可见/匿名被拦截）
apis/         接口封装层：一个接口一个方法，URL/参数变动只改这里
common/       公共层：ApiClient（Session 封装、Token 注入、超时、日志）
config/       配置层：环境地址、账号、标记（密码走环境变量，不进库）
```

换环境只改配置、换接口只改封装、用例只写业务断言——这是分层的意义。

## 被测系统契约（测试依据）

- 统一响应封装：`{"code": 0, "msg": "...", "data": ...}`，业务成功 code=0
- 错误映射：401 未认证 / 403 无权限 / 404 不存在 / 422 参数校验 / 429 限流
- 认证：JWT Bearer；登出后 token 进入服务端黑名单立即失效
- 文章状态：0=草稿（前台不可见） 1=发布

## 用例清单（v1：22 条）

| 文件 | 用例 | 类型 |
|------|------|------|
| test_health | 健康检查封装正确 / MySQL 在线 | smoke |
| test_auth | 登录成功 / 密码错误 / 缺参数 / 登出后旧 token 失效 | smoke |
| test_posts_crud | 草稿增查改删 / 后台列表可搜 / 缺标题 / 标题 200 边界 / 201 越界 / 非法 status | crud |
| test_authz | 5 个管理员接口匿名拦截 / 伪造 token / 草稿对前台列表与详情不可见 | security |

## 快速开始

```bash
# 0. 起被测系统（主仓根目录）：start-all.bat 或 docker-compose up -d

# 1. 创建虚拟环境（Python 3.12）
cd autotest
D:\python\python312\python.exe -m venv .venv
.venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置管理员密码（不进代码库；或使用 config/config.local.yaml）
set BM_ADMIN_PASSWORD=你的管理员密码

# 4. 运行
pytest
```

## CI

GitHub Actions：[.github/workflows/autotest.yml](../.github/workflows/autotest.yml)

流程：MySQL 8 + Redis 7 service 容器 → `scripts/init_db.py` 建库建表灌种子（admin/admin123）→ 后台启动 uvicorn + 健康检查轮询 → `pytest --alluredir` → Allure 结果 artifact。push 到 main 与所有 PR 自动执行，全部通过才允许合并。

## 数据安全设计（重要）

被测的是真实博客，测试数据零污染三件套：

1. **草稿态**：测试文章一律 `status=0`，对前台完全不可见
2. **标记**：标题统一带 `[autotest]` 前缀，可识别可搜索
3. **自动清理**：fixture teardown 保证删除，用例失败也清理

## 已发现的被测系统缺陷（自动化测试产出）

### BUG-1 全文搜索不覆盖存量文章（已修复 2026-10-27）

- **现象（2026-10-24 首次实证）**：keyword 搜索对 2026-10-24 之前创建的文章全部失效（前台列表 / 后台列表 / 详情搜索同源）
- **实证链（首轮）**：`MATCH(title,summary,content) AGAINST('123')` 返回空，而 `LIKE '%123%'` 能命中 id=33；同一时刻新建文章（API 与 SQL 两种插入路径）均能立即被搜到 → 当时锁定"存量行不在索引内"，修复建议为重建索引
- **深化实证（2026-10-27，本地回归 21/22 失败暴露）**：本地库**任何词**的 MATCH（自然语言 / BOOLEAN MODE）都为空，LIKE 却命中；`DROP INDEX + ADD FULLTEXT ... WITH PARSER ngram` 重建**依然为空**；同一份 2 行数据装进新表 MATCH 立即命中；独立临时表 + ngram 正常 → 定位为 **posts 表的 InnoDB FULLTEXT 辅助状态损坏**（疑似历史强杀 / 崩溃恢复遗留），比"存量行缺失"严重得多——整份索引实际为空
- **修复**：`OPTIMIZE TABLE posts`（InnoDB 语义 = recreate + analyze，整表物理重建 + 全部索引重置）。执行后 MATCH 恢复，本地 22/22 全绿
- **教训**：①FT 辅助状态损坏时，ALTER DROP+ADD 重建索引无效，OPTIMIZE（或整表重建）才是确定性修复；②"同数据新表对照"是隔离「表级损坏 vs 实例配置」的关键实验；③CI 绿 ≠ 本地绿——环境差异正是自动化回归要抓的问题

### BUG-2 模型包漏导 UserAvatar，独立脚本崩溃（CI 首跑暴露，已修复）

- **现象**：CI 全新环境执行 `scripts/init_db.py` 时抛 `InvalidRequestError: expression 'UserAvatar' failed to locate a name`，初始化直接失败
- **根因**：`app/models/__init__.py` 注释声称"统一导入所有模型"，实际漏导 `user_avatar.py`；`User.avatars` 关系按字符串名解析，mapper 配置时找不到目标类。本地应用启动时路由间接导入了全部模型，掩盖了这个缺陷
- **影响**：任何脱离应用主程序单独导入模型包的脚本（init_db、Alembic 迁移）都无法运行
- **修复**：模型包补导 `UserAvatar` 并加入 `__all__`（提交 `fix(models): register UserAvatar in models package`）

### BUG-3 全文索引未纳入建表元数据，全新环境搜索 500（CI 二跑暴露，已修复）

- **现象**：CI 干净库中带 keyword 的搜索请求全部返回 500，20/22 用例通过、2 条搜索用例失败
- **根因**：`ft_search` FULLTEXT 索引只存在于手工维护的本地库，`Post` 模型未声明 → `create_all` 建出的 posts 表没有该索引 → `MATCH ... AGAINST` 抛 MySQL 1191
- **影响**：任何从零部署的环境（新机器、CI、Docker）站内搜索整体不可用
- **修复**：`init_db.py` 建表后幂等补建 ngram 全文索引（提交 `fix(init_db): ensure posts ngram fulltext index after create_all`）

## Roadmap

- [x] Allure 报告（allure-pytest 已接入依赖）
- [x] GitHub Actions CI 门禁（MySQL 8 + Redis 7 service 容器，同仓自动部署被测系统）
- [x] 与被测系统合并为单仓库（接口与用例同 PR 演进）
- [ ] 文章列表分页参数边界用例
- [ ] 阅读上报去重（同 IP 5 分钟窗口）用例
- [ ] 分类接口用例
