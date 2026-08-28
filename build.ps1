<#
    Baut den Foto-Sortierer als eigenstaendige EXE und optional als Installer.

    Aufruf:   .\build.ps1
    Ergebnis: dist\Fotosortierer.exe
              installer_output\Fotosortierer-Setup-1.0.0.exe  (falls Inno Setup installiert ist)
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

Write-Host "`n[1/2] Baue EXE mit PyInstaller..." -ForegroundColor Cyan
& ".\.venv\Scripts\pyinstaller.exe" fotosortierer.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller-Build fehlgeschlagen." }
Write-Host "OK: dist\Fotosortierer.exe" -ForegroundColor Green

Write-Host "`n[2/2] Baue Installer mit Inno Setup..." -ForegroundColor Cyan
$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($null -eq $iscc) {
    Write-Host "Inno Setup nicht gefunden - Installer uebersprungen." -ForegroundColor Yellow
    Write-Host "Installieren mit:  winget install --id JRSoftware.InnoSetup" -ForegroundColor Yellow
} else {
    & $iscc installer.iss
    if ($LASTEXITCODE -ne 0) { throw "Inno-Setup-Build fehlgeschlagen." }
    Write-Host "OK: installer_output\Fotosortierer-Setup-1.0.0.exe" -ForegroundColor Green
}

Write-Host "`nFertig." -ForegroundColor Green
