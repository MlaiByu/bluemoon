#!/usr/bin/env sh
# ============================================================
#  bluemoon 容器下线
#  停止并移除容器与网络，但保留：
#    - 数据卷 mysql_data / redis_data（数据库与缓存）
#    - blog-api/static/（上传的图片，宿主机目录）
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "[错误] 未找到 docker 命令。"
    exit 1
fi

docker compose down

echo ""
echo "已停止并移除容器。以下内容均已保留："
echo "  - MySQL 数据卷   mysql_data"
echo "  - Redis 数据卷   redis_data"
echo "  - 上传的图片     blog-api/static/"
echo ""
echo "如需连数据一起清除（不可恢复）：docker compose down -v"
