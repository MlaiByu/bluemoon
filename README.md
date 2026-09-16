# BlueMoon 博客

> 一个安静写字的地方 —— 记录生活、技术与思考的个人博客。

基于 **FastAPI + Vue3 + MySQL + Redis** 构建的全栈个人博客系统，参考 [hexo-theme-butterfly](https://github.com/jerryc127/hexo-theme-butterfly) 视觉风格，采用 16px 圆角卡片质感与 `#667eea → #764ba2` 蓝紫渐变语言。

前后端分离，克隆后按下面「快速开始」操作即可跑起完整站点。

## 项目简介

- **后端 `blog-api/`**：基于 FastAPI 构建，提供 RESTful API
  - 文章 CRUD、分类管理、个人资料、站点统计、SEO 元信息
  - JWT 鉴权（登录 / Token 刷新），登录失败按「用户名 + IP」限流锁定
  - Redis 三档 TTL 缓存（详情 / 列表 / 统计），未启用时自动降级直连 MySQL
  - 图片上传：按日期分目录归档 + 衍生图（缩略图）生成，真实格式校验与解压炸弹防护
  - 头像历史管理（换头像保留历史，可回滚）、随机语录、随机背景图接口
- **前端 `blog-web/`**：基于 Vue3 + Vite + Element Plus
  - 首页：随机语录 + 随机背景图（每次刷新变化）
  - 品牌字标 `BlueMoonの博客`（保留「の」字）
  - 自研主题切换器「拉灯模式」：纸灯笼样式 + 竹纹 + 流苏拉绳 + 朱砂/暖橙配色
  - 暗色 / 亮色双主题（CSS 变量驱动，首屏防闪烁）
  - Images 相册页（后台上传/删除 + 公开浏览 + 灯箱）
  - Markdown 渲染 + highlight.js 代码高亮 + HTML 富文本清洗

## 快速开始

### 前置条件

| 依赖 | 版本 | 是否必需 | 说明 |
| --- | --- | --- | --- |
| Python | 3.10+ | 必需 | 后端运行时 |
| Node.js | 18+（推荐 22.x） | 必需 | 前端构建 |
| MySQL | 8.0 | 必需 | 数据存储，需要可登录的账号 |
| Redis | 5.0+ | 可选 | 缓存加速；未启动时后端自动降级，功能不受影响 |

### 四步跑起来

```bash
# 1) 克隆
# HTTPS（无需配置 SSH key，推荐）
git clone https://github.com/MlaiByu/bluemoon.git
# SSH（本机已配置 SSH key 时可用）
# git clone git@github.com:MlaiByu/bluemoon.git

cd bluemoon
```

```bash
# 2) 后端：建虚拟环境 + 装依赖
#    约定：.venv 位于仓库根目录，不要在 blog-api/ 内另建（启动脚本按根目录查找）
python -m venv .venv

# Windows
.venv\Scripts\python.exe -m pip install -r blog-api\requirements.txt
# macOS / Linux
source .venv/bin/activate && pip install -r blog-api/requirements.txt
```

```bash
# 3) 配置环境变量 + 初始化数据库
cd blog-api

# 复制配置模板（Windows 用 copy）
cp .env.example .env

# 建库 + 建业务账号 + 建表 + 灌入演示数据（含 5 篇示例文章）
../.venv/Scripts/python.exe scripts/init_db.py      # Windows
# python scripts/init_db.py                          # macOS / Linux（已激活 venv）

# 启动后端 → http://127.0.0.1:8000
python run.py
```

```bash
# 4) 前端（另开一个终端）
cd blog-web
npm install
npm run dev        # → http://127.0.0.1:5173
```

打开 <http://127.0.0.1:5173> 即可看到站点。前端通过 Vite 代理把 `/api` 转发到 `127.0.0.1:8000`，无需额外配置跨域。

### 默认管理账号

| 项 | 值 |
| --- | --- |
| 后台地址 | <http://127.0.0.1:5173/admin/login> |
| 用户名 | `admin` |
| 密码 | `admin123` |

> **⚠️ 仅用于本地开发。** 对外部署前请立刻修改密码，并把 `.env` 中的 `SECRET_KEY` 换成随机长串：
>
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(48))"
> ```
>
> `APP_ENV=production` 时若 `SECRET_KEY` 仍为默认值或短于 32 位，应用会**拒绝启动**（见 `app/core/config.py`）。

### Windows 一键启动（可选）

依赖装好后，双击根目录 `start-all.bat`：依次拉起 **MySQL → Redis → 后端 → 前端**，每一步都有端口就绪检测，任一步失败会停在明确的错误提示上（窗口保留报错，不闪退）。`stop-all.bat` 按端口优雅收工，不会误杀机器上其他同名实例。

脚本**不写死任何绝对路径**，克隆到任意目录都能用。本机特有路径用 `local.env.bat` 覆盖：

```bat
copy local.env.bat.example local.env.bat
:: 编辑 local.env.bat，按本机情况修改 MYSQL / NODEBIN / REDIS
```

`local.env.bat` 已被 `.gitignore` 忽略，可以放心填本机路径，不会上传。

## Docker 部署（推荐：一条命令跑起来）

本机只需装 **Docker**，不必单独安装 MySQL / Redis / Python / Node —— 全部跑在容器里。适合快速体验、部署到服务器，或交给别人复现。

### 一条命令

```bash
# Windows
scripts\docker-up.bat

