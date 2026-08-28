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

Write-Host "`nFertig: dist\Fotosortierer.exe" -ForegroundColor Green
