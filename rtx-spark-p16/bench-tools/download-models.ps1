# Downloads the extra benchmark models (resumable). Each model gets its own folder.
$root = "C:\Users\ProArt\models"
$hf = "https://huggingface.co"
$items = @(
  @{ dir = "gpt-oss-20b"; url = "$hf/ggml-org/gpt-oss-20b-GGUF/resolve/main/gpt-oss-20b-MXFP4.gguf"; file = "gpt-oss-20b-MXFP4.gguf" },
  @{ dir = "nemotron-3.5-super-120b"; url = "$hf/ggml-org/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF/resolve/main/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4.gguf"; file = "NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4.gguf" },
  @{ dir = "nemotron-3.5-super-120b"; url = "$hf/ggml-org/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF/resolve/main/mtp-NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-Q8_0.gguf"; file = "mtp-NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-Q8_0.gguf" },
  @{ dir = "qwen3.8-flash-next"; url = "$hf/unsloth/Qwen3.8-Flash-Next-GGUF/resolve/main/UD-IQ4_XS/Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf"; file = "Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf" },
  @{ dir = "qwen3.8-flash-next"; url = "$hf/unsloth/Qwen3.8-Flash-Next-GGUF/resolve/main/UD-IQ4_XS/Qwen3.8-Flash-Next-UD-IQ4_XS-00002-of-00003.gguf"; file = "Qwen3.8-Flash-Next-UD-IQ4_XS-00002-of-00003.gguf" },
  @{ dir = "qwen3.8-flash-next"; url = "$hf/unsloth/Qwen3.8-Flash-Next-GGUF/resolve/main/UD-IQ4_XS/Qwen3.8-Flash-Next-UD-IQ4_XS-00003-of-00003.gguf"; file = "Qwen3.8-Flash-Next-UD-IQ4_XS-00003-of-00003.gguf" },
  @{ dir = "qwen3.8-flash-next"; url = "$hf/unsloth/Qwen3.8-Flash-Next-GGUF/resolve/main/MTP/mtp-Qwen3.8-Flash-Next-shared-Q8_0.gguf"; file = "mtp-Qwen3.8-Flash-Next-shared-Q8_0.gguf" }
)
foreach ($it in $items) {
  $d = Join-Path $root $it.dir
  New-Item -ItemType Directory -Force $d | Out-Null
  $out = Join-Path $d $it.file
  $part = "$out.part"
  if (Test-Path $out) { Write-Output "$(Get-Date -Format HH:mm:ss) skip $($it.file) (exists)"; continue }
  Write-Output "$(Get-Date -Format HH:mm:ss) start $($it.file)"
  $t0 = Get-Date
  & curl.exe -L --fail --retry 20 --retry-delay 5 --retry-all-errors -C - -s -S -o $part $it.url
  if ($LASTEXITCODE -eq 0) {
    Move-Item -Force $part $out
    $gb = (Get-Item $out).Length / 1GB
    $sec = ((Get-Date) - $t0).TotalSeconds
    Write-Output ("{0} done {1} {2:N2} GB in {3:N0} s ({4:N1} MB/s)" -f (Get-Date -Format HH:mm:ss), $it.file, $gb, $sec, ($gb * 1024 / [math]::Max($sec,1)))
  } else {
    Write-Output "$(Get-Date -Format HH:mm:ss) FAILED $($it.file) curl exit $LASTEXITCODE"
  }
}
Write-Output "$(Get-Date -Format HH:mm:ss) all downloads finished"
