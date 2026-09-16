@echo off
REM ============================================================
REM  前端启动器（由 start-all.bat 调用，一般不需要直接双击）
REM  路径按本脚本所在目录自动推导（scripts\ 的上一级 = 项目根）
REM  Vite 输出直接显示在本窗口（不再重定向进日志）：
REM    - 窗口滚动显示 VITE ready 即为启动成功；
REM    - 若报错，错误信息会停留在本窗口（按任意键关闭）。
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM ============================================================
setlocal

pushd "%~dp0.."
set "BASE=%CD%"
popd

if exist "%BASE%\local.env.bat" call "%BASE%\local.env.bat"
if defined NODEBIN set "PATH=%NODEBIN%;%PATH%"

cd /d "%BASE%\blog-web"

echo [%date% %time%] 启动前端：npm run dev
echo ------------------------------------------------------------
echo  项目根  %BASE%
echo  就绪后可访问  http://127.0.0.1:5173
echo  本窗口将实时滚动 Vite 日志（正常现象，请勿关闭，关闭即停止前端）
echo ------------------------------------------------------------
call npm.cmd run dev

echo.
echo ============================================================
echo  [前端已退出] 退出码 %errorlevel%
echo  常见原因：上方报错 / 5173 端口被占用 / node_modules 缺失
echo ============================================================
pause
