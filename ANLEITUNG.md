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
6. Fotos landen dann in: `Zielordner/<PLZ Ort, Strasse Nr>/<Datum>/` -
   die PLZ steht vorne, damit der Explorer die Haeuser nach
   Kehrbezirk gruppiert statt nach Strassennamen.
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

## Für Kunden: Installation

Endanwender brauchen **kein Python**. Sie bekommen eine einzelne
Installationsdatei `Fotosortierer-Setup-<version>.exe`:

1. Datei doppelklicken
2. Dem Setup-Assistenten folgen
3. Fertig - das Programm liegt im Startmenü und auf dem Desktop

Es werden **keine Administratorrechte** benötigt, es erscheint also kein
UAC-Dialog. Entfernen lässt sich das Programm wie jedes andere über
*Einstellungen > Apps > Installierte Apps*.

Einstellungen und Adressbuch werden unter `%APPDATA%\Fotosortierer\`
gespeichert und bei einer Deinstallation **absichtlich behalten**. Wer von
der Skript-Version umsteigt: eine vorhandene `adressbuch.json` neben dem
Programm wird beim ersten Start automatisch dorthin übernommen.

### Warnungen von Windows und Virenscannern

Das Setup ist nicht signiert. Deshalb kann zweierlei auftreten:

- **SmartScreen** ("Der Computer wurde durch Windows geschützt"): auf
  "Weitere Informationen" klicken, dann "Trotzdem ausführen"
- **Virenscanner** melden unter Umständen einen Fund wie `IDP.Generic`
  oder blockieren den Download. Das sind heuristische Fehlerkennungen,
  keine tatsächlichen Funde

## Lizenz

Der Foto-Sortierer steht unter der **GNU General Public License,
Version 3 oder später**. Der vollständige Lizenztext liegt in der Datei
`LICENSE`.

Das ist keine freiwillige Entscheidung: Die EXE enthält `libx265` unter
GPL-2.0. Diese Bibliothek lässt sich nicht entfernen, weil `pillow-heif`
sie schon beim Laden einbindet - ohne sie wäre keine HEIC-Unterstützung
für iPhone-Fotos möglich.

**Für die Weitergabe bedeutet das:** Wer die EXE bekommt, muss auch den
Quellcode bekommen. Er steckt deshalb in der EXE selbst - abrufbar über
**Hilfe > Quellcode speichern**. Es genügt also, die EXE weiterzugeben;
weitere Dateien sind nicht nötig.

## Für Entwickler: Setup bauen

Auf einem Windows-PC genügt:

```
.\build.ps1
```

Ergebnis ist `dist\Fotosortierer-Setup-<version>.exe` - der
Setup-Assistent zum Weitergeben. Fehlt Inno Setup, packt das Skript
ersatzweise ein ZIP des Programmordners.

Für das Setup wird Inno Setup benötigt:

```
winget install --id JRSoftware.InnoSetup
```

Gebaut wird mit **Nuitka**, das den Python-Code nach C übersetzt. Der
naheliegendere Weg über PyInstaller wurde aufgegeben: Virenscanner
melden dessen Programme regelmäßig als Fehlerkennung, weil alle
PyInstaller-Programme denselben Bootloader enthalten. Bei einem Kunden
verschob Norton die Datei wiederholt in Quarantäne; mit dem
Nuitka-Build trat das nicht mehr auf.

Die C-Übersetzung dauert einige Minuten. Das Setup selbst beschreibt
`installer.iss`.

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
