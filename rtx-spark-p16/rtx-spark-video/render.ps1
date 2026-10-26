# Render the film frame by frame in headless Edge: the page steps its own clock (FILM.frame(n)), then the frame is
# captured. Frames go to out\frames-<format><tag>\00000.jpg ...; the film's sound cues (and its cut of the score,
# when it has one) to out\cues-<format><tag>.json.
#
#   powershell -File render.ps1 -Format h [-From 0] [-To 99999] [-Port 9334] [-Quality 92]
#   powershell -File render.ps1 -Format v -Base http://127.0.0.1:8777/quick.html -Tag -quick     (the TikTok cut)
param(
  [ValidateSet('h', 'v')] [string]$Format = 'h',
  [int]$From = 0, [int]$To = 999999, [int]$Port = 9334, [int]$Quality = 92,
  [string]$Base = 'http://127.0.0.1:8777/index.html', [string]$Tag = ''
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$out = Join-Path $root "out\frames-$Format$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$W, $H = if ($Format -eq 'h') { 1920, 1080 } else { 1080, 1920 }
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$prof = Join-Path $root "out\edge-$Format$Tag"
$proc = Start-Process $edge -PassThru -ArgumentList @('--headless=new', "--remote-debugging-port=$Port", '--remote-allow-origins=*',
  "--window-size=$W,$H", "--user-data-dir=$prof", '--hide-scrollbars', '--no-first-run', '--force-color-profile=srgb',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding', 'about:blank')
try {
  $ws = $null
  for ($i = 0; $i -lt 60 -and -not $ws; $i++) {
    Start-Sleep -Milliseconds 300
    try { $t = (Invoke-RestMethod "http://127.0.0.1:$Port/json/list") | Where-Object { $_.type -eq 'page' } | Select-Object -First 1; if ($t) { $ws = $t.webSocketDebuggerUrl } } catch {}
  }
  if (-not $ws) { throw 'no devtools target' }
  $sock = New-Object System.Net.WebSockets.ClientWebSocket
  $ct = [Threading.CancellationToken]::None
  $sock.ConnectAsync([Uri]$ws, $ct).Wait()
  $script:id = 0
  $buf = New-Object byte[] 4194304
  function Cdp($method, $params) {
    $script:id++
    $msg = @{id = $script:id; method = $method; params = $params} | ConvertTo-Json -Depth 10 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($msg)
    $sock.SendAsync((New-Object ArraySegment[byte] -ArgumentList (, $bytes)), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).Wait()
    while ($true) {
      $ms = New-Object IO.MemoryStream
      do {
        $r = $sock.ReceiveAsync((New-Object ArraySegment[byte] -ArgumentList (, $buf)), $ct).Result
        $ms.Write($buf, 0, $r.Count)
      } while (-not $r.EndOfMessage)
      $text = [Text.Encoding]::UTF8.GetString($ms.ToArray())
      if ($text.StartsWith('{"id":' + $script:id + ',')) { return $text }
    }
  }
  function Eval($expr) {
    $res = Cdp 'Runtime.evaluate' @{expression = $expr; awaitPromise = $true; returnByValue = $true} | ConvertFrom-Json
    if ($res.result.exceptionDetails) { throw "page error: $($res.result.exceptionDetails | ConvertTo-Json -Compress -Depth 6)" }
    return $res.result.result.value
  }
  $null = Cdp 'Emulation.setDeviceMetricsOverride' @{width = $W; height = $H; deviceScaleFactor = 1; mobile = $false}
  $null = Cdp 'Page.navigate' @{url = "$Base`?f=$Format"}
  $ready = $false
  for ($i = 0; $i -lt 100 -and -not $ready; $i++) {
    Start-Sleep -Milliseconds 200
    try { $ready = (Eval '!!(window.FILM && document.fonts.status === "loaded")') -eq $true } catch {}
  }
  if (-not $ready) { throw 'the film did not load' }
  $frames = [int](Eval 'FILM.frames')
  $last = [Math]::Min($To, $frames - 1)
  "film: $frames frames ($([Math]::Round($frames / 30, 1)) s); rendering $From..$last as $Format into $out"
  [IO.File]::WriteAllText((Join-Path $root "out\cues-$Format$Tag.json"), (Eval 'JSON.stringify({fps: FILM.fps, duration: FILM.duration, downbeats: FILM.downbeats, score: FILM.score || null, cues: FILM.cues})'))
  $sw = [Diagnostics.Stopwatch]::StartNew()
  # frames are stepped in order from 0 (the chip's simulation needs every step), captured from $From
  for ($n = 0; $n -le $last; $n++) {
    # FILM.frame may return a promise (a cut that shows image frames waits for them to decode)
    $null = Eval "Promise.resolve(FILM.frame($n)).then(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(1)))))"
    if ($n -lt $From) { continue }
    $res = Cdp 'Page.captureScreenshot' @{format = 'jpeg'; quality = $Quality; fromSurface = $true}
    $i0 = $res.IndexOf('"data":"') + 8
    $i1 = $res.IndexOf('"', $i0)
    [IO.File]::WriteAllBytes((Join-Path $out ('{0:D5}.jpg' -f $n)), [Convert]::FromBase64String($res.Substring($i0, $i1 - $i0)))
    if ($n % 150 -eq 0) { "frame $n / $last  ($([Math]::Round($sw.Elapsed.TotalSeconds)) s)" }
  }
  "done: $($last - $From + 1) frames in $([Math]::Round($sw.Elapsed.TotalMinutes, 1)) min"
  try { $null = Cdp 'Browser.close' @{} } catch {}
} finally {
  Start-Sleep -Milliseconds 400
  if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
