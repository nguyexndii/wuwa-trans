@echo off
:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    echo Yeu cau quyen Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
:admin
cd /d "%~dp0"
title Wuthering Waves Screen Translator
echo Dang khoi dong ung dung dich...
.venv\Scripts\python.exe main.py
pause
