<#
    Baut den Foto-Sortierer mit Nuitka statt PyInstaller.

    Hintergrund: Virenscanner melden PyInstaller-Programme regelmaessig als
    Fehlerkennung, weil alle denselben Bootloader enthalten. Nuitka
    uebersetzt den Python-Code nach C und erzeugt eine echte native EXE
    ohne diesen gemeinsamen Nenner.

    Aufruf:   .\build_nuitka.ps1
    Ergebnis: dist_nuitka\Fotosortierer\Fotosortierer.exe
#>

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = ".\.venv\Scripts\python.exe"
$version = (Select-String -Path pfade.py -Pattern '^VERSION = "(.+)"').Matches[0].Groups[1].Value

# Quellcode-Archiv wie beim PyInstaller-Build erzeugen (GPL-Pflicht).
Write-Host "`nPacke Quellcode..." -ForegroundColor Cyan
$quellen = @(
    "main.py", "sortier_logik.py", "pfade.py",
    "fotosortierer.spec", "installer.iss", "version_info.txt", "fotosortierer.ico",
    "build.ps1", "build_nuitka.ps1", "requirements.txt", "ANLEITUNG.md", "LICENSE"
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

Write-Host "`nUebersetze mit Nuitka (dauert einige Minuten)..." -ForegroundColor Cyan
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

# Ergebnis an einen aufgeraeumten Ort legen
if (Test-Path "dist_nuitka") { Remove-Item -Recurse -Force "dist_nuitka" }
New-Item -ItemType Directory "dist_nuitka" | Out-Null
Move-Item "build_nuitka\main.dist" "dist_nuitka\Fotosortierer"

Write-Host "`nFertig: dist_nuitka\Fotosortierer\Fotosortierer.exe" -ForegroundColor Green
