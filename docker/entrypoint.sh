#!/bin/sh
# ============================================================
#  bluemoon api 容器入口
#    1) 等待 MySQL 可连接
#    2) 幂等初始化数据库（建库 / 建业务账号 / 建表 / 种子数据）
#    3) 交给 CMD 启动 uvicorn
#
#  设计取舍：初始化失败不阻塞容器启动。
#  原因是 fail-fast 会让 compose 反复重启容器（restart: unless-stopped），
#  用户只能看到滚动的重启日志而拿不到可操作的提示；而让容器起来后，
#  用户能 docker compose logs 看到原因、exec 进去手动重跑。
#  API 在库表缺失时本来就会返回明确的错误，不会静默给错数据。
# ============================================================
set -e

log() { echo "[entrypoint] $*"; }

log "bluemoon api 启动中..."

# ---------- 1. 等待 MySQL ----------
# compose 已用 depends_on: service_healthy 保证顺序，这里再等一遍是为了
# 覆盖「端口已监听但账号尚未完全就绪」的窗口，避免初始化脚本偶发失败。
wait_for_tcp() {
    host="$1"
    port="$2"
    name="$3"
    retries="${4:-60}"
    i=1
    while [ "$i" -le "$retries" ]; do
        if python -c "
import socket, sys
s = socket.socket()
s.settimeout(2)
try:
    s.connect(('${host}', ${port}))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"; then
            log "${name} 已就绪（${host}:${port}）"
            return 0
        fi
        if [ "$i" -eq 1 ] || [ $((i % 10)) -eq 0 ]; then
            log "等待 ${name}（${host}:${port}）... ${i}/${retries}"
        fi
        i=$((i + 1))
        sleep 2
    done
    log "警告：${name} 在预期时间内未就绪"
    return 1
}

if ! wait_for_tcp "${MYSQL_HOST:-mysql}" "${MYSQL_PORT:-3306}" MySQL 60; then
    log "警告：MySQL 不可用，跳过自动初始化，直接启动应用"
    log "       修复后可手动重跑：docker compose exec api python scripts/init_db.py"
    exec "$@"
fi

# Redis 不做等待：缓存层设计上允许不可用（自动降级直连 MySQL），
# 等它反而会拖慢启动。

# ---------- 2. 初始化数据库（脚本本身是幂等的）----------
if [ "${AUTO_INIT_DB:-true}" = "true" ]; then
    log "初始化数据库（建库 / 建业务账号 / 建表 / 种子数据）"
    if python scripts/init_db.py; then
        log "数据库初始化完成"
    else
        log "警告：数据库初始化失败，应用仍会启动（接口可能报错）"
        log "       手动重跑：docker compose exec api python scripts/init_db.py"
        log "       常见原因：MYSQL_ROOT_PASSWORD 与 mysql 服务不一致；或库尚未就绪"
    fi
else
    log "AUTO_INIT_DB=false，跳过数据库初始化"
fi

# ---------- 3. 启动应用 ----------
log "启动应用：$*"
exec "$@"
