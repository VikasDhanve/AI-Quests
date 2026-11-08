$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskUrl = 'http://127.0.0.1:4192/ai-quests/intl/en_us'
$listener = Get-NetTCPConnection -State Listen -LocalPort 4192 -ErrorAction SilentlyContinue
if ($listener) {
    $answer = Invoke-WebRequest -UseBasicParsing -Uri $taskUrl -TimeoutSec 5
    if ($answer.Content -notmatch '<title>AI Quests</title>') { throw 'Port 4192 belongs to another application.' }
} else {
    $node = (Get-Command node -ErrorAction Stop).Source
    $process = Start-Process -FilePath $node -ArgumentList @('"' + (Join-Path $taskRoot 'scripts\server.mjs') + '"') -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput "$taskRoot\reports\server.log" -RedirectStandardError "$taskRoot\reports\server-error.log" -PassThru
    [IO.File]::WriteAllText("$taskRoot\reports\server.pid",[string]$process.Id)
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 300
        try { $answer = Invoke-WebRequest -UseBasicParsing -Uri $taskUrl -TimeoutSec 2; break } catch { if ($process.HasExited) { throw 'AI Quests server failed; see reports/server-error.log.' } }
    }
    if (-not $answer -or $answer.StatusCode -ne 200) { throw 'AI Quests did not become ready.' }
}
if (-not $env:AI_QUESTS_NO_BROWSER) { Start-Process $taskUrl }
Write-Output $taskUrl