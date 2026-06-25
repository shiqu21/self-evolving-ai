@echo off
REM WorkBuddy 进化服务管理脚本
REM
REM 功能:
REM   start        启动进化服务
REM   stop         停止进化服务
REM   restart      重启服务
REM   status       查看服务状态
REM   test         运行测试
REM   once         运行单次循环
REM
if "%1"=="" goto help
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="test" goto test
if "%1"=="once" goto once

:help
echo.
echo   用法:
echo     service.bat start      启动进化服务
echo     service.bat stop       停止进化服务
echo     service.bat restart    重启服务
echo     service.bat status     查看服务状态
echo     service.bat test       运行测试
echo     service.bat once       运行单次循环
echo.
goto :eof

:start
echo 启动进化服务...
cd /d "%~dp0"
start /B python main.py --interval 5
echo [成功] 服务已启动
goto :eof

:stop
echo 停止进化服务...
taskkill /F /IM python.exe 2>nul
echo [成功] 服务已停止
goto :eof

:restart
echo 重启进化服务...
call :stop
timeout /t 2 >nul
call :start
goto :eof

:status
echo 查看服务状态...
python run.py --status
goto :eof

:test
echo 运行测试...
call test_all..bat
goto :eof

:once
echo 运行单次循环...
python run.py --once
goto :eof