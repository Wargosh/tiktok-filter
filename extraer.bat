@echo off
REM Abre una consola visible y corre el extractor mostrando el avance en vivo.
REM Uso:  extraer.bat --liga D5      (o: extraer.bat --liga C5,C4,C3,D1)
cd /d "%~dp0"
title tiktok-filter %*
if exist "%~dp0tools\platform-tools\adb.exe" set "PATH=%~dp0tools\platform-tools;%PATH%"
set "PY=.venv\Scripts\python.exe"
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not exist "%PY%" (
  echo [X] No hay Python. Ejecuta primero instalar.bat
  pause
  exit /b 1
)
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
set TIKTOK_FILTER_CONSOLE=1
"%PY%" main.py run %*
echo.
echo Terminado. Puedes cerrar esta ventana.
pause