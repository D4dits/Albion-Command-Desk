[CmdletBinding()]
param(
    [string]$Source = "assets/logo.png",
    [string]$SquareLogoOut = "assets/branding/albion-command-desk-logo-2048.png",
    [string]$WideLogoOut = "assets/branding/albion-command-desk-logo-wide-3200.png",
    [string]$IconOut = "albion_dps/qt/ui/command_desk_icon.png",
    [string]$IcoOut = "albion_dps/qt/ui/command_desk_icon.ico",
    [string]$PrimaryWord = "Ablion",
    [string]$SecondaryWord = "Command Desk"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

function New-Graphics {
    param([System.Drawing.Bitmap]$Bitmap)
    $graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    return $graphics
}

function Add-StyledText {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [string]$FontFamily,
        [float]$SizePx,
        [System.Drawing.FontStyle]$FontStyle,
        [System.Drawing.RectangleF]$Bounds,
        [System.Drawing.Color]$FillColor,
        [System.Drawing.Color]$StrokeColor,
        [float]$StrokeWidthPx
    )
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $stringFormat = New-Object System.Drawing.StringFormat
    $stringFormat.Alignment = [System.Drawing.StringAlignment]::Center
    $stringFormat.LineAlignment = [System.Drawing.StringAlignment]::Center
    $emSize = $Graphics.DpiY * $SizePx / 72.0
    $path.AddString($Text, (New-Object System.Drawing.FontFamily($FontFamily)), [int]$FontStyle, $emSize, $Bounds, $stringFormat)
    $fillBrush = New-Object System.Drawing.SolidBrush($FillColor)
    $strokePen = New-Object System.Drawing.Pen($StrokeColor, $StrokeWidthPx)
    $strokePen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $Graphics.FillPath($fillBrush, $path)
    $Graphics.DrawPath($strokePen, $path)
    $fillBrush.Dispose()
    $strokePen.Dispose()
    $path.Dispose()
    $stringFormat.Dispose()
}

