@echo off
chcp 65001 >nul
title 完美自我进化系统
color 0a
cls
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     完美自我进化系统 v3.0                  ║
echo  ║     无需API Key，开箱即用！               ║
echo  ╚═══════════════════════════════════════════╝
echo.
cd /d "%~dp0"

set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe

REM 启动进化系统（无需API Key）
echo [启动] 完美自我进化系统...
echo [信息] 运行间隔: 5分钟
echo [信息] 日志目录: logs\
echo.
echo 按 Ctrl+C 停止系统
echo.

"%PYTHON%" "%~dp0main.py"
pause