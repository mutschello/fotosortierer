<#
    Baut den Foto-Sortierer als eigenstaendige Windows-EXE.

    Aufruf:   .\build.ps1
    Ergebnis: dist\Fotosortierer.exe
#>

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Keine virtuelle Umgebung gefunden - wird angelegt..." -ForegroundColor Yellow
    py -3.12 -m venv .venv
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt pyinstaller
}

Write-Host "`nBaue EXE mit PyInstaller..." -ForegroundColor Cyan
& ".\.venv\Scripts\pyinstaller.exe" fotosortierer.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller-Build fehlgeschlagen." }

# Die GPL verlangt, dass Empfaenger des Programms auch den Quellcode
# bekommen. Er wird deshalb bei jedem Build als Archiv neben die EXE gelegt
# und zusammen mit ihr weitergegeben.
Write-Host "`nPacke Quellcode fuer die Weitergabe..." -ForegroundColor Cyan
$quellen = @(
    "main.py", "sortier_logik.py", "pfade.py",
    "fotosortierer.spec", "version_info.txt", "fotosortierer.ico",
    "build.ps1", "requirements.txt", "ANLEITUNG.md", "LICENSE"
)
$fehlend = $quellen | Where-Object { -not (Test-Path $_) }
if ($fehlend) { throw "Quellcode unvollstaendig, fehlt: $($fehlend -join ', ')" }

$archiv = "dist\Quellcode.zip"
if (Test-Path $archiv) { Remove-Item $archiv }
Compress-Archive -Path $quellen -DestinationPath $archiv
Write-Host "OK: $archiv" -ForegroundColor Green

Write-Host "`nFertig. An Kunden weitergeben:" -ForegroundColor Green
Write-Host "  dist\Fotosortierer.exe" -ForegroundColor Green
Write-Host "  dist\Quellcode.zip   (von der GPL gefordert)" -ForegroundColor Green
