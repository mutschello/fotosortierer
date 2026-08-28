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
    # Quellcode.zip wird von build.ps1 vor dem Bauen erzeugt und hier in die
    # EXE gelegt. Die GPL verlangt, dass Empfaenger an den Quellcode kommen -
    # eingebettet bleibt es bei einer einzigen Datei zum Weitergeben.
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Fotosortierer",
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,          # GUI-Programm: kein schwarzes Konsolenfenster
    icon="fotosortierer.ico",
    version="version_info.txt",
)