# Linux / macOS
./scripts/docker-up.sh
```

脚本会自动完成：生成含随机密钥的 `.env` → 构建镜像 → 启动 MySQL、Redis、应用 → 等待健康检查通过 → 打印访问地址。

想自己控制配置，也可以手动两步：

```bash
cp .env.docker.example .env      # Windows: copy .env.docker.example .env
# 填写 SECRET_KEY、MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD
docker compose up -d --build
```

启动后访问 <http://localhost:8000>，后台入口 `/admin/login`，账号 `admin / admin123`。

### 服务拓扑

```
                   ┌────────────── 浏览器 ──────────────┐
                   │      http://localhost:8000         │
                   └────────────────┬───────────────────┘
                                    │ 唯一入口
                   ┌────────────────▼───────────────────┐
                   │  api    FastAPI + Vue 构建产物      │
                   │  8000   API / 静态资源 / SPA 同源   │
                   └───────┬─────────────────┬──────────┘
                           │ mysql:3306      │ redis:6379
              ┌────────────▼──────────┐ ┌────▼─────────────────┐
              │  mysql  8.0           │ │  redis  7-alpine     │
              │  volume: mysql_data   │ │  volume: redis_data  │
              └───────────────────────┘ └──────────────────────┘
```

**前端刻意不单独开容器。** `blog-api/app/main.py` 的 SPA fallback 要在服务端把文章级 SEO 元信息注入 `index.html`（微信/QQ 抓取分享卡片依赖它，抓取器不执行 JS）；把 `index.html` 交给独立 nginx 托管会让这条链路失效。而前端 axios 的 baseURL 是相对路径 `/api/v1`，与后端同源即可，本来也不需要反向代理 —— 所以正确的形态是「后端托管前端产物」，一个容器、一个入口。

### 服务、端口与卷

| 服务 | 镜像 | 端口 | 卷 / 挂载 | 说明 |
| --- | --- | --- | --- | --- |
| `api` | 本地构建 `docker/api.Dockerfile` | **8000 → 8000** | `./blog-api/static` → `/app/static` | 唯一对外入口：API + 前端 + 上传图片 |
| `mysql` | `mysql:8.0` | 仅容器内网 3306 | `mysql_data`（命名卷） | 库表数据持久化 |
| `redis` | `redis:7-alpine` | 仅容器内网 6379 | `redis_data`（命名卷） | 开 AOF，避免阅读量增量丢失 |

- 数据库与缓存**默认不对宿主机暴露端口**。需要用本机客户端连进去调试时，取消 `docker-compose.yml` 中对应 `ports:` 的注释（只绑 `127.0.0.1`）。
- 上传图片挂在宿主机目录 `blog-api/static/`，与本地开发共用同一份素材：容器化后既有图片直接可见，备份只需拷这个目录。

### 环境变量

集中在仓库根目录的 `.env`（从 `.env.docker.example` 复制）。它只作为 compose 的变量插值来源，浏览器访问不涉及。

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | ✅ | JWT 签名密钥；`APP_ENV=production` 时不足 32 位会拒绝启动 |
| `MYSQL_ROOT_PASSWORD` | ✅ | 首次建库与建业务账号用 |
| `MYSQL_PASSWORD` | ✅ | 业务账号密码 |
| `API_PORT` | — | 宿主机端口，默认 8000 |
| `APP_ENV` / `DEBUG` | — | 默认 `production` / `false`（关闭 `/docs`） |
| `AUTO_INIT_DB` | — | 默认 `true`：启动时幂等地建表并灌演示数据 |
| `REDIS_ENABLED` | — | 默认 `true`；置 `false` 完全关闭缓存 |
| `TRUSTED_PROXIES` | — | 默认留空，见下方「客户端真实 IP」 |

### 常用操作

| 目的 | 命令 |
| --- | --- |
| 查看应用日志 | `docker compose logs -f api` |
| 查看容器状态 | `docker compose ps` |
| 进入容器 | `docker compose exec api sh` |
| 重跑数据库初始化 | `docker compose exec api python scripts/init_db.py` |
| 改代码后只重建应用 | `docker compose up -d --build api` |
| 停止（保留数据） | `scripts\docker-down.bat` 或 `./scripts/docker-down.sh` |
| 停止并清空数据 | `docker compose down -v` ⚠️ 数据库与缓存卷一并删除 |

### 三个需要知道的点

**1. 客户端真实 IP 会受影响**

Docker Desktop（Windows / macOS）的端口映射会把所有来访者的源 IP 改写成网关地址，后端看到的都是同一个 IP。这会削弱两处按 IP 的机制：文章「停留 5 分钟才 +1」的去重窗口，以及登录失败按「用户名 + IP」的限流粒度。

- 在 **Linux 主机上直接跑 Docker** 时源 IP 正常保留，不受影响；
- 若在 Windows / macOS 上对公网提供服务，请在前面加一层反向代理（nginx / traefik），由它写入 `X-Forwarded-For`，并把 `TRUSTED_PROXIES` 设成该代理的地址（如 `172.18.0.0/16`）。
- 留空时后端**完全不采信任何转发头** —— 这是刻意的防伪造设计（否则任何人伪造 XFF 就能绕过限流），不要为了「拿到真实 IP」而随手填 `*`。

**2. mysql 镜像锁在 8.0，不要升 major**

`blog-api/scripts/init_db.py` 用 `IDENTIFIED WITH mysql_native_password` 创建业务账号，而该插件在 MySQL 8.4 起被默认禁用（9.x 移除）。升到 8.4+ 后容器初始化会直接报错。

**3. 首次启动会慢一些**

api 容器要先等 MySQL 健康检查通过，再执行一次幂等的建库建表与种子数据，最后才启动 uvicorn。首次约 1–2 分钟属正常，之后启动会跳过已完成的初始化，很快。

## 前置依赖准备

### MySQL 8

任意方式安装，只要满足：**3306 端口可连**、**`root` 可登录**（或你知道 root 密码）。

`blog-api/scripts/init_db.py` 会自动完成建库、建业务账号、建表、灌演示数据。它默认以 `root` + **空密码** 连接；如果你的 root 有密码：

```bash
# Windows
set MYSQL_ADMIN_USER=root
set MYSQL_ADMIN_PASSWORD=你的root密码
.venv\Scripts\python.exe scripts\init_db.py

