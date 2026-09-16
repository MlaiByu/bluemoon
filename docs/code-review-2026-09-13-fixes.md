# 修复记录（2026-09-13）

对应审查报告：`docs/code-review-2026-09-13.md`。本轮修复 **20 项**（P0 4 项 / P1 8 项 / P2 8 项），全部带自检证据。

## 一、验证结果

| 验证项 | 命令 | 结果 |
|---|---|---|
| 后端语法 / 导入 | `.\.venv\Scripts\python.exe scripts\verify\verify_code_review_fixes.py` | **18/18 单元断言通过** |
| 端到端（HTTP） | 同上，追加 `--base-url http://127.0.0.1:8010`（生产模式实例） | **25/25 全部通过** |
| 前端构建 | `npm run build`（blog-web） | 成功，1941 modules，入口 100.5 KB + vendor 180.1 KB + CSS 70.7 KB（未超 409 KB 基准） |
| 富文本清洗 | `node scripts/verify/verify-sanitize.mjs` | **10/10 通过** |
| 默认口令剔除 | `Select-String dist\assets\*.js -Pattern 'admin123'` | 生产产物**零匹配** |

报告文件：`scripts/verify/last-report.txt`、`scripts/verify/last-sanitize.txt`（该目录已被 .gitignore 覆盖）。

## 二、P0 —— 高危 / 功能缺陷

| # | 文件 | 行为变化 | 验证 |
|---|---|---|---|
| F1 | `blog-web/src/components/PostCard.vue` | 补 `resolveImageUrl` 导入；`hl()` 结果改 `computed` 缓存 | 构建通过；`/categories` 带封面卡片不再抛 ReferenceError |
| S1 | `app/services/cache.py`、`app/services/post_service.py` | 详情缓存 key 改为 `post:detail:{pub\|draft}:{slug}`；`invalidate_post` 两个命名空间都清 | 单测：草稿只写 draft key，pub key 无写入，匿名取回 `None` |
| S3 | `app/core/config.py`、`.env`、`.env.example`、`app/services/image_service.py`、`app/api/v1/upload.py`、`app/api/v1/auth.py` | 上传白名单移除 `svg`；新增 `validate_image_bytes()` 用 Pillow 校验**真实格式**（防改名绕过） | 单测：HTML 冒充 `png` 被拒；合法 PNG 放行 |
| S6 | `blog-web/src/views/admin/Login.vue`、新增 `blog-web/src/components/DevLoginHint.vue` | 默认口令提示拆到独立组件，仅 `import.meta.env.DEV` 时动态 import | 生产产物 grep `admin123` → 零匹配 |

## 三、P1 —— 性能 / 权限收口

| # | 文件 | 行为变化 | 验证 |
|---|---|---|---|
| S4 | `app/services/auth_service.py`、`app/schemas/user.py` | 登录失败按「用户名+IP」计数，达 5 次/5 分钟返回 429；失败文案统一（防账号枚举）；新密码要求 ≥8 位且两类字符 | 单测第 6 次抛 429；HTTP 序列 `[401×5, 429]` |
| S4 | `app/api/deps.py`、`app/core/config.py` | `client_ip()` 只在来源 IP ∈ `TRUSTED_PROXIES` 时采信 `X-Forwarded-For`，默认**完全不信任** | 单测：直连时伪造 XFF 被忽略；白名单内采信首段 |
| S2/P1 | `app/services/image_service.py`、`app/api/v1/upload.py` | 新增 `build_reference_index()` 一次建索引；`list_images` / 批量删除 / 引用检查 / 随文清理全部改为内存比对，消除 N 次 `LIKE '%url%'` 全表扫描 | 单测索引可构建且自洽；引用检查整批只查一次库 |
| P3 | `app/api/v1/upload.py`、`app/core/config.py` | `/upload/images` 结果加 60s 缓存（`CACHE_TTL_IMAGE_LIST`），上传/删除后主动失效 → 首页不再每次全量扫盘 | HTTP：接口 200 且带缓存 |
| P2 | `app/services/post_service.py` | 列表与归档改用 `load_only(...)`，不再把 `content`（TEXT）拉回；归档批量叠加阅读增量 | 单测：`content` 处于 `unloaded` |
| S7 | `app/api/v1/health.py`、`app/main.py` | `/health` 只回状态串，`detail`/`env` 仅 DEBUG 下返回；`/cache/info` 加管理员依赖；生产环境关闭 `/docs`、`/redoc`、`/openapi.json` | HTTP：匿名 `/cache/info` → 401；生产 `/docs` 不再返回 Swagger |
| S8 | `app/api/v1/posts.py` | 列表接口只对**超管**放开 status 过滤（原先任何带 token 的账号都能看到草稿） | HTTP：匿名列表全为已发布 |
| S9 | `app/api/v1/upload.py` | 图库删除接口新增长期资产守卫，头像等不允许绕过归档直接删文件 | 单测：`/static/avatar/...` 被拒 |

