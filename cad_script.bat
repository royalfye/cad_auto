@echo off
title Cadastro Automatico

cd /d "%~dp0"

call venv\Scripts\activate.bat

echo Iniciando sistema...
echo.

py src\interface\app.py

echo.
echo Programa encerrado.
pause