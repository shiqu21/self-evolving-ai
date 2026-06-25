@echo off
REM WorkBuddy 自我进化系统 - 测试与验证入口
REM
REM 用法:
REM   test_all.bat      运行所有测试
REM   test_pipeline.bat 单独测试质量管道
REM   test_evolution.bat 单独测试进化模块
REM   test_reflect.bat  单独测试反思模块

echo ============================================
echo   WorkBuddy 自我进化系统 - 测试入口
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [1/4] 测试质量管道...
python run.py --pipeline
echo.

echo [2/4] 测试提示词进化...
python run.py --evolve-prompt
echo.

echo [3/4] 测试自我反思...
python run.py --reflect
echo.

echo [4/4] 查看系统状态...
python run.py --status
echo.

echo ============================================
echo   测试完成
echo ============================================
pause