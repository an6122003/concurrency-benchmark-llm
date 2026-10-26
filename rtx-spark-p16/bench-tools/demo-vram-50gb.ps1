# Proof for video: a model bigger than the GPU memory setting still runs fully on the GPU.
# Usage: powershell -ExecutionPolicy Bypass -File demo-vram-50gb.ps1 [-Model <gguf>] [-Log <file>]
# Keep Task Manager > Performance > GPU open beside it: watch Dedicated + Shared GPU memory.
param(
  [string]$Model = 'C:\Users\ProArt\models\nemotron-3.5-super-120b\NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4.gguf',
  [string]$Log = "$PSScriptRoot\demo-vram-evidence.txt",
  [string]$Prompt = 'In three short sentences, explain why unified memory lets a laptop run a 120-billion-parameter AI model locally.'
)
$ErrorActionPreference = 'Stop'
$lc = "$PSScriptRoot\llamacpp-cuda-b11671"
$port = 8097
$luid = (typeperf -qx "\GPU Adapter Memory(*)\Dedicated Usage" | Where-Object { $_ -match 'luid' } | Select-Object -First 1)
function Say($text) { $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $text; Write-Host $line; Add-Content -Path $Log -Value $line -Encoding utf8 }
function GpuMem {
  $s = Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage','\GPU Adapter Memory(*)\Shared Usage' -ErrorAction SilentlyContinue
  $ded = ($s.CounterSamples | Where-Object { $_.Path -match 'dedicated' } | Measure-Object CookedValue -Maximum).Maximum
  $sha = ($s.CounterSamples | Where-Object { $_.Path -match 'shared' } | Measure-Object CookedValue -Maximum).Maximum
  # Binary GB (GiB), the unit Task Manager and the NVIDIA App show as "GB".
  '{0:N1} GB dedicated + {1:N1} GB shared = {2:N1} GB on the GPU' -f ($ded/1GB), ($sha/1GB), (($ded+$sha)/1GB)
}

Set-Content -Path $Log -Value "RTX Spark VRAM demo - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -Encoding utf8
$gpu = (nvidia-smi -i 0 --query-gpu=name,memory.total,driver_version --format=csv,noheader).Trim()
Say "GPU: $gpu   <- the GPU memory setting (dedicated VRAM)"
$ErrorActionPreference = 'Continue'  # PS 5.1 turns a native program's stderr into errors
$cuda = & "$lc\llama-bench.exe" --list-devices 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match '^\s+CUDA0:' }
$ErrorActionPreference = 'Stop'
Say ("CUDA can address: " + ($cuda -replace '^\s+', '') + "   <- dedicated + shared system memory")
Say ("Model file: {0} = {1:N1} GB" -f (Split-Path $Model -Leaf), ((Get-Item $Model).Length/1GB))
Say "Before load: $(GpuMem)"

$serverLog = Join-Path $PSScriptRoot 'demo-vram-server.log'
$serverErr = Join-Path $PSScriptRoot 'demo-vram-server.err.log'
$p = Start-Process -FilePath "$lc\llama-server.exe" -PassThru -WindowStyle Hidden -RedirectStandardOutput $serverLog -RedirectStandardError $serverErr `
  -ArgumentList @('-m', $Model, '--host', '127.0.0.1', '--port', "$port", '-ngl', '999', '--fit', 'off', '-fa', 'on',
                  '-c', '8192', '-np', '1', '--load-mode', 'dio', '--reasoning', 'off', '--no-webui', '-lv', '4')
$t0 = Get-Date
Say "Loading every layer onto the GPU (-ngl 999) ..."
while ($true) {
  if ($p.HasExited) { Say "llama-server exited with code $($p.ExitCode)"; Get-Content $serverLog, $serverErr -Tail 15 | ForEach-Object { Say $_ }; exit 1 }
  try { if ((Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$port/health" -TimeoutSec 2).StatusCode -eq 200) { break } } catch {}
  Start-Sleep -Milliseconds 500
}
Say ("Loaded in {0:N0} s" -f ((Get-Date) - $t0).TotalSeconds)
Get-Content $serverLog, $serverErr | Select-String -Pattern 'Total VRAM|offloaded|CUDA0 model buffer|CUDA0 KV buffer|CUDA0 RS buffer|CUDA0 compute buffer' |
  ForEach-Object { Say ("llama.cpp: " + ($_.Line -replace '^[\d.]+ [IWE] ', '').Trim()) }
Say "After load:  $(GpuMem)"

Say "Prompt: $Prompt"
$body = @{ messages = @(@{ role = 'user'; content = $Prompt }); max_tokens = 200; temperature = 0.6 } | ConvertTo-Json -Depth 4
$r = Invoke-RestMethod -Method Post "http://127.0.0.1:$port/v1/chat/completions" -Body $body -ContentType 'application/json'
Say ("Answer: " + ($r.choices[0].message.content -replace '\s+', ' ').Trim())
Say ("Speed: prompt {0:N0} tok/s, generation {1:N1} tok/s ({2} tokens), all on the GPU" -f $r.timings.prompt_per_second, $r.timings.predicted_per_second, $r.timings.predicted_n)
Say "During run: $(GpuMem)"
Stop-Process -Id $p.Id -Force
Say "Done. Evidence saved to $Log"
