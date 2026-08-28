<#
    Baut den Foto-Sortierer als eigenstaendige Windows-EXE.

    Aufruf:   .\build.ps1
    Ergebnis: dist\Fotosortierer\ (Programmordner)
              dist\Fotosortierer-Setup-<version>.exe  (zum Weitergeben)
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

# Die GPL verlangt, dass Empfaenger des Programms auch den Quellcode
# bekommen. Das Archiv wird deshalb vor dem Build gepackt und von
# fotosortierer.spec in die EXE eingebettet. Abrufbar im Programm
# unter Hilfe > Quellcode speichern.
Write-Host "`nPacke Quellcode fuer die Einbettung in die EXE..." -ForegroundColor Cyan
$quellen = @(
    "main.py", "sortier_logik.py", "pfade.py",
    "fotosortierer.spec", "version_info.txt", "fotosortierer.ico",
    "build.ps1", "installer.iss", "requirements.txt", "ANLEITUNG.md", "LICENSE"
)
$fehlend = $quellen | Where-Object { -not (Test-Path $_) }
if ($fehlend) { throw "Quellcode unvollstaendig, fehlt: $($fehlend -join ', ')" }

$archiv = "Quellcode.zip"
if (Test-Path $archiv) { Remove-Item $archiv }
Compress-Archive -Path $quellen -DestinationPath $archiv
Write-Host "OK: $archiv" -ForegroundColor Green

Write-Host "`nBaue EXE mit PyInstaller..." -ForegroundColor Cyan
& ".\.venv\Scripts\pyinstaller.exe" fotosortierer.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller-Build fehlgeschlagen." }


$version = (Select-String -Path pfade.py -Pattern '^VERSION = "(.+)"').Matches[0].Groups[1].Value

# Setup-Assistent bauen. Inno Setup erzeugt daraus eine einzelne
# Installationsdatei mit Lizenzseite, Startmenue-Eintrag und Eintrag in
# "Apps & Features" zum sauberen Deinstallieren.
Write-Host "`nBaue Setup mit Inno Setup..." -ForegroundColor Cyan
$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($null -eq $iscc) {
    Write-Host "Inno Setup nicht gefunden - Setup uebersprungen." -ForegroundColor Yellow
    Write-Host "Installieren mit:  winget install --id JRSoftware.InnoSetup" -ForegroundColor Yellow
    Write-Host "`nErsatzweise wird der Programmordner als ZIP gepackt." -ForegroundColor Yellow
    $paket = "dist\Fotosortierer-$version.zip"
    if (Test-Path $paket) { Remove-Item $paket }
    Compress-Archive -Path "dist\Fotosortierer" -DestinationPath $paket
    Write-Host "`nFertig (ohne Setup)." -ForegroundColor Green
    Write-Host "An Kunden weitergeben: $paket" -ForegroundColor Green
    exit 0
}

& $iscc "/DAppVersion=$version" installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno-Setup-Build fehlgeschlagen." }

Write-Host "`nFertig." -ForegroundColor Green
Write-Host "An Kunden weitergeben: dist\Fotosortierer-Setup-$version.exe" -ForegroundColor Green
Write-Host "Der Kunde startet die Datei und folgt dem Assistenten." -ForegroundColor Green
