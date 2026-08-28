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
VERSION = "1.0.0"


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


def build_datum():
    """
    Datum des Builds als "TT.MM.JJJJ".

    Als EXE ist das der Zeitstempel der EXE selbst - den schreibt
    PyInstaller beim Bauen, und Windows behaelt ihn beim Kopieren bei.
    Im Quellcode-Betrieb gibt es keinen Build, daher die neueste
    Aenderung an den Programmdateien.
    """
    from datetime import datetime

    try:
        if ist_gebundelt():
            stempel = os.path.getmtime(sys.executable)
        else:
            ordner = programm_verzeichnis()
            dateien = [
                os.path.join(ordner, n)
                for n in os.listdir(ordner)
                if n.endswith(".py")
            ]
            stempel = max(os.path.getmtime(d) for d in dateien)
        return datetime.fromtimestamp(stempel).strftime("%d.%m.%Y")
    except Exception:
        return "unbekannt"


def titel_zusatz():
    """Versions- und Build-Angabe fuer die Fensterkopfzeile."""
    return "v{} (Build {})".format(VERSION, build_datum())
