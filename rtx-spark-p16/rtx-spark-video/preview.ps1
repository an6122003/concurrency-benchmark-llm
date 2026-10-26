# Stills of the film at given seconds (the clock still runs every frame up to each one), for checking the layout.
#   powershell -File preview.ps1 -Format h -At 5,9,18.5 [-Port 9340]
#   powershell -File preview.ps1 -Format v -At 1,5 -Base http://127.0.0.1:8777/quick.html -Tag -quick
param([ValidateSet('h', 'v')] [string]$Format = 'h', [string]$At = '5', [int]$Port = 9340,
      [string]$Base = 'http://127.0.0.1:8777/index.html', [string]$Tag = '')
$times = @($At -split '[,; ]+' | Where-Object { $_ } | ForEach-Object { [double]::Parse($_, [Globalization.CultureInfo]::InvariantCulture) })
$sp = 'C:\Users\ProArt\AppData\Local\Temp\claude\C--Users-ProArt-Desktop-Project\7798a40b-a3ff-4606-ac88-bbf988d29d19\scratchpad'
$out = Join-Path $PSScriptRoot 'out\preview'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$W, $H = if ($Format -eq 'h') { 1920, 1080 } else { 1080, 1920 }
$steps = @(@{js = '(async () => { for (let i = 0; i < 100 && !(window.FILM && document.fonts.status === "loaded"); i++) await new Promise(r => setTimeout(r, 100)); return !!window.FILM; })()'; wait = 0.2})
$prev = 0
foreach ($s in $times) {
  $n = [int][Math]::Round($s * 30)
  $steps += @{js = "for (let i = $prev; i <= $n; i++) FILM.frame(i); new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r($n))))"; wait = 0.1; out = (Join-Path $out ("{0}{1}-{2:000.0}.jpg" -f $Format, $Tag, $s))}
  $prev = $n + 1
}
$stepsFile = Join-Path $out "steps-$Format$Tag.json"
$steps | ConvertTo-Json -Depth 4 | Set-Content -Path $stepsFile -Encoding UTF8
& "$sp\cdp-shot.ps1" -Url "$Base`?f=$Format" -Steps $stepsFile -Width $W -Height $H -Port $Port
