#!/usr/bin/env sh
# ============================================================
#  bluemoon 一键容器化启动
#    1) 检查 Docker / Compose / 守护进程
#    2) 若无 .env 则自动生成（随机 SECRET_KEY 与数据库密码）
#    3) 构建镜像并启动全部服务
#    4) 等待健康检查通过，打印访问地址
# ============================================================
set -e

# 切到仓库根（本脚本位于 scripts/ 下）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BASE_DIR"

echo "==> 项目根目录：$BASE_DIR"

# ---------- 1. 环境检查 ----------
if ! command -v docker >/dev/null 2>&1; then
    echo "[错误] 未找到 docker 命令。"
    echo "       请先安装 Docker Desktop（Windows / macOS）或 Docker Engine（Linux）。"
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "[错误] 当前 docker 不支持 compose 子命令，需要 Docker Compose v2。"
    echo "       可用 docker compose version 自行确认。"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "[错误] 无法连接 Docker 守护进程，请确认 Docker Desktop / dockerd 已启动。"
    exit 1
fi

# ---------- 2. 生成部署配置 ----------
echo "==> 检查部署配置 .env"
if [ -f .env ]; then
    echo "    已存在，沿用现有配置"
else
    PY=""
    if command -v python3 >/dev/null 2>&1; then
        PY=python3
    elif command -v python >/dev/null 2>&1; then
        PY=python
    fi
    if [ -z "$PY" ]; then
        echo "[错误] 需要 python 生成随机密钥。"
        echo "       请手动执行：cp .env.docker.example .env，填写 SECRET_KEY 与数据库密码后再运行本脚本。"
        exit 1
    fi
    "$PY" scripts/gen_docker_env.py
fi

# ---------- 3. 构建并启动 ----------
echo "==> 构建镜像并启动容器（首次构建需要几分钟）"
docker compose up -d --build

# ---------- 4. 等待就绪 ----------
echo "==> 等待应用健康检查通过"
i=1
READY=0
while [ "$i" -le 40 ]; do
    STATUS="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' bluemoon-api 2>/dev/null || echo starting)"
    if [ "$STATUS" = "healthy" ]; then
        READY=1
        echo "    应用已就绪"
        break
    fi
    i=$((i + 1))
    sleep 3
done

if [ "$READY" != "1" ]; then
    echo "    提示：健康检查尚未通过，可能是首次初始化数据库较慢。"
    echo "          可用 docker compose logs -f api 查看进度。"
fi

HOST_PORT="$(docker compose port api 8000 2>/dev/null | head -1 | sed 's/.*://')"
HOST_PORT="${HOST_PORT:-8000}"

echo ""
echo "==================== 容器状态 ===================="
docker compose ps
echo "=================================================="
echo ""
echo "  访问地址   http://localhost:${HOST_PORT}"
echo "  后台入口   http://localhost:${HOST_PORT}/admin/login"
echo "             默认账号 admin / admin123，请尽快修改密码"
echo "  查看日志   docker compose logs -f api"
echo "  停止服务   ./scripts/docker-down.sh"
echo ""
