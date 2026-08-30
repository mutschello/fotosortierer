"""
Kernlogik für den Foto-Sortierer.
Enthält: EXIF/GPS-Auslesen, Gruppierung von Fotos zu "Terminen",
Adressbuch-Verwaltung (Cache) und Reverse-Geocoding über OpenStreetMap (Nominatim).
"""

# Copyright (C) 2026 Jürgen Mutscheller – mutschweb
# Alle Rechte vorbehalten.
#
# Dieses Programm nutzt libheif und libde265 unter der LGPL-3.0. Beide
# liegen als eigenstaendige Bibliotheken im Programmordner und koennen
# ausgetauscht werden; ihre Quellen sind auf Anfrage erhaeltlich.

import os
import json
import time
import shutil
import math
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

import pfade

try:
    # pi-heif ist die reine Dekodier-Variante von pillow-heif. Sie bringt
    # libheif und libde265 unter LGPL mit, aber nicht den x265-Encoder, der
    # unter GPL steht. Gelesen wird HEIC damit genauso; gespeichert wird
    # ohnehin nie ein Bild.
    import pi_heif
    pi_heif.register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

BILDENDUNGEN = {".jpg", ".jpeg", ".heic", ".heif", ".png"}

# Fotos, die näher als dieser Radius (Meter) beieinander liegen UND
# nicht mehr als GRUPPEN_MAX_PAUSE auseinander liegen (Zeit), gehören zum selben Termin.
GRUPPEN_RADIUS_METER = 10
GRUPPEN_MAX_PAUSE_MINUTEN = 240  # falls am selben Haus z.B. vormittags+nachmittags fotografiert wird

ADRESSBUCH_DATEI = pfade.daten_datei("adressbuch.json")


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

class Foto:
    def __init__(self, pfad):
        self.pfad = pfad
        self.dateiname = os.path.basename(pfad)
        self.zeit = None       # datetime
        self.lat = None        # float oder None
        self.lon = None        # float oder None

    def hat_gps(self):
        return self.lat is not None and self.lon is not None


class Terminguppe:
    """Eine Gruppe von Fotos, die vermutlich zu einem Haus/Termin gehören."""
    def __init__(self):
        self.fotos = []
        self.lat = None
        self.lon = None
        self.adresse_vorschlag = ""
        self.adresse_bestaetigt = None  # wird vom Nutzer gesetzt

    def mittelpunkt(self):
        pts = [(f.lat, f.lon) for f in self.fotos if f.hat_gps()]
        if not pts:
            return None, None
        lat = sum(p[0] for p in pts) / len(pts)
        lon = sum(p[1] for p in pts) / len(pts)
        return lat, lon

    def zeitspanne(self):
        zeiten = [f.zeit for f in self.fotos if f.zeit]
        if not zeiten:
            return None, None
        return min(zeiten), max(zeiten)


# ---------------------------------------------------------------------------
# EXIF auslesen
# ---------------------------------------------------------------------------

def _konvertiere_gps(wert, ref):
    """Wandelt EXIF-GPS (Grad, Minuten, Sekunden als Tupel) in Dezimalgrad um."""
    try:
        grad, minuten, sekunden = wert
        dezimal = float(grad) + float(minuten) / 60.0 + float(sekunden) / 3600.0
        if ref in ("S", "W"):
            dezimal = -dezimal
        return dezimal
    except Exception:
        return None


