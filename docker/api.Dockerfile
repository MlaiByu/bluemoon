# syntax=docker/dockerfile:1
#
# bluemoon 应用镜像：前端构建 + 后端运行，单容器单入口
#
# 为什么前端不单独用 nginx 容器？
#   blog-api/app/main.py 的 SPA fallback 会读取前端 dist/index.html 并在
#   服务端注入文章级 SEO 元信息（微信/QQ 抓取分享卡片依赖它，抓取器不执行 JS）。
#   若把前端交给独立 nginx 托管，index.html 就不再经过后端，SEO 注入直接失效。
#   另外前端 axios 的 baseURL 是相对路径 /api/v1，与后端同源即可，无需反代。
#   → 所以正确做法是把构建产物交给后端托管，一个容器、一个入口。
#
# 构建上下文必须是「仓库根目录」（见 docker-compose.yml 的 build.context），
# 因为镜像里同时需要 blog-api/ 与 blog-web/。
#
# 构建：docker build -f docker/api.Dockerfile -t bluemoon-api .
# 或直接：docker compose up -d --build

# ============================================================
#  stage 1 — 构建前端静态产物
# ============================================================
FROM node:22-alpine AS web-build

WORKDIR /build

# 先只拷依赖清单：改业务代码不会触发 npm ci 重跑，充分利用层缓存
COPY blog-web/package.json blog-web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY blog-web/ ./

# 说明：vite build 的模式是 production，不会加载 .env.development，
# 因此 VITE_API_BASE 为 undefined，代码会回落到相对路径 /api/v1
# （见 blog-web/src/api/request.js 的 `import.meta.env.VITE_API_BASE || '/api/v1'`）。
# 这正是我们想要的：产物与部署域名解耦，同源即可用。
RUN npm run build


# ============================================================
#  stage 2 — 后端运行时（同时托管 stage 1 的前端产物）
# ============================================================
FROM python:3.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 依赖单独成层：日常改代码不会重新安装依赖
COPY blog-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 后端源码（.venv / .env / static 的真实图片等已由 .dockerignore 排除）
COPY blog-api/ ./

# 前端产物 → 对应 config.py 的 FRONTEND_DIST（compose 里设为 /app/frontend-dist）
COPY --from=web-build /build/dist ./frontend-dist

# 上传目录：运行时由 compose 用卷挂载覆盖，这里先建好占位
RUN mkdir -p /app/static

# 入口脚本：等待 MySQL → 幂等初始化数据库 → 启动 uvicorn
COPY docker/entrypoint.sh /app/docker-entrypoint.sh
# git 在 Windows 上不保留可执行位，必须显式 chmod，否则 ENTRYPOINT 无法执行
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

# 容器内自检：/health 属于 v1 路由聚合，实际路径是 /api/v1/health
# （api_router = APIRouter(prefix=API_V1_PREFIX)）
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
