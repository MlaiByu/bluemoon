# BlueMoon 博客

> 一个安静写字的地方 —— 记录生活、技术与思考的个人博客。

基于 **FastAPI + Vue3 + MySQL + Redis** 构建的全栈个人博客系统，参考 [hexo-theme-butterfly](https://github.com/jerryc127/hexo-theme-butterfly) 视觉风格，采用 16px 圆角卡片质感与 `#667eea → #764ba2` 蓝紫渐变语言。

## 项目简介

BlueMoon 是一个前后端分离的个人博客系统，包含完整的后台管理与公开浏览能力。

- **后端 `blog-api/`**：基于 FastAPI 构建，提供 RESTful API
  - 文章 CRUD、分类管理、个人资料、站点统计
  - JWT 鉴权（登录 / Token 刷新）
  - Redis 缓存（文章详情、列表、统计三档 TTL）
  - 图片上传（扫描 `static/uploads` 目录，限制大小与扩展名）
  - 随机语录、随机背景图接口
- **前端 `blog-web/`**：基于 Vue3 + Vite + Element Plus
  - 首页：随机语录 + 随机背景图（每次刷新变化）
  - 品牌字标 `BlueMoonの博客`（保留「の」字）
  - 自研主题切换器「拉灯模式」：纸灯笼样式 + 竹纹 + 流苏拉绳 + 朱砂/暖橙配色
  - 暗色 / 亮色模式（CSS 变量驱动，首屏防闪烁）
  - Images 相册页（后台上传/删除 + 公开浏览）
  - Markdown 渲染 + highlight.js 代码高亮

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端框架 | FastAPI 0.115 · Uvicorn · Pydantic v2 |
| 数据库 | MySQL 8 · SQLAlchemy 2.0 · Alembic |
| 缓存 | Redis 5+ |
| 鉴权 | JWT (python-jose) · passlib + bcrypt |
| 前端框架 | Vue 3.5 · Vue Router 4 · Pinia 2 |
| 构建工具 | Vite 5 |
| UI 组件 | Element Plus 2.8 · @element-plus/icons-vue |
| 工具库 | axios · dayjs · markdown-it · highlight.js · nprogress |

## 目录结构

```
bluemoon/
├── blog-api/              # 后端服务
│   ├── app/
│   │   ├── api/v1/        # 路由：auth / posts / categories / profile / stats / upload / health
│   │   ├── core/          # 配置、安全、异常、响应封装
│   │   ├── db/            # 数据库连接与基类
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── services/      # 业务逻辑层
│   │   ├── utils/         # 工具函数
│   │   └── main.py        # FastAPI 应用入口
│   ├── scripts/init_db.py # 数据库初始化脚本
│   ├── static/uploads/    # 图片上传目录（不入库）
│   ├── tests/
│   ├── requirements.txt
│   ├── run.py             # 开发启动脚本
│   ├── .env.example       # 环境变量模板
│   └── .env               # 实际配置（不入库，需自行创建）
├── blog-web/              # 前端应用
│   ├── src/
│   │   ├── components/    # 通用组件（含 ThemeSwitch 主题切换器）
│   │   ├── views/         # 页面
│   │   ├── composables/   # 组合式函数（useTheme 等）
│   │   ├── stores/        # Pinia 状态
│   │   ├── router/        # 路由
│   │   ├── api/           # 接口封装
│   │   └── styles/        # 全局样式（含主题变量）
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── _tools/                # 本地工具（Redis 发行版等，不入库）
├── docs/                  # 文档与截图
├── start-all.bat          # 一键启动（MySQL + Redis + 后端 + 前端）
├── stop-all.bat           # 一键停止
└── .gitignore
```

## 环境要求

- **Python** 3.10+
- **Node.js** 18+（推荐 22.x）
- **MySQL** 8.0
- **Redis** 5.0+

## 安装与运行

### 1. 克隆仓库

```bash
git clone git@github.com:MlaiByu/bluemoon.git
cd bluemoon
```

### 2. 后端配置与启动

```bash
cd blog-api

# 创建虚拟环境并安装依赖
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# 配置环境变量（复制模板后按实际修改数据库 / Redis / 密钥）
cp .env.example .env
# Windows
copy .env.example .env

# 初始化数据库（首次运行）
python scripts/init_db.py

# 启动开发服务
python run.py
# 后端默认运行在 http://127.0.0.1:8000
# API 文档：http://127.0.0.1:8000/docs
```

> `.env` 中需正确配置 `MYSQL_*`、`REDIS_*`、`SECRET_KEY`。`SECRET_KEY` 务必修改为随机长字符串。

### 3. 前端配置与启动

```bash
cd blog-web

# 安装依赖
npm install
# 或使用 pnpm / yarn

# 启动开发服务
npm run dev
# 前端默认运行在 http://127.0.0.1:5173
```

前端开发环境通过 Vite 代理将 `/api` 转发至后端 `http://127.0.0.1:8000`，无需额外配置跨域。

### 4. 一键启动（Windows）

项目根目录提供 `start-all.bat` / `stop-all.bat`，可一键拉起 MySQL、Redis、后端、前端四个服务。使用前需按脚本内的路径变量（`MYSQL`、`REDIS`、`VENV`、`NODEBIN`）调整为本机实际路径。

```bat
start-all.bat   :: 启动全部服务（各服务独立窗口）
stop-all.bat    :: 停止全部服务
```

### 5. 构建生产版本

```bash
cd blog-web
npm run build      # 产物输出至 dist/
npm run preview    # 本地预览构建结果（端口 4173）
```

## 主题说明

前端内置暗色 / 亮色双主题，由 `src/composables/useTheme.js` 统一管理：

- 主题状态持久化于 `localStorage('bm-theme')`
- `main.js` 在挂载前调用 `initTheme()` 防止首屏闪烁
- 所有自定义组件使用 CSS 变量令牌（`--bm-card`、`--bm-bg`、`--bm-text`、`--bm-border`、`--bm-primary` 等），明暗模式通用
- Element Plus 暗色变量自动跟随 `html.dark` class

## 许可

个人项目，保留所有权利。
