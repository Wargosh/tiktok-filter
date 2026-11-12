@echo off
REM Abre una consola visible y corre el extractor mostrando el avance en vivo.
REM Uso:  extraer.bat --liga D5      (o: extraer.bat 50 --liga C5)
cd /d "%~dp0"
title SAM extractor %*
set "PATH=%PATH%;D:\USUARIO\Nueva carpeta - copia\platform-tools"
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
.venv\Scripts\python.exe main.py run %*
echo.
echo Terminado. Puedes cerrar esta ventana.
pause