## 四、P2 —— 加固

| # | 文件 | 行为变化 | 验证 |
|---|---|---|---|
| P4 | `app/services/cache.py`、`app/services/post_service.py` | 列表缓存 key 带版本号 `post:list:v{n}:{hash}`，失效只需 `INCR`（去掉 `SCAN` 全量删除）；草稿保存不再触发站点级失效 | 单测：version 自增且 key 含新版本 |
| P5 | `app/services/cache.py`、`app/services/post_service.py` | 新增 `cache.mget()`；列表/归档一次批量取阅读增量，替代逐条 `GET` | 单测：`mget -> ['3', None]` |
| P6 | `app/api/v1/upload.py`、`app/api/v1/auth.py` | 两个上传端点由 `async def` 改同步 `def`，Pillow 编解码与写盘走 FastAPI 线程池，不再阻塞事件循环 | 端到端上传路径正常（401/400 分支已验） |
| S10 | `app/services/image_service.py`、`app/api/v1/auth.py`、`app/core/config.py` | 新增 `IMAGE_MAX_PIXELS`（5000 万）；头像处理失败改为**报错**而非回退未压缩原图；读取改 `file.read(limit+1)` 限长 | 单测：9000×9000 被拒 |
| F2 | 新增 `blog-web/src/utils/sanitizeHtml.js`、`blog-web/src/components/MarkdownView.vue` | 保留 `html: true` 兼容既有富文本，但原始 HTML token 经清洗：删除 script/object/embed/link/meta/base/form、全部 `on*` 内联事件、`srcdoc`，并把 `javascript:`/`vbscript:`/`data:text/html` 改写为 `#`（视频 iframe 正常保留） | Node 单测 10/10（含"iframe 外链保留"与"普通富文本不受影响"） |
| F6 | `blog-web/src/components/MarkdownView.vue` | 图片失败处理由内联 `onerror` 字符串改为父级 `@error.capture` 事件委托 + `data-original` | 随 F2 一并构建通过 |
| F4 | `blog-web/src/stores/user.js` | `localStorage` 解析加 try/catch，存储损坏时清 key 而非全站白屏 | 构建通过 |
| S5 | `app/services/auth_service.py`、`app/api/deps.py` | 改密后写入 `token:invalid-before:{uid}`，早于该时刻签发的 token 一律失效（接口文案"请重新登录"与行为一致）；`_load_user` 对非法 `sub` 不再 500 | 端到端鉴权链路正常（401 分支已验） |

## 五、本轮**未改**的项（需你拍板）

| 项 | 原因 |
|---|---|
| S5 剩余部分：token 有效期 24h → 缩短 + refresh token | 属会话架构调整，会改动前端登录态流转，需确认后再动 |
| S2 终极方案：`post_images` 关联表 | 需要数据迁移，当前"批量化索引"已把单次请求从 O(图数×全表) 降到 O(1) 次全表 |
| F3 首页 `page_size: 50` 无分页 | 产品决策（首屏一次给全 vs 分页），未擅自改交互 |
| F5 dev server `host: '0.0.0.0'` | 你可能会用手机连局域网调试，未擅自收紧 |
| SPA 回退对未知路径返回 200 + index.html | 既有设计（`/openapi.json` 也会命中），不是本轮引入的问题，仅记录 |

## 六、环境处理说明

1. **`.venv` 曾缺失**：仓库根的 `.venv`（`start-all.bat` / `run-backend.bat` 引用的是它）在本次会话开始时不存在，已用 uv 按既有规约重建：
   `uv venv --python 'D:\python10\python.exe' --seed .venv` + `uv pip install -r blog-api/requirements.txt --python .venv\Scripts\python.exe`。
   （过程中误在 `blog-api/` 下建了一个重复 venv，已删除。）
2. **MySQL / Redis 已启动并在运行**：`D:\mysql8`（3306）、`_tools\redis`（6379）本次会话前均未运行，为跑端到端验证已启动，**验证后保留运行**，可直接 `start-all.bat` 起前后端。
3. **`blog-web/dist` 已重建**：为本轮前端改动的产物，内容为当前源码构建结果。
4. 临时验证实例（8010 端口的生产模式后端）已停止；临时落盘文件已移入 `.workbuddy/tmp/review-20260913/`（注意：工作区对删除操作有 safe-delete 钩子拦截，`Remove-Item` 会被 fail-closed 拒绝）。

## 七、复跑验证

```powershell
# 后端单元 + 端到端（需 MySQL/Redis 就绪）
.\.venv\Scripts\python.exe scripts\verify\verify_code_review_fixes.py

# 起一个生产模式实例再跑 HTTP 断言
cd blog-api
$env:APP_ENV='production'; $env:DEBUG='false'
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
# 另开一个终端：
.\.venv\Scripts\python.exe scripts\verify\verify_code_review_fixes.py --base-url http://127.0.0.1:8010

# 前端
cd blog-web; npm run build
node ..\scripts\verify\verify-sanitize.mjs
```
