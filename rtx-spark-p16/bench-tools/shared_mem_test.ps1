# Does a model run slower when its weights sit in Windows "shared" GPU memory?
# Same models, same 50 GB setting, three runs each:
#   A  baseline: weights land in dedicated GPU memory
#   B  spilled:  an idle "balloon" process fills the dedicated pool first, so the weights land in shared memory
#   A2 baseline again, to rule out drift (heat, battery)
# Per-process GPU memory counters record where each run's weights actually were.
$ErrorActionPreference = 'Continue'
$bt = $PSScriptRoot
$lc = "$bt\llamacpp-cuda-b11671"
$out = 'C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025\shared-memory-test'
New-Item -ItemType Directory -Force $out | Out-Null
$models = [ordered]@{
  'qwen3.8-27b'     = 'C:\Users\ProArt\AppData\Local\hermes\models\Qwen3.8-27B-UD-Q4_K_M.gguf'
  'qwen3.6-35b-a3b' = 'C:\Users\ProArt\AppData\Local\hermes\models\Qwen3.6-35B-A3B-UD-Q4_K_M.gguf'
}
function Log($m) { $l = "[{0}] {1}" -f (Get-Date -Format HH:mm:ss), $m; Write-Output $l; Add-Content -Path "$out\log.txt" -Value $l -Encoding utf8 }

function ProcGpuMem([int]$procId) {
  $c = Get-Counter '\GPU Process Memory(*)\Dedicated Usage', '\GPU Process Memory(*)\Shared Usage' -ErrorAction SilentlyContinue
  $mine = $c.CounterSamples | Where-Object { $_.InstanceName -like "pid_$($procId)_*" }
  [pscustomobject]@{
    ded_gb    = [math]::Round((($mine | Where-Object { $_.Path -match 'dedicated usage' } | Measure-Object CookedValue -Sum).Sum) / 1GB, 2)
    shared_gb = [math]::Round((($mine | Where-Object { $_.Path -match 'shared usage' } | Measure-Object CookedValue -Sum).Sum) / 1GB, 2)
  }
}

function AdapterMem {
  $c = Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage', '\GPU Adapter Memory(*)\Shared Usage' -ErrorAction SilentlyContinue
  '{0:N1} GB dedicated + {1:N1} GB shared' -f ((($c.CounterSamples | Where-Object { $_.Path -match 'dedicated' } | Measure-Object CookedValue -Maximum).Maximum) / 1GB),
    ((($c.CounterSamples | Where-Object { $_.Path -match 'shared' } | Measure-Object CookedValue -Maximum).Maximum) / 1GB)
}

function RunBench($key, $tag) {
  $json = "$out\$key-$tag.json"
  $p = Start-Process -FilePath "$lc\llama-bench.exe" -PassThru -WindowStyle Hidden -RedirectStandardOutput $json -RedirectStandardError "$out\$key-$tag.err" `
    -ArgumentList @('-m', $models[$key], '-ngl', '999', '-fa', '1', '-ub', '2048', '-p', '512', '-n', '128', '-r', '3', '-o', 'json')
  $peak = [pscustomobject]@{ ded_gb = 0; shared_gb = 0 }
  while (-not $p.HasExited) {
    $m = ProcGpuMem $p.Id
    if (($m.ded_gb + $m.shared_gb) -gt ($peak.ded_gb + $peak.shared_gb)) { $peak = $m }
    Start-Sleep -Milliseconds 300
  }
  $r = Get-Content $json -Raw | ConvertFrom-Json
  $row = [pscustomobject]@{
    model = $key; run = $tag
    pp512 = [math]::Round(($r | Where-Object { $_.n_prompt -gt 0 }).avg_ts, 1)
    tg128 = [math]::Round(($r | Where-Object { $_.n_gen -gt 0 }).avg_ts, 2)
    weights_dedicated_gb = $peak.ded_gb; weights_shared_gb = $peak.shared_gb
  }
  Log ("{0,-16} {1,-9} pp512 {2,7:N0} t/s  tg128 {3,6:N2} t/s  in {4:N1} GB dedicated + {5:N1} GB shared" -f $key, $tag, $row.pp512, $row.tg128, $row.weights_dedicated_gb, $row.weights_shared_gb)
  $row
}

Set-Content -Path "$out\log.txt" -Value "Shared vs dedicated GPU memory test - $(Get-Date -Format 'yyyy-MM-dd HH:mm') - setting: $((nvidia-smi -i 0 --query-gpu=memory.total --format=csv,noheader).Trim()) dedicated" -Encoding utf8
$rows = @()
Log "Idle: $(AdapterMem)"
foreach ($k in $models.Keys) { $rows += RunBench $k 'A' }

Log "Starting balloon: idle llama-server holding ~47 GB so the dedicated pool is full"
$balloon = Start-Process -FilePath "$lc\llama-server.exe" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$out\balloon.log" -RedirectStandardError "$out\balloon.err" `
  -ArgumentList @('-m', 'C:\Users\ProArt\models\qwen3-4b-instruct-2507\Qwen3-4B-Instruct-2507-Q4_K_M.gguf', '--host', '127.0.0.1', '--port', '8096',
                  '-ngl', '999', '--fit', 'off', '-fa', 'on', '-c', '340000', '-np', '1', '--no-webui')
while ($true) {
  if ($balloon.HasExited) { Log "balloon exited with code $($balloon.ExitCode)"; break }
  try { if ((Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8096/health' -TimeoutSec 2).StatusCode -eq 200) { break } } catch {}
  Start-Sleep -Milliseconds 500
}
$bm = ProcGpuMem $balloon.Id
Log ("Balloon holds {0:N1} GB dedicated + {1:N1} GB shared. Adapter now: {2}" -f $bm.ded_gb, $bm.shared_gb, (AdapterMem))
foreach ($k in $models.Keys) { $rows += RunBench $k 'B-spill' }
$bm = ProcGpuMem $balloon.Id
Log ("Balloon after the spilled runs: {0:N1} GB dedicated + {1:N1} GB shared" -f $bm.ded_gb, $bm.shared_gb)
Stop-Process -Id $balloon.Id -Force
Start-Sleep -Seconds 5

foreach ($k in $models.Keys) { $rows += RunBench $k 'A2' }
$rows | ConvertTo-Json | Set-Content -Path "$out\results.json" -Encoding utf8
$rows | Export-Csv -Path "$out\results.csv" -NoTypeInformation -Encoding utf8
Log "Done"
