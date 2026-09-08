$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$output = Join-Path $root 'data\network-capture'
New-Item -ItemType Directory -Path $output -Force | Out-Null
$started = $false
try {
  $state = & pktmon status 2>&1
  if ($LASTEXITCODE -ne 0) { throw 'Packet driver access denied.' }
  $state | Out-File (Join-Path $output 'initial-status.txt')
  if (($state -join ' ') -match '\brunning\b' -and ($state -join ' ') -notmatch 'not running') { throw 'An existing capture appears active; leaving it unchanged.' }
  & pktmon start --capture --comp nics --pkt-size 64 --file-name (Join-Path $output 'demo.etl') --file-size 64 --log-mode circular | Out-File (Join-Path $output 'capture.log')
  if ($LASTEXITCODE -ne 0) { throw 'Could not start packet capture.' }
  $started = $true
  Push-Location $root
  try { & (Join-Path $root '.venv\Scripts\python.exe') (Join-Path $root 'scripts\demo_end_to_end.py') *> (Join-Path $output 'workflow.log'); $testExit = $LASTEXITCODE }
  finally { Pop-Location }
  & pktmon stop | Out-File (Join-Path $output 'capture.log') -Append
  $started = $false
  & pktmon etl2pcap (Join-Path $output 'demo.etl') --out (Join-Path $output 'demo.pcapng') | Out-File (Join-Path $output 'capture.log') -Append
  @{status='captured';workflow_exit=$testExit;scope='Host NIC headers; includes unrelated applications';captured_at=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $output 'status.json')
} catch {
  @{status='failed';error=$_.Exception.Message} | ConvertTo-Json | Set-Content (Join-Path $output 'status.json')
} finally { if ($started) { & pktmon stop | Out-File (Join-Path $output 'capture.log') -Append } }