# macOS / Linux
MYSQL_ADMIN_USER=root MYSQL_ADMIN_PASSWORD=你的root密码 python scripts/init_db.py
```

常用参数：`--no-seed` 只建表不灌数据；`--drop` 先删表再重建（**危险**）。

<details>
<summary>Windows 免安装版（zip）关键步骤</summary>

```ini
; my.ini
[mysqld]
basedir=D:/mysql8
datadir=D:/mysql8/data
port=3306
character-set-server=utf8mb4
default_authentication_plugin=mysql_native_password
```

```bash
mysqld --defaults-file=D:/mysql8/my.ini --initialize-insecure   # 首次初始化，root 空密码
mysqld --defaults-file=D:/mysql8/my.ini --console               # 启动（cwd 需为 D:/mysql8）
```

Windows 下配置里的路径建议用**正斜杠**。
</details>

### Redis（可选）

仓库**不含** Redis 二进制（`_tools/redis/` 已被 gitignore 排除）。任选一种：

- 下载 Windows 版 Redis（如 [tporadowski/redis](https://github.com/tporadowski/redis/releases)），解压到 `_tools/redis/`，确保 `redis-server.exe` 位于该目录下（`start-all.bat` 默认按此路径查找）；
- 或使用 Docker / WSL / 已有安装，然后在 `local.env.bat` 里把 `REDIS` 指向它。

不装 Redis 也能跑：在 `.env` 里设 `REDIS_ENABLED=false`，或直接不启动——缓存层会自动降级为直连 MySQL，只是失去加速效果。

### Python 与 Node

Python 3.10+、Node 18+ 即可，无需特殊版本。

> **Windows + 智能应用控制（Smart App Control）用户必读**
>
> SAC 会拦截**未签名**的解释器。请使用 [python.org](https://www.python.org/downloads/) 官方安装包（带 Python Software Foundation 签名）创建虚拟环境；用 `uv` 或 `python-build-standalone` 下载的解释器没有 Authenticode 签名，可能被系统静默拦截，表现为服务「时好时坏」或 `os error 4551`。

## 配置说明

`blog-api/.env` 的关键项（完整清单见 `blog-api/.env.example`）：

| 变量 | 示例值 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `development` | 设为 `production` 会关闭 `/docs`，并强制校验密钥与 CORS |
| `DEBUG` | `true` | 模板中为 `true`，便于本地排查；生产环境请设 `false` |
| `MYSQL_HOST` / `MYSQL_PORT` | `127.0.0.1` / `3306` | 数据库连接 |
| `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | `bluemoon` / `bluemoon123` / `bluemoon` | 业务账号，由 `init_db.py` 自动创建 |
| `REDIS_ENABLED` | `true` | 置 `false` 可完全关闭缓存 |
| `SECRET_KEY` | （空） | JWT 签名密钥，**生产环境必须设置** |
| `TRUSTED_PROXIES` | （空） | 反向代理白名单，只有来源 IP 在此列表内才采信 `X-Forwarded-For`。**直连部署务必留空**，否则可伪造 XFF 绕过按 IP 的限流 |
| `LOGIN_MAX_FAILURES` | `5` | 同一「用户名 + IP」在窗口内的失败上限，超限返回 429 |
| `IMAGE_MAX_PIXELS` | `50000000` | 图片像素上限，防解压炸弹 |
| `CORS_ORIGINS` | `http://localhost:5173,...` | 允许的前端来源 |
| `UPLOAD_DIR` | `static/uploads` | 上传根目录（相对 `blog-api/`） |

