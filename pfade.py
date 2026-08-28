r"""
Zentrale Pfad-Verwaltung.

Wichtig für die EXE-/Installer-Variante: Als installiertes Programm liegt die
Anwendung in C:\Program Files\..., das für normale Benutzer nicht beschreibbar
ist. Benutzerdaten (Einstellungen, Adressbuch) gehören daher nach
%APPDATA%\Fotosortierer und nicht neben das Programm.
"""

import os
import shutil
import sys

APP_NAME = "Fotosortierer"


def ist_gebundelt():
    """True, wenn wir als PyInstaller-EXE laufen."""
    return getattr(sys, "frozen", False)


def programm_verzeichnis():
    """Verzeichnis des Programms (EXE-Ordner bzw. Quellcode-Ordner)."""
    if ist_gebundelt():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def ressourcen_verzeichnis():
    """Verzeichnis mitgelieferter Dateien (bei --onefile das Temp-Verzeichnis)."""
    if ist_gebundelt():
        return getattr(sys, "_MEIPASS", programm_verzeichnis())
    return os.path.dirname(os.path.abspath(__file__))


def daten_verzeichnis():
    """
    Beschreibbares Verzeichnis für Benutzerdaten.
    Wird bei Bedarf angelegt.
    """
    basis = os.environ.get("APPDATA") or os.path.expanduser("~")
    pfad = os.path.join(basis, APP_NAME)
    os.makedirs(pfad, exist_ok=True)
    return pfad


def daten_datei(name):
    r"""
    Vollständiger Pfad zu einer Benutzerdatei in %APPDATA%\Fotosortierer.

    Liegt die Datei noch am alten Ort (neben dem Programm, wie in der
    Skript-Version), wird sie einmalig dorthin verschoben, damit bestehende
    Adressbücher und Einstellungen nicht verloren gehen.
    """
    ziel = os.path.join(daten_verzeichnis(), name)
    if not os.path.exists(ziel):
        alt = os.path.join(programm_verzeichnis(), name)
        if os.path.isfile(alt):
            try:
                shutil.move(alt, ziel)
            except Exception:
                try:
                    shutil.copy2(alt, ziel)
                except Exception:
                    return alt
    return ziel
