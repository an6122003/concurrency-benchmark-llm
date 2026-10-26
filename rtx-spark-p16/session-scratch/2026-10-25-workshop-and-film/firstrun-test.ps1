# A first-time install of the RTX Spark workshop on this laptop, as on a new one:
# a new folder, an empty Ollama model store and an empty uv cache, nothing running.
# (The speech-to-text model's shared cache folder was moved aside beforehand.)
$base = 'C:\Users\ProArt\ai-workshop-firstrun'
$env:WORKSHOP_DIR = Join-Path $base 'ai-workshop'
$env:OLLAMA_MODELS = Join-Path $base 'cache\ollama-models'
$env:UV_CACHE_DIR = Join-Path $base 'cache\uv'
$env:WORKSHOP_YES = '1'; $env:WORKSHOP_NO_START = '1'; $env:CI = '1'
Remove-Item Env:WORKSHOP_BRANCH -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS, $env:UV_CACHE_DIR | Out-Null
$t = Get-Date
"FIRST-RUN start $($t.ToString('s'))"
irm https://raw.githubusercontent.com/an6122003/rtx-spark-ai-workshop/main/install.ps1 | iex
$code = $LASTEXITCODE
"FIRST-RUN done in $([int]((Get-Date) - $t).TotalMinutes) min, setup exit $code"
