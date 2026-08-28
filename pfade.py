r"""
Zentrale Pfad-Verwaltung.

Wichtig für die EXE-Variante: Wird das Programm in einen nur lesbaren
Ordner gelegt (etwa C:\Program Files\...), kann es dort nichts speichern.
Benutzerdaten (Einstellungen, Adressbuch) gehören daher nach
%APPDATA%\Fotosortierer und nicht neben das Programm.
"""

# Copyright (C) 2026 Jürgen Mutscheller – mutschweb
#
# Dieses Programm ist freie Software: Sie können es unter den Bedingungen
# der GNU General Public License, Version 3 oder (nach Ihrer Wahl) jeder
# späteren Version, weitergeben und/oder verändern.
#
# Die Veröffentlichung erfolgt in der Hoffnung, dass es nützlich ist,
# jedoch OHNE JEDE GEWÄHRLEISTUNG. Einzelheiten stehen in der Datei
# LICENSE, die dem Programm beiliegt.

import os
import shutil
import sys

APP_NAME = "Fotosortierer"
VERSION = "1.1.2"


def ist_gebundelt():
    """
    True, wenn das Programm als fertige EXE laeuft.

    PyInstaller setzt sys.frozen, Nuitka dagegen nicht - dort erkennt man
    den uebersetzten Zustand am globalen __compiled__. Ohne die zweite
    Pruefung hielte sich der Nuitka-Build faelschlich fuer eine
    Quellcode-Ausfuehrung und faende weder Build-Datum noch Beilagen.
    """
    return bool(getattr(sys, "frozen", False)) or "__compiled__" in globals()


def programm_datei():
    """
    Pfad zur laufenden Programmdatei, oder None.

    PyInstaller traegt die EXE in sys.executable ein. Nuitka setzt dort
    einen python.exe-Pfad, den es gar nicht gibt - die echte EXE steht
    bei Nuitka in sys.argv[0]. Deshalb beide Kandidaten pruefen und den
    ersten nehmen, der tatsaechlich existiert.
    """
    for kandidat in (sys.executable, sys.argv[0] if sys.argv else None):
        if kandidat and os.path.isfile(kandidat):
            return kandidat
    return None


def programm_verzeichnis():
    """Verzeichnis des Programms (EXE-Ordner bzw. Quellcode-Ordner)."""
    if ist_gebundelt():
        datei = programm_datei()
        if datei:
            return os.path.dirname(datei)
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
            datei = programm_datei()
            if not datei:
                return "unbekannt"
            stempel = os.path.getmtime(datei)
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
