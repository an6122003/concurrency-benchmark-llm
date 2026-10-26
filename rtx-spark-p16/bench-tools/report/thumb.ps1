# Resizes a screenshot to a small JPEG for the report page: thumb.ps1 <src> <dst> [width] [quality]
param([string]$Src, [string]$Dst, [int]$Width = 640, [long]$Quality = 72)
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($Src)
$height = [int][math]::Round($img.Height * $Width / $img.Width)
$bmp = New-Object System.Drawing.Bitmap $Width, $height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.DrawImage($img, 0, 0, $Width, $height)
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$params = New-Object System.Drawing.Imaging.EncoderParameters 1
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), $Quality
$bmp.Save($Dst, $codec, $params)
$g.Dispose(); $bmp.Dispose(); $img.Dispose()
