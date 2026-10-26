# The rest of the benchmark at the 96 GB setting on the 140 W charger, one GPU job at a time, most valuable first.
# --skip-done skips phases the manifest already records as ok. The battery pause in rtx_spark_bench.py (below 30%,
# resume at 50%) stays as a safety net; the manifest records the battery at the start and end of every phase.
# Qwen3.8-Flash-Next stays out: at 96 GB its 27 GB embedding table leaves Windows without RAM.
$py = 'C:\Users\ProArt\Desktop\Project\tools\python\cpython-3.13.17-windows-aarch64-none\python.exe'
$bt = 'C:\Users\ProArt\Desktop\Project\bench-tools'
$main = 'qwen3.6-35b-a3b', 'qwen3.8-27b', 'nemotron-3.5-super-120b'
$more = 'gpt-oss-20b', 'gemma-4-26b-a4b', 'nemotron-3.5-nano-30b', 'qwen3-4b-2507', 'gemma-4-e4b'
function Log($m) { Write-Output "[$(Get-Date -Format HH:mm:ss)] $m" }
function Bench { & $py -X utf8 -u "$bt\rtx_spark_bench.py" @args }

Log "1/6 full concurrency suite: main models"
Bench @main --phases suite --skip-done

Log "2/6 MTP speculative decoding under load: main models"
Bench @main --phases mtp --skip-done

Log "3/6 batched decode ceiling: main models"
Bench @main --phases batched --skip-done

Log "4/6 full suite and batched decode: the other models"
Bench @more --phases 'suite,batched' --skip-done

Log "5/6 DGX Spark reference parameters"
Bench gpt-oss-20b --phases ref --skip-done

Log "6/6 analysis"
& $py -X utf8 -u "$bt\analyze.py"
& $py -X utf8 -u "$bt\export_csv.py"
Log "pipeline finished"
