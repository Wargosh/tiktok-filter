# Arma un paquete OFFLINE de tiktok-filter: trae Python portable, librerias y ADB.
# Ejecutar en esta PC (con internet la primera vez):  powershell -ExecutionPolicy Bypass -File empaquetar.ps1
# Resultado: dist\tiktok-filter-portable\  y  dist\tiktok-filter-portable.zip
$ErrorActionPreference = "Stop"
$root  = $PSScriptRoot
$dist  = Join-Path $root "dist"
$out   = Join-Path $dist "tiktok-filter-portable"
$cache = Join-Path $dist "cache"
New-Item -ItemType Directory -Force $cache | Out-Null
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null

# 1) Codigo del proyecto
foreach ($f in "main.py","seguir.ps1","extraer.bat","instalar.bat","config.example.json","requirements.txt","README.md") {
  Copy-Item (Join-Path $root $f) $out
}
Copy-Item (Join-Path $root "sam") $out -Recurse
Get-ChildItem $out -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Copy-Item (Join-Path $root "config.example.json") (Join-Path $out "config.json")

# 2) Python portable (embeddable) de la misma version que el .venv
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
$ver = (& $venvPy -c "import platform;print(platform.python_version())").Trim()
$zip = Join-Path $cache "python-$ver-embed-amd64.zip"
if (-not (Test-Path $zip)) {
  Write-Host "Descargando Python $ver embeddable..."
  Invoke-WebRequest "https://www.python.org/ftp/python/$ver/python-$ver-embed-amd64.zip" -OutFile $zip
}
$py = Join-Path $out "python"
Expand-Archive $zip -DestinationPath $py -Force
$pth = Get-ChildItem $py -Filter "python*._pth" | Select-Object -First 1
$lines = Get-Content $pth.FullName | ForEach-Object { if ($_ -match '^#\s*import site') { 'import site' } else { $_ } }
$lines += 'Lib\site-packages'
$lines += '..'
Set-Content $pth.FullName $lines -Encoding ASCII

# 3) Librerias (copiadas del .venv, mismas versiones probadas)
$sp = Join-Path $py "Lib\site-packages"
New-Item -ItemType Directory -Force $sp | Out-Null
Get-ChildItem (Join-Path $root ".venv\Lib\site-packages") | Where-Object { $_.Name -notmatch '^(pip|pip-.*|__pycache__|_distutils_hack|distutils-precedence\.pth|setuptools.*)$' } |
  ForEach-Object { Copy-Item $_.FullName $sp -Recurse -Force }
Get-ChildItem $sp -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# 4) ADB (platform-tools): del PATH de esta PC o descargado
$adb = (Get-Command adb -ErrorAction SilentlyContinue).Source
$tools = Join-Path $out "tools"
New-Item -ItemType Directory -Force $tools | Out-Null
if ($adb) {
  Copy-Item (Split-Path $adb) (Join-Path $tools "platform-tools") -Recurse
} else {
  $ptz = Join-Path $cache "platform-tools.zip"
  if (-not (Test-Path $ptz)) { Invoke-WebRequest "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" -OutFile $ptz }
  Expand-Archive $ptz -DestinationPath $tools -Force
}

# 5) Prueba rapida del Python portable
& (Join-Path $py "python.exe") -c "import uiautomator2, openpyxl, sam.ranking; print('Python portable OK')"
if ($LASTEXITCODE -ne 0) { throw "El Python portable no pudo importar las librerias" }

# 6) Zip
$z = Join-Path $dist "tiktok-filter-portable.zip"
if (Test-Path $z) { Remove-Item $z -Force }
Compress-Archive -Path $out -DestinationPath $z
"{0}  ({1:N1} MB)" -f $z, ((Get-Item $z).Length/1MB)
