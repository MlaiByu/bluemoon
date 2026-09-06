@echo off
REM ============================================================
REM  bluemoon 个人博客 - 一键启动（MySQL + Redis + 后端 + 前端）
REM  每个服务在独立窗口中运行，关闭对应窗口即可停止该服务
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM        （UTF-8 会导致 cmd 乱码 / 命令被拦腰截断）
REM ============================================================
set BASE=C:\Users\12607\Desktop\bluemoon
set VENV=%BASE%\.venv\Scripts
set MYSQL=D:\mysql8
set REDIS=%BASE%\_tools\redis
set NODEBIN=C:\Users\12607\.workbuddy\binaries\node\versions\22.22.2-2

set "PATH=%NODEBIN%;%PATH%"

echo ============================================================
echo   bluemoon 启动中...
echo   MySQL   : %MYSQL%  (port 3306)
echo   Redis   : %REDIS%  (port 6379)
echo   后端    : http://127.0.0.1:8000  (docs: /docs)
echo   前端    : http://127.0.0.1:5173
echo ============================================================
echo.

REM ---- MySQL（端口已占用则跳过，防止重复启动）----
netstat -ano | findstr /C:":3306 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [跳过] MySQL 已在运行
) else (
    start "bluemoon-MySQL" /D "%MYSQL%" bin\mysqld.exe --defaults-file=%MYSQL%\my.ini --console
    echo [启动] MySQL ...
)

REM ---- Redis ----
netstat -ano | findstr /C:":6379 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [跳过] Redis 已在运行
) else (
    start "bluemoon-Redis" "%REDIS%\redis-server.exe" --port 6379 --bind 127.0.0.1 --save "" --appendonly no
    echo [启动] Redis ...
)

REM ---- 后端 FastAPI ----
netstat -ano | findstr /C:":8000 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [跳过] 后端已在运行
) else (
    start "bluemoon-Backend" /D "%BASE%\blog-api" "%VENV%\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    echo [启动] 后端 uvicorn ...
)

REM ---- 前端 Vite ----
netstat -ano | findstr /C:":5173 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [跳过] 前端已在运行
) else (
    start "bluemoon-Frontend" /D "%BASE%\blog-web" cmd /c "npm run dev"
    echo [启动] 前端 vite ...
)

echo.
echo 全部服务已处理，稍等几秒后打开 http://127.0.0.1:5173
echo 提示：后端 Swagger 文档在 http://127.0.0.1:8000/docs
pause
