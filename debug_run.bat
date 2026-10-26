@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Quick Expander (Debug Console)

echo ========================================================
echo        ⚡ Quick Expander 管理面板 (调试运行模式)
echo ========================================================

set "PY_EXE=python.exe"
where python.exe >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
        set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    )
)

"%PY_EXE%" main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序运行结束或发生异常，错误代码: %ERRORLEVEL%
    pause
)