def lese_exif(pfad):
    """Liest Aufnahmezeit und GPS-Koordinaten aus einem Foto. Gibt (zeit, lat, lon) zurück."""
    zeit, lat, lon = None, None, None
    try:
        with Image.open(pfad) as bild:
            exif = bild.getexif()
            if not exif:
                exif_daten = {}
            else:
                exif_daten = {TAGS.get(k, k): v for k, v in exif.items()}

            # DateTimeOriginal liegt im Exif-Sub-IFD (0x8769), nicht im Haupt-IFD
            datum_str = exif_daten.get("DateTime")
            if exif:
                try:
                    exif_sub_ifd = exif.get_ifd(0x8769)
                    if exif_sub_ifd:
                        exif_sub = {TAGS.get(k, k): v for k, v in exif_sub_ifd.items()}
                        datum_str = exif_sub.get("DateTimeOriginal") or datum_str
                except Exception:
                    pass
            if datum_str:
                try:
                    zeit = datetime.strptime(str(datum_str), "%Y:%m:%d %H:%M:%S")
                except Exception:
                    zeit = None

            # GPS-Infos liegen in einem separaten IFD
            gps_ifd = exif.get_ifd(0x8825) if exif else None
            if gps_ifd:
                gps_daten = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
                lat_val = gps_daten.get("GPSLatitude")
                lat_ref = gps_daten.get("GPSLatitudeRef")
                lon_val = gps_daten.get("GPSLongitude")
                lon_ref = gps_daten.get("GPSLongitudeRef")
                if lat_val and lon_val:
                    lat = _konvertiere_gps(lat_val, lat_ref)
                    lon = _konvertiere_gps(lon_val, lon_ref)
    except Exception as e:
        print(f"Warnung: Konnte EXIF von {pfad} nicht lesen: {e}")

    # Fallback: Dateiänderungsdatum, falls kein EXIF-Datum vorhanden
    if zeit is None:
        try:
            zeit = datetime.fromtimestamp(os.path.getmtime(pfad))
        except Exception:
            zeit = None

    return zeit, lat, lon


def scanne_ordner(eingangsordner):
    """Durchsucht rekursiv einen Ordner nach Fotos und liest deren EXIF-Daten."""
    fotos = []
    for wurzel, _, dateien in os.walk(eingangsordner):
        for name in dateien:
            ext = os.path.splitext(name)[1].lower()
            if ext in BILDENDUNGEN:
                voller_pfad = os.path.join(wurzel, name)
                f = Foto(voller_pfad)
                f.zeit, f.lat, f.lon = lese_exif(voller_pfad)
                fotos.append(f)
    return fotos


# ---------------------------------------------------------------------------
# Gruppierung
# ---------------------------------------------------------------------------

