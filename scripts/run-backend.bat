@echo off
REM ============================================================
REM  后端启动器（由 start-all.bat 调用，一般不需要直接双击）
REM  路径按本脚本所在目录自动推导（scripts\ 的上一级 = 项目根）
REM  uvicorn 输出直接显示在本窗口（不再重定向进日志）：
REM    - 看到 "Uvicorn running on http://127.0.0.1:8000" 即启动成功；
REM    - 若报错，错误信息会停留在本窗口（按任意键关闭）。
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM ============================================================
setlocal

pushd "%~dp0.."
set "BASE=%CD%"
popd

if exist "%BASE%\local.env.bat" call "%BASE%\local.env.bat"
set "PY=%BASE%\.venv\Scripts\python.exe"

cd /d "%BASE%\blog-api"

echo [%date% %time%] 启动后端：uvicorn app.main:app --host 127.0.0.1 --port 8000
echo ------------------------------------------------------------
echo  项目根  %BASE%
echo  解释器  %PY%
echo  就绪后可访问  http://127.0.0.1:8000/docs
echo  本窗口将实时滚动后端日志（正常现象，请勿关闭，关闭即停止后端）
echo ------------------------------------------------------------
"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo ============================================================
echo  [后端已退出] 退出码 %errorlevel%
echo  常见原因：上方报错 / 8000 端口被占用 / MySQL 未就绪 / 依赖缺失
echo ============================================================
pause
