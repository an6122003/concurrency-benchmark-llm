param(
  [Parameter(Mandatory)] [string]$Url,
  [Parameter(Mandatory)] [string]$Steps,   # JSON file: [{js, wait, out}]
  [int]$Width = 1920, [int]$Height = 1080, [double]$Scale = 1, [int]$Port = 9333
)
$ErrorActionPreference = 'Stop'
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$prof = Join-Path $PSScriptRoot 'edge-prof'
$proc = Start-Process $edge -PassThru -ArgumentList @('--headless=new', "--remote-debugging-port=$Port", '--remote-allow-origins=*',
  "--window-size=$Width,$Height", "--user-data-dir=$prof", '--hide-scrollbars', '--no-first-run', 'about:blank')
try {
  $ws = $null
  for ($i = 0; $i -lt 50 -and -not $ws; $i++) {
    Start-Sleep -Milliseconds 300
    try {
      $t = (Invoke-RestMethod "http://127.0.0.1:$Port/json/list") | Where-Object { $_.type -eq 'page' } | Select-Object -First 1
      if ($t) { $ws = $t.webSocketDebuggerUrl }
    } catch {}
  }
  if (-not $ws) { throw 'no devtools target' }
  $sock = New-Object System.Net.WebSockets.ClientWebSocket
  $ct = [Threading.CancellationToken]::None
  $sock.ConnectAsync([Uri]$ws, $ct).Wait()
  $script:id = 0
  function Cdp($method, $params) {
    $script:id++
    $msg = @{id = $script:id; method = $method; params = $params} | ConvertTo-Json -Depth 10 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($msg)
    $sock.SendAsync((New-Object ArraySegment[byte] -ArgumentList (, $bytes)), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).Wait()
    while ($true) {
      $ms = New-Object IO.MemoryStream
      do {
        $buf = New-Object byte[] 1048576
        $r = $sock.ReceiveAsync((New-Object ArraySegment[byte] -ArgumentList (, $buf)), $ct).Result
        $ms.Write($buf, 0, $r.Count)
      } while (-not $r.EndOfMessage)
      $text = [Text.Encoding]::UTF8.GetString($ms.ToArray())
      if ($text -match ('^\{"id":' + $script:id + ',')) { return $text }
    }
  }
  $null = Cdp 'Emulation.setDeviceMetricsOverride' @{width = $Width; height = $Height; deviceScaleFactor = $Scale; mobile = $false}
  $null = Cdp 'Page.addScriptToEvaluateOnNewDocument' @{source = 'window.__errs=[];addEventListener("error",e=>__errs.push(String(e.message)));addEventListener("unhandledrejection",e=>__errs.push("rejection: "+String(e.reason)));'}
  $null = Cdp 'Page.navigate' @{url = $Url}
  Start-Sleep -Seconds 4
  foreach ($s in (Get-Content $Steps -Raw | ConvertFrom-Json)) {
    if ($s.js) {
      $res = Cdp 'Runtime.evaluate' @{expression = $s.js; awaitPromise = $true; returnByValue = $true}
      if ($res -match '"exceptionDetails"') { Write-Output "JS error: $res" }
      elseif ($res -match '"value":(.*)\}\}\}$') { Write-Output "js -> $($Matches[1])" }
    }
    if ($s.wait) { Start-Sleep -Milliseconds ([int]($s.wait * 1000)) }
    if ($s.out) {
      $res = Cdp 'Page.captureScreenshot' @{format = 'jpeg'; quality = 88}
      if ($res -match '"data":"([^"]+)"') {
        [IO.File]::WriteAllBytes($s.out, [Convert]::FromBase64String($Matches[1]))
        Write-Output "saved $($s.out)"
      } else { Write-Output "no screenshot: $($res.Substring(0, [Math]::Min(300, $res.Length)))" }
    }
  }
  $logs = Cdp 'Runtime.evaluate' @{expression = 'JSON.stringify(window.__errs || [])'; returnByValue = $true}
  Write-Output "page errors: $logs"
  try { $null = Cdp 'Browser.close' @{} } catch {}
} finally {
  Start-Sleep -Milliseconds 500
  if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
