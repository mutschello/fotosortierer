<#
    Baut den Foto-Sortierer als Windows-Programm und schnuert daraus
    einen Setup-Assistenten.

    Gebaut wird mit Nuitka, nicht mit PyInstaller: Virenscanner melden
    PyInstaller-Programme regelmaessig als Fehlerkennung, weil alle
    denselben Bootloader enthalten. Nuitka uebersetzt den Python-Code nach
    C und erzeugt eine native EXE ohne diesen gemeinsamen Nenner.

    Aufruf:   .\build.ps1
    Ergebnis: dist\Fotosortierer\ (Programmordner)
              dist\Fotosortierer-Setup-<version>.exe  (zum Weitergeben)

    Benoetigt Inno Setup fuer das Setup:
              winget install --id JRSoftware.InnoSetup
#>

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Keine virtuelle Umgebung gefunden - wird angelegt..." -ForegroundColor Yellow
    py -3.12 -m venv .venv
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt nuitka
}

$version = (Select-String -Path pfade.py -Pattern '^VERSION = "(.+)"').Matches[0].Groups[1].Value
Write-Host "`nFoto-Sortierer $version" -ForegroundColor Cyan

# Die GPL verlangt, dass Empfaenger des Programms auch den Quellcode
# bekommen. Das Archiv wird deshalb vor dem Build gepackt und mit in das
# Programm gelegt. Abrufbar unter Hilfe > Quellcode speichern.
Write-Host "`n[1/3] Packe Quellcode..." -ForegroundColor Cyan
$quellen = @(
    "main.py", "sortier_logik.py", "pfade.py",
    "installer.iss", "version_info.txt", "fotosortierer.ico",
    "build.ps1", "requirements.txt", "ANLEITUNG.md", "LICENSE"
)
$fehlend = $quellen | Where-Object { -not (Test-Path $_) }
if ($fehlend) { throw "Quellcode unvollstaendig, fehlt: $($fehlend -join ', ')" }
if (Test-Path "Quellcode.zip") { Remove-Item "Quellcode.zip" }
Compress-Archive -Path $quellen -DestinationPath "Quellcode.zip"

# Nuitkas Standard-Cache landet unter AppData\Local\Packages\... - ein sehr
# langer, umgeleiteter Containerpfad. gcc findet darueber seine eigenen
# Header nicht (Fehler: structuredquerycondition.h not found), obwohl sie
# vorhanden sind. Ein kurzer Pfad behebt das.
$env:NUITKA_CACHE_DIR = "C:\nuitka-cache"

Write-Host "`n[2/3] Uebersetze mit Nuitka (dauert einige Minuten)..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build_nuitka -ErrorAction SilentlyContinue
& $python -m nuitka `
    --standalone `
    --assume-yes-for-downloads `
    --enable-plugin=tk-inter `
    --include-package=pillow_heif `
    --include-package-data=pillow_heif `
    --include-data-files=Quellcode.zip=Quellcode.zip `
    --windows-console-mode=disable `
    --windows-icon-from-ico=fotosortierer.ico `
    --company-name="Juergen Mutscheller - mutschweb" `
    --product-name="Foto-Sortierer" `
    --file-version=$version.0 `
    --product-version=$version.0 `
    --file-description="Foto-Sortierer fuer Schornsteinfeger" `
    --copyright="(c) 2026 Juergen Mutscheller - mutschweb" `
    --output-dir=build_nuitka `
    --output-filename=Fotosortierer.exe `
    main.py

if ($LASTEXITCODE -ne 0) { throw "Nuitka-Build fehlgeschlagen." }

if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
New-Item -ItemType Directory "dist" | Out-Null
Move-Item "build_nuitka\main.dist" "dist\Fotosortierer"

Write-Host "`n[3/3] Baue Setup mit Inno Setup..." -ForegroundColor Cyan
$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($null -eq $iscc) {
    Write-Host "Inno Setup nicht gefunden - Setup uebersprungen." -ForegroundColor Yellow
    Write-Host "Installieren mit:  winget install --id JRSoftware.InnoSetup" -ForegroundColor Yellow
    Write-Host "`nErsatzweise wird der Programmordner als ZIP gepackt." -ForegroundColor Yellow
    Compress-Archive -Path "dist\Fotosortierer" -DestinationPath "dist\Fotosortierer-$version.zip"
    Write-Host "`nFertig (ohne Setup)." -ForegroundColor Green
    Write-Host "An Kunden weitergeben: dist\Fotosortierer-$version.zip" -ForegroundColor Green
    exit 0
}

& $iscc "/DAppVersion=$version" installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno-Setup-Build fehlgeschlagen." }

Write-Host "`nFertig." -ForegroundColor Green
Write-Host "An Kunden weitergeben: dist\Fotosortierer-Setup-$version.exe" -ForegroundColor Green
Write-Host "Der Kunde startet die Datei und folgt dem Assistenten." -ForegroundColor Green
