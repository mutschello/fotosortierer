# -*- mode: python ; coding: utf-8 -*-
"""
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
    datas=heif_datas,
    hiddenimports=heif_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "setuptools", "pip"],
    noarchive=False,
)

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