前端配置在 `blog-web/.env.development`（`VITE_API_BASE=/api/v1`），一般无需改动。

## 项目结构

```
bluemoon/
├── blog-api/                  # 后端服务
│   ├── app/
│   │   ├── api/v1/            # 路由：auth / posts / categories / profile / stats / upload / seo / health
│   │   ├── core/              # 配置、安全、异常、响应封装
│   │   ├── db/                # 数据库连接与基类
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑层（缓存 / 图片 / 头像 / SEO / 统计）
│   │   ├── utils/             # 工具函数
│   │   └── main.py            # FastAPI 应用入口
│   ├── scripts/init_db.py     # 数据库初始化（建库 / 建用户 / 建表 / 演示数据）
│   ├── scripts/               # 衍生图回填、校验脚本
│   ├── static/                # 上传文件根目录（运行时产物，仅提交 .gitkeep 占位）
│   ├── tests/                 # 测试（注意下方「开发约定」中的警告）
│   ├── requirements.txt
│   ├── run.py                 # 后端启动入口
│   └── .env.example           # 环境变量模板
├── blog-web/                  # 前端应用
│   ├── src/
│   │   ├── components/        # 通用组件（ThemeSwitch 拉灯模式、图库、Markdown 渲染等）
│   │   ├── views/             # 页面（含 admin/ 后台）
│   │   ├── composables/       # 组合式函数（useTheme、useSeo、useReadingTimer）
│   │   ├── stores/            # Pinia 状态
│   │   ├── router/            # 路由 + 鉴权守卫
│   │   ├── api/               # 接口封装
│   │   ├── utils/             # 富文本清洗等
│   │   └── styles/            # 全局样式与主题变量
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docker/                    # 容器化
│   ├── api.Dockerfile         # 多阶段：构建前端产物 + 运行后端
│   └── entrypoint.sh          # 等 MySQL → 幂等初始化库 → 启动 uvicorn
├── docker-compose.yml         # MySQL + Redis + 应用 编排（网络/卷/依赖顺序）
├── .dockerignore              # 构建上下文排除规则（含 .env，防密码进镜像）
├── .env.docker.example        # Docker 部署变量模板（复制为根目录 .env）
├── scripts/                   # 启动器与运维脚本
│   ├── run-backend.bat        # 后端启动器（由 start-all.bat 调用）
│   ├── run-frontend.bat       # 前端启动器
│   ├── docker-up.bat / .sh    # 一键容器化启动
│   ├── docker-down.bat / .sh  # 一键下线（保留数据卷）
│   ├── gen_docker_env.py      # 生成含随机密钥的 .env
│   └── verify_*.py            # 数据布局 / 头像 / 兼容性自检脚本
├── docs/                      # 设计与审查文档
├── _tools/                    # 本地工具目录（Redis 发行版放这里，不入库）
├── start-all.bat              # 一键启动（MySQL + Redis + 后端 + 前端）
├── stop-all.bat               # 一键停止
├── local.env.bat.example      # 本机路径覆盖模板
├── .gitattributes             # 换行策略（.bat 强制 CRLF）
└── .gitignore
```

