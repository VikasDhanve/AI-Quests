$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$pidPath = Join-Path $taskRoot 'reports\server.pid'
if (-not (Test-Path -LiteralPath $pidPath)) { Write-Output 'AI Quests is not running.'; exit 0 }
$taskProcessId = [int]([IO.File]::ReadAllText($pidPath))
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $taskProcessId"
if (-not $process) { Write-Output 'AI Quests is already stopped.'; exit 0 }
$expected = Join-Path $taskRoot 'scripts\server.mjs'
if ($process.Name -ne 'node.exe' -or $process.CommandLine.IndexOf($expected,[StringComparison]::OrdinalIgnoreCase) -lt 0) { throw 'Process ownership check failed. No process was stopped.' }
Stop-Process -Id $taskProcessId
Write-Output 'AI Quests stopped.'