@echo off
REM Instalador portable de tiktok-filter. Funciona en cualquier PC con Windows:
REM copia la carpeta del proyecto donde quieras y haz doble clic aqui.
cd /d "%~dp0"
title tiktok-filter - instalacion
echo === tiktok-filter: instalacion ===
echo Carpeta: %CD%
echo.

REM 0) Paquete portable: ya trae Python, librerias y ADB. No necesita internet.
if exist "python\python.exe" (
  echo Paquete portable detectado: Python, librerias y ADB incluidos.
  set "PATH=%CD%\tools\platform-tools;%PATH%"
  if not exist config.json copy config.example.json config.json >nul
  goto probar
)
REM 1) Python real (el alias de la Microsoft Store no sirve: se prueba ejecutandolo)
set "PY="
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY ( python -c "import sys" >nul 2>nul && set "PY=python" )

if defined PY goto conpython
REM Sin Python: descargo uno portable dentro del proyecto (carpeta python\)
echo No hay Python instalado. Descargo Python portable en la carpeta python\ ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $v='3.13.9'; Invoke-WebRequest \"https://www.python.org/ftp/python/$v/python-$v-embed-amd64.zip\" -OutFile py.zip; Expand-Archive py.zip -DestinationPath python -Force; Remove-Item py.zip; $p=Get-ChildItem python -Filter 'python*._pth' | Select -First 1; $l=(Get-Content $p.FullName) -replace '^#\s*import site','import site'; $l+='Lib\site-packages'; $l+='..'; Set-Content $p.FullName $l; Invoke-WebRequest https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py"
if not exist "python\python.exe" ( echo [X] No pude descargar Python. Revisa internet o usa el paquete tiktok-filter-portable.zip & pause & exit /b 1 )
"python\python.exe" get-pip.py --no-warn-script-location || ( echo [X] Fallo instalar pip & pause & exit /b 1 )
del get-pip.py
"python\python.exe" -m pip install --no-warn-script-location -r requirements.txt || ( echo [X] Fallo pip install & pause & exit /b 1 )
goto adb

:conpython
%PY% --version

REM 2) Entorno virtual + dependencias
if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual .venv ...
  %PY% -m venv .venv || ( echo [X] No pude crear .venv & pause & exit /b 1 )
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || ( echo [X] Fallo pip install & pause & exit /b 1 )

:adb
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
:probar
echo === Instalado. Conecta el celular por USB y acepta "Permitir depuracion USB" ===
adb devices
echo Comprobando conexion con el celular...
set "PY=.venv\Scripts\python.exe"
if exist "python\python.exe" set "PY=python\python.exe"
"%PY%" main.py check
echo.
echo Para extraer:  extraer.bat --liga C5,C4,C3,D1
pause