### 图片存储布局

上传文件按**日期优先**归档，`{scope}` 当前为 `post`（随文章生命周期，可随文清理）：

```
blog-api/static/
├── {YYYY}/{MM}/{DD}/uploads/post/   # 文章配图（含 @400 / @1024 衍生图）
├── gallery/                         # 图库长期资产（不参与随文清理）
└── avatar/                          # 头像长期资产（换头像保留历史，可回滚）
```

`static/` 整体不入库——它是运行时产物，各自环境生成。只有 `.gitkeep` 占位文件被提交，确保 clone 后目录存在。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端框架 | FastAPI 0.115 · Uvicorn · Pydantic v2 |
| 数据库 | MySQL 8 · SQLAlchemy 2.0 · PyMySQL |
| 缓存 | Redis 5+ |
| 鉴权 | JWT (python-jose) · passlib + bcrypt |
| 图片处理 | Pillow（真实格式校验 + 衍生图生成） |
| 前端框架 | Vue 3.5 · Vue Router 4 · Pinia 2 |
| 构建工具 | Vite 5 |
| UI 组件 | Element Plus 2.8（按需引入）· @element-plus/icons-vue |
| 工具库 | axios · dayjs · markdown-it · highlight.js · nprogress |

## 主题说明

前端内置暗色 / 亮色双主题，由 `src/composables/useTheme.js` 统一管理：

- 主题状态持久化于 `localStorage('bm-theme')`
- `main.js` 在挂载前调用 `initTheme()` 防止首屏闪烁
- 事实源是 `html.dark` class，Element Plus 暗色变量自动跟随
- 所有自定义组件使用 CSS 变量令牌（`--bm-bg`、`--bm-card`、`--bm-text`、`--bm-border`、`--bm-primary` 等），明暗模式通用

## 开发约定

改代码前请留意这几条，都是踩过坑之后定下来的：

| 约定 | 原因 |
| --- | --- |
| `.bat` 必须保存为 **ANSI/GBK + CRLF** | UTF-8 会让 cmd 乱码或把命令拦腰截断；LF 换行会让 `goto` 标签与多行 `if` 块解析出错。`.gitattributes` 已强制 `.bat` 检出为 CRLF |
| 主题色一律用 `--bm-*` 变量，不硬编码颜色 | 否则暗色模式下会出现刺眼的白底/白条 |
| Element Plus 组件与样式按需引入 | 禁止 `import { ElMessage } from 'element-plus'`，会破坏 tree-shaking |
| 图片上传白名单**不含 `svg`** | `/static` 与站点同源托管，带脚本的 SVG 会成为存储型 XSS |
| 正文富文本渲染后需过 `utils/sanitizeHtml.js` | 保留既有的内嵌视频等能力，同时移除脚本与事件属性 |
| 图片引用检查走批量索引，不在循环里单张查询 | `content LIKE '%url%'` 是 TEXT 全表扫描 |
| 缓存只存 MySQL 基数，Redis 增量在读出后叠加一次 | 接口层重复叠加会导致阅读数翻倍 |

> **⚠️ 关于 `blog-api/tests/`**：`tests/test_smoke.py` 会写入**真实数据库**（包括修改 `profile.bio`）。在连着自己数据的开发库上跑之前请留意这一点，建议先备份或使用独立测试库。

## 日常开发流程（Git）

### 改完代码 → 提交 → 推送

```bash
git status                  # ?? 未跟踪 / M 已修改，先看清楚改了什么
git add -A                  # 全部暂存；只想提交部分文件就写具体路径
git commit -m "fix: 修正首页语录的随机逻辑"
git push origin main
```

推送前扫一眼暂存内容，确认没把不该提交的东西带进来：

```bash
git status --short
git ls-files blog-api/static/   # 只应该有 .gitkeep；出现图片说明忽略规则被改坏了
```

