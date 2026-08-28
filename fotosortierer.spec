# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller-Beschreibung für den Foto-Sortierer.
Bauen mit:  .venv\Scripts\pyinstaller.exe fotosortierer.spec --noconfirm
"""

from PyInstaller.utils.hooks import collect_all

# pillow-heif bringt native Bibliotheken mit, die PyInstaller sonst übersieht.
heif_datas, heif_binaries, heif_hidden = collect_all("pillow_heif")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=heif_binaries,
    # Quellcode.zip wird von build.ps1 vor dem Bauen erzeugt und hier ins
    # Programmverzeichnis gelegt. Die GPL verlangt, dass Empfaenger an den
    # Quellcode kommen; abrufbar unter Hilfe > Quellcode speichern.
    datas=heif_datas + [("Quellcode.zip", ".")],
    hiddenimports=heif_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "setuptools", "pip"],
    noarchive=False,
)

# Hinweis: libx265 laesst sich nicht aus dem Bundle entfernen. Die
# Erweiterung _pillow_heif.pyd bindet die DLL beim Laden ein - ohne sie
# scheitert bereits der Import, auch wenn nur gelesen und nie gespeichert
# wird. Getestet: Bundle ohne libx265 -> ImportError. Die GPL-2.0 von x265
# ist daher im Ueber-Dialog ausgewiesen.

pyz = PYZ(a.pure)

# Onedir statt Onefile: Im Onefile-Modus entpackt sich die EXE beim Start
# selbst in einen Temp-Ordner und startet sich von dort. Virenscanner werten
# das als Packer-Verhalten - Norton meldete IDP.Generic, eine rein
# heuristische Fehlerkennung. Onedir legt die Dateien offen daneben und
# vermeidet dieses Muster. Weitergegeben wird der Ordner als ZIP.

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,      # Bibliotheken kommen ueber COLLECT daneben
    name="Fotosortierer",
    debug=False,
    strip=False,
    upx=False,
    console=False,              # GUI-Programm: kein schwarzes Konsolenfenster
    icon="fotosortierer.ico",
    version="version_info.txt",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Fotosortierer",
)
