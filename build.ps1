<#
    Baut den Foto-Sortierer als Windows-Programm und packt ihn zur
    Weitergabe in ein ZIP.

    Gebaut wird mit Nuitka, nicht mit PyInstaller: Virenscanner melden
    PyInstaller-Programme regelmaessig als Fehlerkennung, weil alle
    denselben Bootloader enthalten. Nuitka uebersetzt den Python-Code nach
    C und erzeugt eine native EXE ohne diesen gemeinsamen Nenner.

    Aufruf:   .\build.ps1
    Ergebnis: dist\Fotosortierer\ (Programmordner)
              dist\Fotosortierer-<version>.zip  (zum Weitergeben)
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

# Nuitkas Standard-Cache landet unter AppData\Local\Packages\... - ein sehr
# langer, umgeleiteter Containerpfad. gcc findet darueber seine eigenen
# Header nicht (Fehler: structuredquerycondition.h not found), obwohl sie
# vorhanden sind. Ein kurzer Pfad behebt das.
$env:NUITKA_CACHE_DIR = "C:\nuitka-cache"

Write-Host "`n[1/2] Uebersetze mit Nuitka (dauert einige Minuten)..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build_nuitka -ErrorAction SilentlyContinue
& $python -m nuitka `
    --standalone `
    --assume-yes-for-downloads `
    --enable-plugin=tk-inter `
    --include-package=pi_heif `
    --include-package-data=pi_heif `
    --windows-console-mode=disable `
    --windows-icon-from-ico=fotosortierer.ico `
    --company-name="Juergen Mutscheller - mutschweb" `
    --product-name="Foto-Sortierer" `
    --file-version=$version.0 `
    --product-version=$version.0 `
    --file-description="Foto-Sortierer fuer Handwerksbetriebe" `
    --copyright="(c) 2026 Juergen Mutscheller - mutschweb" `
    --output-dir=build_nuitka `
    --output-filename=Fotosortierer.exe `
    main.py

if ($LASTEXITCODE -ne 0) { throw "Nuitka-Build fehlgeschlagen." }

if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
New-Item -ItemType Directory "dist" | Out-Null
Move-Item "build_nuitka\main.dist" "dist\Fotosortierer"

# Ausgeliefert wird ein ZIP, kein Installer. Virenscanner beanstanden
# selbstentpackende Setup-Dateien als Fehlerkennung - der blosse
# Programmordner im ZIP kommt dagegen durch. Die Desktop-Verknuepfung legt
# das Programm selbst an (Extras > Verknuepfung auf dem Desktop anlegen).
Write-Host "`n[2/2] Packe Programmordner fuer die Weitergabe..." -ForegroundColor Cyan
$paket = "dist\Fotosortierer-$version.zip"
if (Test-Path $paket) { Remove-Item $paket }
Compress-Archive -Path "dist\Fotosortierer" -DestinationPath $paket

Write-Host "`nFertig." -ForegroundColor Green
Write-Host "An Kunden weitergeben: $paket" -ForegroundColor Green
Write-Host "Der Kunde entpackt es und startet Fotosortierer.exe." -ForegroundColor Green
