@echo off
REM WorkBuddy 自我进化系统 - 启动脚本
REM
REM 功能:
REM   - 启动完整的自动进化服务
REM   - 支持后台运行
REM   - 日志记录

echo ============================================
echo   WorkBuddy 自我进化系统
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [信息] Python环境正常
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

echo [信息] 启动进化系统...
echo.

REM 启动进化服务
REM 使用 start 命令后台运行，/B 表示后台模式
REM 使用 run_never_sleep 防止CMD窗口假死

start /B python "%PROJECT_DIR%main.py" --interval 5

echo [成功] 进化系统已启动
echo.
echo 查看日志: logs\evolution_YYYY-MM-DD.log
echo 停止服务: 按 Ctrl+C
echo.
pause