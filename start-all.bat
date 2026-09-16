@echo off
REM ============================================================
REM  bluemoon 一键启动（MySQL - Redis - 后端 - 前端）
REM  路径按本脚本所在目录自动推导，克隆到任意位置都能用；
REM  本机特有路径（MySQL / Node / Redis）请复制 local.env.bat.example
REM  为 local.env.bat 后填写，该文件不入库。
REM  每个服务在独立窗口中运行，关闭对应窗口即可停止该服务
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM        （UTF-8 会导致 cmd 乱码 / 命令被拦腰截断）
REM ============================================================
setlocal EnableDelayedExpansion

REM ---------------- 路径推导 ----------------
REM %~dp0 = 本脚本所在目录，末尾自带反斜杠，需要去掉
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

REM 本机路径覆盖（可选，不入库）
if exist "%BASE%\local.env.bat" call "%BASE%\local.env.bat"

if not defined MYSQL set "MYSQL=D:\mysql8"
if not defined REDIS set "REDIS=%BASE%\_tools\redis"
if defined NODEBIN set "PATH=%NODEBIN%;%PATH%"

set "VENV=%BASE%\.venv\Scripts"
set "PY=%VENV%\python.exe"

REM 延时 1 秒：不用 timeout.exe——(1) Git/usr/bin 下有同名 GNU timeout.exe 会抢先，
REM 导致 "/t" 报 invalid time interval；(2) Windows 版要求 stdin 为真实控制台，
REM stdin 被重定向时报"不支持输入重新定向"并立即退出，等待循环会退化成瞬时轮询。
REM ping -n 2 回环约延时 1 秒，且不依赖 stdin，任何环境都可用。
set "SLEEP1=ping -n 2 127.0.0.1"

echo ============================================================
echo   bluemoon 启动中（带就绪自检）
echo   项目根  : %BASE%
echo   MySQL   : %MYSQL%  (port 3306)
echo   Redis   : %REDIS%  (port 6379)
echo   后端    : http://127.0.0.1:8000  (docs: /docs)
echo   前端    : http://127.0.0.1:5173
echo ============================================================
echo.

REM ---------------- 环境自检 ----------------
echo [0/4] 环境自检...
if not exist "%PY%" (
    echo   [错误] 找不到 Python 虚拟环境：%PY%
    echo   请先在项目根目录创建虚拟环境并安装依赖：
    echo       python -m venv .venv
    echo       .venv\Scripts\python.exe -m pip install -r blog-api\requirements.txt
    goto :fail
)
if not exist "%MYSQL%\bin\mysqld.exe" (
    echo   [错误] 找不到 MySQL：%MYSQL%\bin\mysqld.exe
    echo   请在 local.env.bat 中把 MYSQL 指向本机 MySQL 8 目录（见 local.env.bat.example）
    goto :fail
)
if not exist "%MYSQL%\my.ini" (
    echo   [错误] 找不到 MySQL 配置：%MYSQL%\my.ini
    goto :fail
)
if not exist "%REDIS%\redis-server.exe" (
    echo   [错误] 找不到 Redis：%REDIS%\redis-server.exe
    echo   仓库不含 Redis 二进制，请下载 Windows 版 Redis 解压到：
    echo       %BASE%\_tools\redis\
    echo   或在 local.env.bat 中把 REDIS 指向已有安装目录
    goto :fail
)
if not exist "%BASE%\blog-api\app\main.py" (
    echo   [错误] 找不到后端入口：%BASE%\blog-api\app\main.py
    goto :fail
)
if not exist "%BASE%\blog-web\package.json" (
    echo   [错误] 找不到前端工程：%BASE%\blog-web\package.json
    goto :fail
)
if not exist "%BASE%\blog-web\node_modules" (
    echo   [错误] 前端依赖未安装，请先执行：cd /d %BASE%\blog-web ^&^& npm install
    goto :fail
)
where npm.cmd >nul 2>&1
if errorlevel 1 (
    echo   [错误] 未找到 npm，请安装 Node.js 18+ 并加入 PATH，
    echo          或在 local.env.bat 中设置 NODEBIN 指向 Node 安装目录
    goto :fail
)
echo   环境自检通过