def _distanz_meter(lat1, lon1, lat2, lon2):
    """Haversine-Formel für Distanz zwischen zwei GPS-Punkten in Metern."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def gruppiere_fotos(fotos):
    """
    Gruppiert Fotos anhand GPS-Nähe zu Terminguppen.
    Fotos ohne GPS werden separat zurückgegeben (zeitliche Zuordnung erfolgt in _ordne_gps_lose_zu).
    """
    fotos_mit_gps = [f for f in fotos if f.hat_gps()]
    fotos_ohne_gps = [f for f in fotos if not f.hat_gps()]

    # Nach Zeit sortieren, damit Zeit-Lücken sinnvoll ausgewertet werden können
    fotos_mit_gps.sort(key=lambda f: f.zeit or datetime.min)

    gruppen = []
    for foto in fotos_mit_gps:
        passende_gruppe = None
        for gruppe in gruppen:
            g_lat, g_lon = gruppe.mittelpunkt()
            if g_lat is None:
                continue
            dist = _distanz_meter(foto.lat, foto.lon, g_lat, g_lon)
            if dist <= GRUPPEN_RADIUS_METER:
                # zusätzlich prüfen, ob zeitlich plausibel (nicht zwei Besuche Wochen auseinander)
                _, g_max_zeit = gruppe.zeitspanne()
                if foto.zeit and g_max_zeit:
                    pause = abs((foto.zeit - g_max_zeit).total_seconds()) / 60
                    if pause > GRUPPEN_MAX_PAUSE_MINUTEN:
                        continue
                passende_gruppe = gruppe
                break
        if passende_gruppe is None:
            passende_gruppe = Terminguppe()
            gruppen.append(passende_gruppe)
        passende_gruppe.fotos.append(foto)

    for gruppe in gruppen:
        gruppe.lat, gruppe.lon = gruppe.mittelpunkt()

    _ordne_gps_lose_zu(gruppen, fotos_ohne_gps)

    return gruppen


def _ordne_gps_lose_zu(gruppen, fotos_ohne_gps):
    """Versucht Fotos ohne GPS anhand der Aufnahmezeit der nächstgelegenen Gruppe zuzuordnen."""
    unzugeordnet = []
    for foto in fotos_ohne_gps:
        if not foto.zeit or not gruppen:
            unzugeordnet.append(foto)
            continue
        beste_gruppe = None
        beste_differenz = None
        for gruppe in gruppen:
            g_min, g_max = gruppe.zeitspanne()
            if not g_min:
                continue
            if g_min <= foto.zeit <= g_max:
                diff = 0
            else:
                diff = min(abs((foto.zeit - g_min).total_seconds()),
                           abs((foto.zeit - g_max).total_seconds()))
            if diff <= 20 * 60 and (beste_differenz is None or diff < beste_differenz):
                beste_differenz = diff
                beste_gruppe = gruppe
        if beste_gruppe:
            beste_gruppe.fotos.append(foto)
        else:
            unzugeordnet.append(foto)

    if unzugeordnet:
        sammel_gruppe = Terminguppe()
        sammel_gruppe.fotos = unzugeordnet
        sammel_gruppe.adresse_vorschlag = "Manuell zuordnen (kein GPS)"
        gruppen.append(sammel_gruppe)


# ---------------------------------------------------------------------------
# Adressbuch (lokaler Cache, damit nicht jedes Mal online nachgefragt werden muss)
# ---------------------------------------------------------------------------

class Adressbuch:
    def __init__(self, pfad=ADRESSBUCH_DATEI):
        self.pfad = pfad
        self.eintraege = []  # Liste von {lat, lon, adresse}
        self._laden()

    def _laden(self):
        if os.path.exists(self.pfad):
            try:
                with open(self.pfad, "r", encoding="utf-8") as f:
                    self.eintraege = json.load(f)
            except Exception:
                self.eintraege = []
            self._format_umstellen()

    def _format_umstellen(self):
        """
        Stellt Eintraege aus dem alten Format ("Strasse Nr, PLZ Ort") einmalig
        auf das neue um. Laeuft still im Hintergrund, damit bekannte Haeuser
        nach einem Update nicht weiter Ordner im alten Format erzeugen.
        """
        geaendert = False
        for eintrag in self.eintraege:
            alt = eintrag.get("adresse", "")
            neu = adresse_ins_neue_format(alt)
            if neu != alt:
                eintrag["adresse"] = neu
                geaendert = True
        if geaendert:
            try:
                self.speichern()
            except Exception:
                pass  # Umstellung greift dann beim naechsten Start erneut

    def speichern(self):
        with open(self.pfad, "w", encoding="utf-8") as f:
            json.dump(self.eintraege, f, ensure_ascii=False, indent=2)

    def suche(self, lat, lon, radius=GRUPPEN_RADIUS_METER):
        for eintrag in self.eintraege:
            dist = _distanz_meter(lat, lon, eintrag["lat"], eintrag["lon"])
            if dist <= radius:
                return eintrag["adresse"]
        return None

    def hinzufuegen(self, lat, lon, adresse):
        if self.suche(lat, lon) is None:
            self.eintraege.append({"lat": lat, "lon": lon, "adresse": adresse})
            self.speichern()


# ---------------------------------------------------------------------------
# Reverse-Geocoding über OpenStreetMap Nominatim (kostenlos, aber rate-limited)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Adressformat
#
# Ordnernamen lauten "PLZ Ort, Strasse Hausnummer". Die PLZ steht vorne, damit
# der Explorer die Haeuser nach Postleitzahl - also nach Kehrbezirk - gruppiert
# statt nach Strassennamen. Der Ort bleibt im Namen, weil eine PLZ mehrere
# Ortsteile umfassen kann und sonst zwei verschiedene Haeuser im selben Ordner
# landen koennten.
# ---------------------------------------------------------------------------

def adresse_formatieren(strasse, hausnr, plz, ort):
    """Baut die Adresszeile. Fehlende Bestandteile werden ausgelassen."""
    ortsteil = " ".join(t for t in (str(plz).strip(), str(ort).strip()) if t)
    strassenteil = " ".join(t for t in (str(strasse).strip(), str(hausnr).strip()) if t)
    return ", ".join(t for t in (ortsteil, strassenteil) if t)


def adresse_ins_neue_format(adresse):
    """
    Wandelt eine Adresse aus dem alten Format ("Strasse Nr, PLZ Ort") in das
    neue ("PLZ Ort, Strasse Nr") um.

    Noetig fuer bestehende Adressbuecher: dort stehen fertige Adresszeilen, die
    direkt als Ordnername dienen. Ohne Umstellung wuerden bekannte Haeuser
    weiterhin Ordner im alten Format erzeugen.

    Bereits umgestellte oder unbekannte Schreibweisen bleiben unveraendert.
    """
    if not adresse or "," not in adresse:
        return adresse

    vorne, hinten = [t.strip() for t in adresse.split(",", 1)]
    if not vorne or not hinten:
        return adresse

    # Steht vorne schon eine Postleitzahl, ist nichts zu tun.
    if vorne.split(" ", 1)[0].isdigit():
        return adresse

    # Sonst gilt das alte Format, sobald hinten eine PLZ steht.
    if hinten.split(" ", 1)[0].isdigit():
        return f"{hinten}, {vorne}"

    return adresse


_LETZTE_ANFRAGE = [0.0]

def reverse_geocode(lat, lon):
    """Wandelt GPS-Koordinaten in eine Adresse um. Gibt None bei Fehler/keiner Internetverbindung zurück."""
    # Nominatim erlaubt max. 1 Anfrage/Sekunde
    verstrichen = time.time() - _LETZTE_ANFRAGE[0]
    if verstrichen < 1.1:
        time.sleep(1.1 - verstrichen)
    _LETZTE_ANFRAGE[0] = time.time()

    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode({
        "format": "jsonv2",
        "lat": lat,
        "lon": lon,
        "zoom": 18,
        "addressdetails": 1,
    })
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Fotosortierer/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            daten = json.loads(resp.read().decode("utf-8"))
        adr = daten.get("address", {})
        adresse = adresse_formatieren(
            strasse=adr.get("road", ""),
            hausnr=adr.get("house_number", ""),
            plz=adr.get("postcode", ""),
            ort=adr.get("city") or adr.get("town") or adr.get("village") or adr.get("municipality", ""),
        ) or daten.get("display_name", "")
        return adresse or None
    except Exception as e:
        print(f"Warnung: Reverse-Geocoding fehlgeschlagen: {e}")
        return None


def bestimme_adresse(gruppe, adressbuch):
    """Ermittelt für eine Terminguppe eine Adresse: erst lokales Adressbuch, dann Online-Geocoding."""
    if gruppe.lat is None:
        return gruppe.adresse_vorschlag or "Manuell zuordnen (kein GPS)"

    bekannt = adressbuch.suche(gruppe.lat, gruppe.lon)
    if bekannt:
        return bekannt

    online = reverse_geocode(gruppe.lat, gruppe.lon)
    if online:
        return online

    return f"Unbekannt (GPS {gruppe.lat:.5f}, {gruppe.lon:.5f})"


# ---------------------------------------------------------------------------
# Dateien einsortieren
# ---------------------------------------------------------------------------

def _sicherer_ordnername(name):
    """Entfernt Zeichen, die in Windows-Ordnernamen verboten sind."""
    verboten = '<>:"/\\|?*'
    for z in verboten:
        name = name.replace(z, "-")
    return name.strip().strip(".") or "Unbekannt"


def sortiere_gruppe(gruppe, zielordner, kopieren=False):
    """Verschiebt (oder kopiert) alle Fotos einer Gruppe in Zielordner/Adresse/Datum/."""
    adresse = _sicherer_ordnername(gruppe.adresse_bestaetigt or gruppe.adresse_vorschlag)
    datum_min, _ = gruppe.zeitspanne()
    datum_str = datum_min.strftime("%Y-%m-%d") if datum_min else "unbekanntes-datum"

    zielpfad = os.path.join(zielordner, adresse, datum_str)
    os.makedirs(zielpfad, exist_ok=True)

    verschoben = []
    for foto in gruppe.fotos:
        ziel_datei = os.path.join(zielpfad, foto.dateiname)
        # Namenskollision vermeiden
        zaehler = 1
        basis, ext = os.path.splitext(foto.dateiname)
        while os.path.exists(ziel_datei):
            ziel_datei = os.path.join(zielpfad, f"{basis}_{zaehler}{ext}")
            zaehler += 1
        if kopieren:
            shutil.copy2(foto.pfad, ziel_datei)
        else:
            shutil.move(foto.pfad, ziel_datei)
        verschoben.append(ziel_datei)

    return zielpfad, verschoben
