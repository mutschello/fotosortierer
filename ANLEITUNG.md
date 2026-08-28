# Foto-Sortierer für Schornsteinfeger

Sortiert Fotos automatisch anhand von GPS-Daten in Ordner, die nach der
Hausadresse benannt sind – z.B. für Fotos, die über **Qfile Pro** vom
Handy auf den QNAP-Server geladen werden.

## Funktionsweise (kurz)

1. Alle Fotos in einem Eingangsordner werden eingelesen (auch Unterordner
   von verschiedenen Mitarbeitern/Geräten).
2. Fotos, die geografisch nah beieinander liegen (< 80m), werden als
   "ein Termin/Haus" gruppiert.
3. Aus den GPS-Koordinaten wird über OpenStreetMap automatisch eine
   Adresse ermittelt (kostenlos, benötigt Internetverbindung).
4. Bereits bekannte Häuser werden ab dem zweiten Besuch sofort erkannt
   (lokales Adressbuch, `adressbuch.json`) – dafür ist dann keine
   Internetverbindung mehr nötig.
5. Vor dem Einsortieren zeigt die App alle erkannten Gruppen mit
   Vorschaubildern an. Der Meister kann jede Adresse noch korrigieren,
   bevor die Fotos tatsächlich verschoben werden.
6. Fotos landen dann in: `Zielordner/<Adresse>/<Datum>/`
7. Fotos ohne GPS-Daten werden versucht anhand der Uhrzeit einer
   Gruppe zuzuordnen; falls das nicht möglich ist, landen sie in einer
   Sammelgruppe "Manuell zuordnen".

## Installation

Voraussetzung: [Python 3.10+](https://www.python.org/downloads/) auf dem PC
installiert (Haken bei "Add python.exe to PATH" beim Setup nicht vergessen).

```
pip install pillow pillow-heif
```

## Starten

```
python main.py
```

Beim Start:
1. **Eingangsordner** wählen – der Ordner, in den Qfile Pro auf dem
   Server hochlädt.
2. **Zielordner** wählen – wo die sortierten Fotos landen sollen.
3. "Fotos einlesen und gruppieren" klicken.
4. Die erkannten Gruppen prüfen, Adressen ggf. korrigieren.
5. "Bestätigte Gruppen jetzt einsortieren" klicken.

Ordner- und letzte Pfadangaben werden gemerkt (`einstellungen.json`).

## Als eigenständige .exe (kein Python nötig)

Damit die Mitarbeiter/der Meister die App ohne Python-Installation
starten können, lässt sie sich mit PyInstaller in eine einzelne .exe
packen. Das muss **auf einem Windows-PC** ausgeführt werden:

```
pip install pyinstaller
pyinstaller --onefile --windowed --name FotoSortierer main.py
```

Die fertige Datei liegt danach in `dist\FotoSortierer.exe` und kann
z.B. per Verknüpfung auf den Desktop des Büro-PCs gelegt werden.

## Hinweise & Grenzen

- **GPS erforderlich für Automatik**: Ist bei einem Foto kein GPS
  aktiv gewesen, kann es meist trotzdem über die Uhrzeit einer
  Foto-Gruppe zugeordnet werden, aber nicht immer 100% zuverlässig –
  hier lohnt ein kurzer Blick vor dem Bestätigen.
- **Internetzugang**: Nur für die *erste* Erkennung eines neuen Hauses
  nötig (OpenStreetMap-Abfrage). Bereits bekannte Häuser funktionieren
  auch offline.
- **80-Meter-Radius**: Kann in `sortier_logik.py` über die Konstante
  `GRUPPEN_RADIUS_METER` angepasst werden, falls z.B. Mehrfamilienhäuser
  mit mehreren Eingängen fälschlich getrennt oder benachbarte
  Grundstücke fälschlich zusammengelegt werden.
- **Nichts geht verloren**: Solange nicht auf "einsortieren" bestätigt
  wird, passiert nichts mit den Originaldateien. Mit der Option
  "Fotos kopieren statt verschieben" bleiben zusätzlich auch nach dem
  Sortieren die Originale im Eingangsordner erhalten.
- **Erweiterbar**: Falls es später doch eine digitale Terminliste
  (Adresse + Uhrzeit je Auftrag) geben sollte, lässt sich damit die
  Zuordnung noch zuverlässiger machen (kann bei Bedarf ergänzt werden).