REM ---------------- MySQL ----------------
echo [1/4] MySQL (3306)...
call :portReady 3306
if "!READY!"=="1" (
    echo   已在运行
) else (
    start "bluemoon-MySQL" /D "%MYSQL%" bin\mysqld.exe --defaults-file=%MYSQL%\my.ini --console
    call :waitPort 3306 120
    if "!READY!"=="1" (
        echo   已启动
    ) else (
        echo   [错误] MySQL 在 120 秒内未监听 3306
        echo   请查看 bluemoon-MySQL 窗口，或手动执行：
        echo   cd /d %MYSQL%\bin ^&^& mysqld.exe --defaults-file=%MYSQL%\my.ini --console
        goto :fail
    )
)

REM ---------------- Redis ----------------
echo [2/4] Redis (6379)...
call :portReady 6379
if "!READY!"=="1" (
    echo   已在运行
) else (
    start "bluemoon-Redis" "%REDIS%\redis-server.exe" --port 6379 --bind 127.0.0.1 --save "" --appendonly no
    call :waitPort 6379 30
    if "!READY!"=="1" (
        echo   已启动
    ) else (
        echo   [错误] Redis 在 30 秒内未监听 6379
        goto :fail
    )
)

REM ---------------- 后端 ----------------
echo [3/4] 后端 FastAPI (8000)...
call :portReady 8000
if "!READY!"=="1" (
    echo   已在运行
) else (
    start "bluemoon-Backend" "%BASE%\scripts\run-backend.bat"
    call :waitPort 8000 60
    if "!READY!"=="1" (
        echo   已启动
    ) else (
        echo   [错误] 后端在 60 秒内未监听 8000
        echo   请查看 bluemoon-Backend 窗口中的报错信息
        goto :fail
    )
)

REM ---------------- 前端 ----------------
echo [4/4] 前端 Vite (5173)...
call :portReady 5173
if "!READY!"=="1" (
    echo   已在运行
) else (
    start "bluemoon-Frontend" "%BASE%\scripts\run-frontend.bat"
    call :waitPort 5173 90
    if "!READY!"=="1" (
        echo   已启动
    ) else (
        echo   [错误] 前端在 90 秒内未监听 5173
        echo   请查看 bluemoon-Frontend 窗口中的报错信息
        goto :fail
    )
)

goto :end

REM ---------------- 子过程：端口是否已监听 ----------------
:portReady
set READY=0
netstat -ano | findstr /R /C:":%1 .*LISTENING" >nul
if not errorlevel 1 set READY=1
goto :eof

REM ---------------- 子过程：等待端口就绪 ----------------
:waitPort
set READY=0
for /L %%i in (1,1,%2) do (
    netstat -ano | findstr /R /C:":%1 .*LISTENING" >nul
    if not errorlevel 1 (
        set READY=1
        goto :eof
    )
    %SLEEP1% >nul 2>&1
)
goto :eof

REM ---------------- 失败出口 ----------------
:fail
echo.
echo ============================================================
echo   启动未完成，请先处理上面的错误，再重新运行本脚本。
echo   请查看各服务窗口中的报错信息（窗口会保留错误）
echo ============================================================
pause
exit /b 1

REM ---------------- 成功出口 ----------------
:end
echo.
echo ============================================================
echo   全部就绪：
echo     前端      http://127.0.0.1:5173
echo     后端      http://127.0.0.1:8000
echo     接口文档  http://127.0.0.1:8000/docs
echo   后台登录  http://127.0.0.1:5173/admin/login
echo ============================================================
start "" http://127.0.0.1:5173
pause
exit /b 0
