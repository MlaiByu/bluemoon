@echo off
REM ============================================================
REM  bluemoon 个人博客 - 一键停止（关闭 MySQL / Redis / 后端 / 前端）
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM ============================================================
echo 正在停止 bluemoon 服务...

REM MySQL / Redis 按进程名结束
taskkill /F /IM mysqld.exe >nul 2>&1
taskkill /F /IM redis-server.exe >nul 2>&1

REM 后端(8000) / 前端(5173) 按端口结束对应进程
for %%P in (8000 5173) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R ":%%P .*LISTENING"') do (
    taskkill /F /PID %%A >nul 2>&1
  )
)

echo 已停止。下次启动请运行 start-all.bat
pause