`.env`、`local.env.bat`、`.env.docker`、上传的图片、`node_modules/`、`.venv/`、`dist/` 都已在 `.gitignore` 里，正常不会误入。

推送后想确认远端真的收到了：

```bash
git log --oneline -1            # 本地最新 commit
git ls-remote origin            # 远端 refs/heads/main 的 SHA，两者应一致
```

### 代码改了，怎么让 Docker 生效

镜像里跑的是**构建产物**，改完代码必须重建容器：

```bash
docker compose up -d --build api   # 只重建应用容器（数据库/缓存不受影响）
docker compose logs -f api         # 确认起来了
```

本地非 Docker 开发不需要这步 —— Vite 与 uvicorn 都带热重载，存盘即生效。

### 在新机器 / WSL / 服务器上拿到代码

```bash
git clone https://github.com/MlaiByu/bluemoon.git
cd bluemoon
```

HTTPS 无需配置 SSH key；已配 key 的也可以用 `git clone git@github.com:MlaiByu/bluemoon.git`。

> 在 WSL / Linux 上开发时，Windows 专用的 `start-all.bat` 用不了。要么按上文走 Docker，要么手动起服务：`.venv/bin/python blog-api/run.py` 与 `cd blog-web && npm run dev`。

### 提交信息约定

| 前缀 | 用途 |
| --- | --- |
| `feat:` | 新功能 |
| `fix:` | 修 bug |
| `docs:` | 文档 |
| `chore:` | 杂项：依赖、脚本、配置 |
| `refactor:` | 重构 |

### 常见补救（建议都在推送前做）

| 场景 | 命令 |
| --- | --- |
| commit message 写错了 | `git commit --amend -m "新的说明"` |
| 撤销上一次 commit、但保留改动 | `git reset --soft HEAD~1` |
| 把文件移出暂存区 | `git restore --staged <文件>` |
| 丢弃某个文件的本地改动 | `git restore <文件>` ⚠️ 不可恢复 |
| 推之前再核对一遍改动 | `git diff` / `git diff --staged` |

> `reset --hard`、`push --force`、`clean -fd` 都会丢数据 —— 清空工作区或覆盖远端历史之前，先确认没有需要保留的东西。

## 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| 前端提示「服务器开小差了」 | 基本等同于后端 8000 没起来——先看后端窗口的报错 |
| 后端启动即退出，报找不到模块 | 依赖没装齐：`.venv\Scripts\python.exe -m pip install -r blog-api\requirements.txt` |
| 后端起不来，日志提示数据库连接失败 | 检查 MySQL 是否启动、`.env` 里的 `MYSQL_*` 是否正确、是否已跑过 `scripts/init_db.py` |
| 无法登录后台 | 确认已执行 `init_db.py`（它会创建 `admin / admin123`）；若改过密码用新密码 |
| 上传图片失败 | 确认 `blog-api/static/` 目录存在（仓库只提交了 `.gitkeep` 占位）；检查图片大小与扩展名是否在 `ALLOWED_IMAGE_EXT` 内 |
| 阅读数不动 | 阅读计数需要文章可见且停留满 5 秒才 +1，且同一 IP 在 5 分钟内只计一次 |
| `start-all.bat` 报找不到 MySQL / Redis | 复制 `local.env.bat.example` 为 `local.env.bat`，把 `MYSQL` / `REDIS` 指向本机实际路径 |
| 服务「时好时坏」或报 `os error 4551` | Windows Smart App Control 拦截了未签名的 Python 解释器，见上方说明 |
| 想彻底关掉缓存 | `.env` 里设 `REDIS_ENABLED=false` |
| `docker compose up` 报未设置 `SECRET_KEY` | 用 `scripts/docker-up.bat` 自动生成，或先 `cp .env.docker.example .env` 并填写必填项 |
| Docker 里改了代码不生效 | 镜像里跑的是构建产物，需重建：`docker compose up -d --build api` |
| 容器起来了但 8000 打不开 | `docker compose ps` 看 api 是否 healthy，`docker compose logs api` 看初始化进度（首次 1–2 分钟） |
| Docker 版阅读数不涨 | Docker Desktop 下所有访客共享网关 IP，5 分钟去重窗口会把它们合并计数，见「客户端真实 IP」 |

## 许可

个人项目，保留所有权利。

如需用于自己的博客，欢迎参考实现思路；大规模复制或商用请先联系作者。