function Crop-SourceEmblem {
    param([System.Drawing.Bitmap]$SourceBitmap)
    # Crop upper emblem area to remove original "Albion" wordmark.
    $cropRect = New-Object System.Drawing.Rectangle(132, 20, 760, 540)
    $crop = New-Object System.Drawing.Bitmap($cropRect.Width, $cropRect.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = New-Graphics -Bitmap $crop
    $destRect = New-Object System.Drawing.Rectangle(0, 0, $cropRect.Width, $cropRect.Height)
    $g.DrawImage($SourceBitmap, $destRect, $cropRect, [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    return $crop
}

function Write-IcoFromPng {
    param(
        [string]$PngPath,
        [string]$IcoPath
    )
    [byte[]]$pngBytes = [System.IO.File]::ReadAllBytes($PngPath)
    $bytesInRes = [uint32]$pngBytes.Length
    $imageOffset = [uint32]22

    $stream = New-Object System.IO.MemoryStream
    $writer = New-Object System.IO.BinaryWriter($stream)
    # ICONDIR
    $writer.Write([UInt16]0)   # reserved
    $writer.Write([UInt16]1)   # type: icon
    $writer.Write([UInt16]1)   # images
    # ICONDIRENTRY
    $writer.Write([byte]0)     # width: 256
    $writer.Write([byte]0)     # height: 256
    $writer.Write([byte]0)     # color count
    $writer.Write([byte]0)     # reserved
    $writer.Write([UInt16]1)   # planes
    $writer.Write([UInt16]32)  # bit count
    $writer.Write($bytesInRes)
    $writer.Write($imageOffset)
    $writer.Write($pngBytes)
    $writer.Flush()
    [System.IO.File]::WriteAllBytes($IcoPath, $stream.ToArray())
    $writer.Dispose()
    $stream.Dispose()
}

$sourcePath = (Resolve-Path $Source).Path
$sourceBitmap = [System.Drawing.Bitmap]::FromFile($sourcePath)
$emblem = Crop-SourceEmblem -SourceBitmap $sourceBitmap

try {
    # Square logo 2048x2048
    $square = New-Object System.Drawing.Bitmap(2048, 2048, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $gSquare = New-Graphics -Bitmap $square
    $gSquare.Clear([System.Drawing.Color]::FromArgb(255, 8, 12, 18))

    $glowBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        (New-Object System.Drawing.Rectangle(0, 0, 2048, 2048)),
        ([System.Drawing.Color]::FromArgb(90, 255, 158, 46)),
        ([System.Drawing.Color]::FromArgb(6, 0, 0, 0)),
        [System.Drawing.Drawing2D.LinearGradientMode]::Vertical
    )
    $gSquare.FillRectangle($glowBrush, 0, 0, 2048, 2048)
    $glowBrush.Dispose()

    $gSquare.DrawImage($emblem, (New-Object System.Drawing.Rectangle(284, 140, 1480, 1050)))

    $plateRect = New-Object System.Drawing.Rectangle(240, 1260, 1568, 520)
    $plateBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(200, 9, 15, 26))
    $gSquare.FillRectangle($plateBrush, $plateRect)
    $plateBrush.Dispose()

    Add-StyledText -Graphics $gSquare -Text $PrimaryWord -FontFamily "Segoe UI Black" -SizePx 190 -FontStyle ([System.Drawing.FontStyle]::Bold) -Bounds (New-Object System.Drawing.RectangleF(260, 1295, 1528, 210)) -FillColor ([System.Drawing.Color]::FromArgb(255, 248, 176, 62)) -StrokeColor ([System.Drawing.Color]::FromArgb(255, 69, 26, 8)) -StrokeWidthPx 10
    Add-StyledText -Graphics $gSquare -Text $SecondaryWord -FontFamily "Segoe UI Semibold" -SizePx 88 -FontStyle ([System.Drawing.FontStyle]::Bold) -Bounds (New-Object System.Drawing.RectangleF(260, 1525, 1528, 130)) -FillColor ([System.Drawing.Color]::FromArgb(255, 224, 234, 245)) -StrokeColor ([System.Drawing.Color]::FromArgb(255, 12, 18, 28)) -StrokeWidthPx 4

    $squareLogoPath = Join-Path (Get-Location) $SquareLogoOut
    $square.Save($squareLogoPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $gSquare.Dispose()
    $square.Dispose()

    # Wide logo 3200x1200
    $wide = New-Object System.Drawing.Bitmap(3200, 1200, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $gWide = New-Graphics -Bitmap $wide
    $gWide.Clear([System.Drawing.Color]::FromArgb(255, 6, 10, 16))
    $gWide.DrawImage($emblem, (New-Object System.Drawing.Rectangle(140, 70, 980, 700)))
    Add-StyledText -Graphics $gWide -Text $PrimaryWord -FontFamily "Segoe UI Black" -SizePx 230 -FontStyle ([System.Drawing.FontStyle]::Bold) -Bounds (New-Object System.Drawing.RectangleF(1180, 200, 1900, 260)) -FillColor ([System.Drawing.Color]::FromArgb(255, 248, 176, 62)) -StrokeColor ([System.Drawing.Color]::FromArgb(255, 69, 26, 8)) -StrokeWidthPx 12
    Add-StyledText -Graphics $gWide -Text $SecondaryWord -FontFamily "Segoe UI Semibold" -SizePx 120 -FontStyle ([System.Drawing.FontStyle]::Bold) -Bounds (New-Object System.Drawing.RectangleF(1180, 470, 1900, 160)) -FillColor ([System.Drawing.Color]::FromArgb(255, 224, 234, 245)) -StrokeColor ([System.Drawing.Color]::FromArgb(255, 12, 18, 28)) -StrokeWidthPx 5

    $linePen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 241, 191, 80), 16)
    $linePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $linePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $gWide.DrawLine($linePen, 1240, 700, 2860, 700)
    $linePen.Dispose()

    $wideLogoPath = Join-Path (Get-Location) $WideLogoOut
    $wide.Save($wideLogoPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $gWide.Dispose()
    $wide.Dispose()

    # App icon 256x256 (emblem-focused)
    $icon = New-Object System.Drawing.Bitmap(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $gIcon = New-Graphics -Bitmap $icon
    $gIcon.Clear([System.Drawing.Color]::Transparent)
    $bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 10, 18, 30))
    $gIcon.FillRectangle($bgBrush, 0, 0, 256, 256)
    $bgBrush.Dispose()
    $gIcon.DrawImage($emblem, (New-Object System.Drawing.Rectangle(8, 5, 240, 170)))
    Add-StyledText -Graphics $gIcon -Text $PrimaryWord -FontFamily "Segoe UI Black" -SizePx 26 -FontStyle ([System.Drawing.FontStyle]::Bold) -Bounds (New-Object System.Drawing.RectangleF(4, 178, 248, 42)) -FillColor ([System.Drawing.Color]::FromArgb(255, 248, 176, 62)) -StrokeColor ([System.Drawing.Color]::FromArgb(255, 69, 26, 8)) -StrokeWidthPx 2
    Add-StyledText -Graphics $gIcon -Text "Desk" -FontFamily "Segoe UI Semibold" -SizePx 17 -FontStyle ([System.Drawing.FontStyle]::Bold) -Bounds (New-Object System.Drawing.RectangleF(4, 220, 248, 28)) -FillColor ([System.Drawing.Color]::FromArgb(255, 224, 234, 245)) -StrokeColor ([System.Drawing.Color]::FromArgb(255, 12, 18, 28)) -StrokeWidthPx 1.5

    $iconPath = Join-Path (Get-Location) $IconOut
    $icon.Save($iconPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $icoPath = Join-Path (Get-Location) $IcoOut
    Write-IcoFromPng -PngPath $iconPath -IcoPath $icoPath
    $gIcon.Dispose()
    $icon.Dispose()

    Write-Host "[branding] Generated square logo: $SquareLogoOut"
    Write-Host "[branding] Generated wide logo:   $WideLogoOut"
    Write-Host "[branding] Updated app icon:      $IconOut"
    Write-Host "[branding] Updated app ico:       $IcoOut"
}
finally {
    $emblem.Dispose()
    $sourceBitmap.Dispose()
}
