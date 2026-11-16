@echo off
REM Extractor de tiktok-filter con consola visible.
REM Doble clic: pregunta las ligas.  Desde consola:  extraer.bat --liga C5,C4,C3
cd /d "%~dp0"
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

set "ARGS=%*"
if not "%ARGS%"=="" goto correr

:preguntar
cls
echo ================================================
echo   tiktok-filter - extraer usuarios del ranking
echo ================================================
echo.
echo Ligas posibles: A1-A3, B1-B5, C1-C5, D1-D5
echo.
echo Escribe la liga o las ligas SEPARADAS SOLO POR COMAS, sin espacios.
echo   Una liga:     C5
echo   Varias:       C5,C4,C3
echo (Si escribes minusculas o espacios no pasa nada, se corrigen solos.)
echo (Enter sin escribir nada = usar el ranking que ya tengas abierto en el cel)
echo.
set "LIGAS="
set /p "LIGAS=Ligas: "
if not defined LIGAS (
  set "ARGS="
  goto correr
)
set "NORM="
for /f "usebackq delims=" %%N in (`call "%PY%" -m sam.ligas "%LIGAS%"`) do set "NORM=%%N"
if not defined NORM set "NORM=INVALIDO:"
if "%NORM:~0,9%"=="INVALIDO:" (
  echo.
  echo [X] No entendi: %NORM:~9%
  echo     Usa letra A-D y numero, separadas por comas. Ejemplo: C5,C4,D1
  pause
  goto preguntar
)
echo.
echo Ligas a buscar: %NORM%
set "ARGS=--liga %NORM%"
:correr
title tiktok-filter %ARGS%
echo.
echo Iniciando: %ARGS%
echo Conecta el celular por USB con TikTok abierto. No lo uses mientras extrae.
echo.
"%PY%" main.py run %ARGS%
echo.
echo Terminado. Los txt y Excel quedaron en la carpeta output.
if exist output start "" explorer output
pause