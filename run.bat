@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Quick Expander

echo ========================================================
echo        ⚡ Quick Expander 全局文本自动补全神器
echo ========================================================
echo 正在启动/唤出管理面板...

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序退出，返回代码: %ERRORLEVEL%
    pause
)
