# Sin QuickEdit: un clic en la ventana no congela el seguimiento
try { Add-Type -Name K -Namespace W -MemberDefinition '[DllImport("kernel32.dll")] public static extern System.IntPtr GetStdHandle(int h); [DllImport("kernel32.dll")] public static extern bool GetConsoleMode(System.IntPtr h, out uint m); [DllImport("kernel32.dll")] public static extern bool SetConsoleMode(System.IntPtr h, uint m);'; $hh=[W.K]::GetStdHandle(-10); $mm=0; if ([W.K]::GetConsoleMode($hh,[ref]$mm)) { [void][W.K]::SetConsoleMode($hh, ($mm -band (-bnot 0x40)) -bor 0x80) } } catch {}
$host.UI.RawUI.WindowTitle = "tiktok-filter - seguimiento"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Set-Location (Join-Path $PSScriptRoot "logs")
$PID | Set-Content .watch.pid
$cur = $null; $pos = 0
while ($true) {
  $f = Get-ChildItem *.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($f -and $f.FullName -ne $cur) { $cur = $f.FullName; $pos = 0; Write-Host "`n===== $($f.Name) =====" -ForegroundColor Cyan }
  if ($cur) {
    $lines = Get-Content $cur -Encoding UTF8
    if ($lines.Count -gt $pos) { $lines[$pos..($lines.Count-1)] | ForEach-Object { Write-Host $_ }; $pos = $lines.Count }
  }
  Start-Sleep -Seconds 2
}
