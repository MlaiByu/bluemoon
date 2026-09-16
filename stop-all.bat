@echo off
REM ============================================================
REM  bluemoon 一键停止（前端 - 后端 - Redis - MySQL）
REM  路径按本脚本所在目录自动推导，克隆到任意位置都能用；
REM  本机特有路径请在 local.env.bat 中覆盖。
REM  设计要点：
REM    1) findstr 必须 /R /C:，否则参数里的空格被当作 OR 模式，
REM       会把全系统 LISTENING 行一并命中（旧版就是这个坑）。
REM    2) Redis / MySQL 不再 taskkill /F /IM，按端口取唯一 PID，
REM       避免误杀机器上其他同名实例。
REM    3) 跳过 PID 0/1/4 等无效目标。
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM ============================================================
setlocal EnableDelayedExpansion

REM ---------------- 路径推导 ----------------
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

REM 本机路径覆盖（可选，不入库）
if exist "%BASE%\local.env.bat" call "%BASE%\local.env.bat"

if not defined MYSQL set "MYSQL=D:\mysql8"
if not defined REDIS set "REDIS=%BASE%\_tools\redis"

echo 正在停止 bluemoon 服务...

REM ============================================================
REM  按端口结束后端(8000) / 前端(5173)
REM ============================================================
for %%P in (8000 5173) do (
    set "PORT_NO=%%P"
    set FOUND=0
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
        set "PID=%%A"
        if not "!PID!"=="" if not "!PID!"=="0" if not "!PID!"=="1" if not "!PID!"=="4" (
            echo   [停止] 端口 %%P 对应进程 !PID!
            taskkill /F /PID !PID! >nul 2>&1
            if errorlevel 1 echo          警告：taskkill 退出码 !errorlevel!
            set FOUND=1
        )
    )
    if "!FOUND!"=="0" echo   [跳过] 端口 %%P 未在监听
)

REM ============================================================
REM  Redis：先 redis-cli 优雅关闭，失败再按端口结束
REM ============================================================
echo.
echo Redis (6379)
if exist "%REDIS%\redis-cli.exe" (
    "%REDIS%\redis-cli.exe" -h 127.0.0.1 -p 6379 shutdown nosave >nul 2>&1
    if not errorlevel 1 (
        echo   [停止] Redis graceful shutdown OK
    ) else (
        echo   [警告] redis-cli shutdown 失败，改用按端口结束
        call :killByPort 6379
    )
) else (
    echo   [跳过] 未找到 redis-cli.exe，改用按端口结束
    call :killByPort 6379
)

REM ============================================================
REM  MySQL：先 mysqladmin 优雅关闭，失败再按端口结束
REM  不再用 taskkill /F /IM mysqld.exe，防止误杀其他 MySQL 实例
REM ============================================================
echo.
echo MySQL (3306)
if exist "%MYSQL%\bin\mysqladmin.exe" (
    "%MYSQL%\bin\mysqladmin.exe" -h 127.0.0.1 -P 3306 -u root shutdown <nul >nul 2>&1
    if not errorlevel 1 (
        echo   [停止] MySQL graceful shutdown OK
    ) else (
        echo   [警告] mysqladmin 关闭失败，改用按端口结束
        call :killByPort 3306
    )
) else (
    echo   [跳过] 未找到 mysqladmin.exe，改用按端口结束
    call :killByPort 3306
)

echo.
echo 已停止。下次启动请运行 start-all.bat
pause
exit /b 0

REM ============================================================
REM  子过程：按端口结束监听进程（带 PID 安全检查）
REM  调用：call :killByPort PORT
REM ============================================================
:killByPort
set "PORT_NO=%~1"
set FOUND=0
for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%PORT_NO% .*LISTENING"') do (
    set "PID=%%A"
    if not "!PID!"=="" if not "!PID!"=="0" if not "!PID!"=="1" if not "!PID!"=="4" (
        echo   [停止] 端口 %PORT_NO% 对应进程 !PID!
        taskkill /F /PID !PID! >nul 2>&1
        if errorlevel 1 echo          警告：taskkill 退出码 !errorlevel!
        set FOUND=1
    )
)
if "!FOUND!"=="0" echo   [跳过] 端口 %PORT_NO% 未在监听
set "PORT_NO="
set "PID="
set "FOUND="
exit /b 0
