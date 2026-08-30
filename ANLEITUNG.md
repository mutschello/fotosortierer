# Foto-Sortierer

Sortiert Fotos automatisch anhand von GPS-Daten in Ordner, die nach der
Hausadresse benannt sind. Gedacht für Handwerksbetriebe und kleine
Unternehmen, die ihre Arbeit vor Ort mit Fotos dokumentieren – etwa für
Bilder, die vom Handy auf einen Netzwerkspeicher hochgeladen werden.

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
1. **Eingangsordner** wählen – der Ordner, in den die Fotos auf dem
   Server hochlädt.
2. **Zielordner** wählen – wo die sortierten Fotos landen sollen.
3. "Fotos einlesen und gruppieren" klicken.
4. Die erkannten Gruppen prüfen, Adressen ggf. korrigieren.
5. "Bestätigte Gruppen jetzt einsortieren" klicken.

Ordner- und letzte Pfadangaben werden gemerkt (`einstellungen.json`).

## Für Kunden: Installation

Endanwender brauchen **kein Python**. Sie bekommen ein ZIP-Archiv
`Fotosortierer-<version>.zip`:

1. Archiv herunterladen
2. Mit Rechtsklick auf "Alle extrahieren" entpacken - am besten nach
   `Dokumente` oder an einen anderen dauerhaften Ort
3. Im entpackten Ordner `Fotosortierer.exe` doppelklicken

Beim ersten Start fragt das Programm, ob es ein Symbol auf dem Desktop
anlegen soll. Danach genügt ein Doppelklick auf dieses Symbol. Nachholen
lässt sich das jederzeit über *Extras > Verknüpfung auf dem Desktop
anlegen*.

Das Programm **nicht direkt aus dem ZIP heraus starten** - Windows führt
es dann in einem temporären Ordner aus, in dem es nichts speichern kann.
Der entpackte Ordner darf auch nicht verschoben werden, ohne die
Verknüpfung neu anzulegen.

Einstellungen und Adressbuch werden unter `%APPDATA%\Fotosortierer\`
gespeichert, nicht im Programmordner. Wer von der Skript-Version
umsteigt: eine vorhandene `adressbuch.json` neben dem Programm wird beim
ersten Start automatisch dorthin übernommen.

### Warum kein Installer?

Ein Setup-Assistent wäre bequemer, ist aber nicht praktikabel:
Virenscanner beanstanden selbstentpackende Installationsdateien als
vermeintliche Bedrohung, obwohl nichts Schädliches darin ist. Bei einem
Kunden blockierte Norton das Setup wiederholt, den blossen Programmordner
im ZIP dagegen nicht. Deshalb die Auslieferung als Archiv.

### Warnungen von Windows

Das Programm ist nicht signiert. SmartScreen kann daher melden "Der
Computer wurde durch Windows geschützt" - über "Weitere Informationen"
-> "Trotzdem ausführen" lässt es sich starten.

## Lizenz

Der Foto-Sortierer ist urheberrechtlich geschütztes Eigentum von
Jürgen Mutscheller – mutschweb. Einzelheiten stehen in der Datei
`LICENSE`.

Verwendete Fremdbibliotheken:

| Bibliothek | Lizenz |
|---|---|
| Pillow | MIT-CMU |
| pi-heif | BSD-3-Clause |
| libheif, libde265 | LGPL-3.0 |

Die beiden LGPL-Bibliotheken liegen als eigenständige Dateien im
Programmordner und lassen sich austauschen – damit ist die LGPL erfüllt,
ohne dass der eigene Quellcode offengelegt werden muss.

Bewusst **nicht** verwendet wird `pillow-heif`: Dessen Paket bindet den
x265-Encoder ein, der unter GPL steht und das gesamte Programm unter die
GPL zwingen würde. `pi-heif` ist die Dekodier-Variante desselben
Entwicklers und kommt ohne x265 aus. Da das Programm nie ein Bild
speichert, entsteht dadurch kein Nachteil.

## Für Entwickler: Programm bauen

Auf einem Windows-PC genügt:

```
.\build.ps1
```

Ergebnis ist `dist\Fotosortierer-<version>.zip` - das Archiv zum
Weitergeben.

Gebaut wird mit **Nuitka**, das den Python-Code nach C übersetzt. Der
naheliegendere Weg über PyInstaller wurde aufgegeben: Virenscanner melden
dessen Programme regelmäßig als Fehlerkennung, weil alle
PyInstaller-Programme denselben Bootloader enthalten. Bei einem Kunden
verschob Norton die Datei wiederholt in Quarantäne; mit dem Nuitka-Build
trat das nicht mehr auf.

Ein Setup mit Inno Setup gab es zwischenzeitlich, wurde aber wieder
entfernt - Norton beanstandete den Installer ebenso. Das Skript dafür
steht in der Git-Historie, falls einmal ein Code-Signing-Zertifikat
vorliegt und der Weg wieder gangbar wird.

Die C-Übersetzung dauert einige Minuten.

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
