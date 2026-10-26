# Everything that must run at the 50 GB setting before the restart to 96 GB:
# the 50 GB side of the big-model A/B, plus llama-bench for the small models (unaffected by the setting).
$py = 'C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe'
$bt = 'C:\Users\ProArt\Desktop\Project\bench-tools'
function Log($m) { Write-Output "[$(Get-Date -Format HH:mm:ss)] $m" }
function Bench { & $py -X utf8 -u "$bt\rtx_spark_bench.py" @args }

Log "A/B at 50 GB: Nemotron 3.5 Super"
Bench nemotron-3.5-super-120b --phases quick --tag gpu50 --skip-done
Log "llama-bench: small models"
Bench gpt-oss-20b gemma-4-26b-a4b nemotron-3.5-nano-30b qwen3-4b-2507 gemma-4-e4b --phases bench --skip-done
Log "waiting for the Qwen3.8-Flash-Next download"
while (-not (Select-String -Path "$bt\download-models.log" -Pattern 'all downloads finished' -Quiet)) { Start-Sleep -Seconds 20 }
Log "A/B at 50 GB: Qwen3.8-Flash-Next"
Bench qwen3.8-flash-next --phases quick --tag gpu50 --skip-done
Log "pre-restart runs finished: safe to restart"
