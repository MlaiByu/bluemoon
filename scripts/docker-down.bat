@echo off
REM ============================================================
REM  bluemoon 容器下线（Windows）
REM  停止并移除容器与网络，但保留数据卷与上传图片：
REM    - MySQL 数据卷   mysql_data
REM    - Redis 数据卷   redis_data
REM    - 上传的图片     blog-api\static\
REM  注意：本文件必须保存为 ANSI/GBK 编码 + CRLF 换行
REM ============================================================
setlocal

pushd "%~dp0.."

where docker >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 docker 命令。
    popd
    exit /b 1
)

docker compose down

echo.
echo 已停止并移除容器。以下内容均已保留：
echo   - MySQL 数据卷   mysql_data
echo   - Redis 数据卷   redis_data
echo   - 上传的图片     blog-api\static\
echo.
echo 如需连数据一起清除（不可恢复）：docker compose down -v
popd
pause
exit /b 0
