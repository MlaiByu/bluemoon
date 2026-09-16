@echo off
REM ============================================================
REM  bluemoon 一键容器化启动（Windows）
REM    1) 检查 Docker / Compose / 守护进程
REM    2) 若无 .env 则自动生成（随机 SECRET_KEY 与数据库密码）
REM    3) 构建镜像并启动全部服务
REM    4) 等待健康检查通过，打印访问地址
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM        （UTF-8 会导致 cmd 乱码 / 命令被拦腰截断）
REM ============================================================
setlocal EnableDelayedExpansion

REM 切到仓库根（本脚本位于 scripts\ 下）
pushd "%~dp0.."
set "BASE=%CD%"

echo ==^> 项目根目录：%BASE%

REM ---------------- 1. 环境检查 ----------------
where docker >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 docker 命令。
    echo        请先安装 Docker Desktop for Windows。
    goto :fail
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo [错误] 当前 docker 不支持 compose 子命令，需要 Docker Compose v2。
    echo        可用 docker compose version 自行确认。
    goto :fail
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] 无法连接 Docker 守护进程，请确认 Docker Desktop 已启动。
    goto :fail
)

REM ---------------- 2. 生成部署配置 ----------------
echo ==^> 检查部署配置 .env
if exist "%BASE%\.env" (
    echo     已存在，沿用现有配置
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [错误] 需要 python 生成随机密钥。
        echo        请手动执行：copy .env.docker.example .env
        echo        填好 SECRET_KEY 与数据库密码后再运行本脚本。
        goto :fail
    )
    python "%BASE%\scripts\gen_docker_env.py"
    if errorlevel 1 goto :fail
)

REM ---------------- 3. 构建并启动 ----------------
echo ==^> 构建镜像并启动容器（首次构建需要几分钟）
docker compose up -d --build
if errorlevel 1 goto :fail

REM ---------------- 4. 等待就绪 ----------------
echo ==^> 等待应用健康检查通过
set READY=0
for /L %%i in (1,1,40) do (
    if "!READY!"=="0" (
        for /f "usebackq delims=" %%S in (`docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" bluemoon-api 2^>nul`) do (
            if "%%S"=="healthy" set READY=1
        )
    )
    if "!READY!"=="1" goto :healthy
    ping -n 4 127.0.0.1 >nul 2>&1
)

:healthy
if "!READY!"=="1" (
    echo     应用已就绪
) else (
    echo     提示：健康检查尚未通过，可能是首次初始化数据库较慢。
    echo           可用 docker compose logs -f api 查看进度。
)

REM 取实际映射到宿主机的端口
set "HOST_PORT="
for /f "tokens=2 delims=:" %%P in ('docker compose port api 8000 2^>nul') do set "HOST_PORT=%%P"
if not defined HOST_PORT set "HOST_PORT=8000"

echo.
echo ==================== 容器状态 ====================
docker compose ps
echo ==================================================
echo.
echo   访问地址   http://localhost:%HOST_PORT%
echo   后台入口   http://localhost:%HOST_PORT%/admin/login
echo              默认账号 admin / admin123，请尽快修改密码
echo   查看日志   docker compose logs -f api
echo   停止服务   scripts\docker-down.bat
echo.
popd
pause
exit /b 0

:fail
echo.
echo ============================================================
echo   启动未完成，请先处理上面的错误。
echo ============================================================
popd
pause
exit /b 1
