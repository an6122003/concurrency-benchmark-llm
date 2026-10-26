# Runs everything after batch 1, one GPU job at a time:
# spec-decoding showdown -> one-shot coding tests -> batch 2 (big models) -> DGX Spark reference run.
$py = 'C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe'
$bt = 'C:\Users\ProArt\Desktop\Project\bench-tools'
$out = 'C:\Users\ProArt\Desktop\Project\concurrency-benchmark-llm\suite-results-rtx-spark-p16-20261025'
function Log($m) { Write-Output "[$(Get-Date -Format HH:mm:ss)] $m" }

Log "waiting for batch 1"
while (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'rtx_spark_bench\.py' }) { Start-Sleep -Seconds 30 }
Log "batch 1 finished"

& $py -X utf8 -u "$bt\spec_showdown.py" qwen3.8-27b
$best = (Get-Content "$out\spec-showdown\qwen3.8-27b.json" -Raw | ConvertFrom-Json).best
if (-not $best) { $best = 'mtp-n2' }
Log "fastest speculative config: $best"

& $py -X utf8 -u "$bt\oneshot_coding.py" --prompt-file "$bt\prompts\oneshot-game-neon-spark.txt" --out "$out\coding\neon-spark" --spec $best
& $py -X utf8 -u "$bt\oneshot_coding.py" --prompt-file "$bt\prompts\oneshot-webapp-galaxy-forge.txt" --out "$out\coding\galaxy-forge" --spec $best
Log "coding tests finished"

Log "waiting for downloads"
while (-not (Select-String -Path "$bt\download-models.log" -Pattern 'all downloads finished' -Quiet)) { Start-Sleep -Seconds 30 }
& $py -X utf8 -u "$bt\rtx_spark_bench.py" gpt-oss-20b nemotron-3.5-super-120b qwen3.8-flash-next
& $py -X utf8 -u "$bt\rtx_spark_bench.py" gpt-oss-20b --phases ref
& $py -X utf8 -u "$bt\analyze.py"
Log "chain finished"
