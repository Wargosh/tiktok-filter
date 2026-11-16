@echo off
REM Instalador portable de tiktok-filter. Funciona en cualquier PC con Windows:
REM copia la carpeta del proyecto donde quieras y haz doble clic aqui.
cd /d "%~dp0"
title tiktok-filter - instalacion
echo === tiktok-filter: instalacion ===
echo Carpeta: %CD%
echo.

REM 1) Python
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo [X] No encontre Python. Instala Python 3.10 o superior desde https://www.python.org/downloads/
  echo     y marca "Add python.exe to PATH". Luego vuelve a ejecutar este instalador.
  pause
  exit /b 1
)
%PY% --version

REM 2) Entorno virtual + dependencias
if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual .venv ...
  %PY% -m venv .venv || ( echo [X] No pude crear .venv & pause & exit /b 1 )
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || ( echo [X] Fallo pip install & pause & exit /b 1 )

REM 3) ADB (platform-tools): usa el del PATH o descarga uno dentro del proyecto
where adb >nul 2>nul
if errorlevel 1 (
  if not exist "tools\platform-tools\adb.exe" (
    echo Descargando Android platform-tools ...
    if not exist tools mkdir tools
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'tools\pt.zip'; Expand-Archive 'tools\pt.zip' -DestinationPath 'tools' -Force; Remove-Item 'tools\pt.zip'"
  )
  set "PATH=%CD%\tools\platform-tools;%PATH%"
)
where adb >nul 2>nul || ( echo [X] No pude conseguir adb. & pause & exit /b 1 )

REM 4) Configuracion
if not exist config.json copy config.example.json config.json >nul

echo.
echo === Instalado. Conecta el celular por USB y acepta "Permitir depuracion USB" ===
adb devices
echo Comprobando conexion con el celular...
".venv\Scripts\python.exe" main.py check
echo.
echo Para extraer:  extraer.bat --liga C5,C4,C3,D1
pause
