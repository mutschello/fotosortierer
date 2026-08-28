"""
Foto-Sortierer für Schornsteinfeger
------------------------------------
Sortiert Fotos vom Server (z.B. QNAP-Ordner, in den Qfile Pro hochlädt)
automatisch anhand der GPS-Daten in Ordner, die nach der Hausadresse benannt sind.

Start: python main.py
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

import sortier_logik as logik

EINSTELLUNGEN_DATEI = "einstellungen.json"


class FotoSortiererApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Foto-Sortierer – Schornsteinfeger")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.eingangsordner = tk.StringVar()
        self.zielordner = tk.StringVar()
        self.kopieren = tk.BooleanVar(value=False)

        self.adressbuch = logik.Adressbuch()
        self.gruppen = []
        self.gruppen_widgets = []  # (frame, entry_var, checkbox_var)

        self._lade_einstellungen()
        self._baue_oberflaeche()

    # -- Einstellungen (Ordnerpfade merken) ---------------------------------

    def _lade_einstellungen(self):
        import json
        if os.path.exists(EINSTELLUNGEN_DATEI):
            try:
                with open(EINSTELLUNGEN_DATEI, "r", encoding="utf-8") as f:
                    daten = json.load(f)
                self.eingangsordner.set(daten.get("eingangsordner", ""))
                self.zielordner.set(daten.get("zielordner", ""))
            except Exception:
                pass

    def _speichere_einstellungen(self):
        import json
        with open(EINSTELLUNGEN_DATEI, "w", encoding="utf-8") as f:
            json.dump({
                "eingangsordner": self.eingangsordner.get(),
                "zielordner": self.zielordner.get(),
            }, f)

    # -- Oberfläche -----------------------------------------------------------

    def _baue_oberflaeche(self):
        # Kopfbereich: Ordnerauswahl
        kopf = ttk.Frame(self, padding=10)
        kopf.pack(fill="x")

        ttk.Label(kopf, text="Eingangsordner (von Qfile Pro / NAS):").grid(row=0, column=0, sticky="w")
        ttk.Entry(kopf, textvariable=self.eingangsordner, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(kopf, text="Wählen...", command=self._waehle_eingangsordner).grid(row=0, column=2)

        ttk.Label(kopf, text="Zielordner (sortierte Fotos):").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(kopf, textvariable=self.zielordner, width=60).grid(row=1, column=1, padx=5, pady=(5, 0))
        ttk.Button(kopf, text="Wählen...", command=self._waehle_zielordner).grid(row=1, column=2, pady=(5, 0))

        ttk.Checkbutton(kopf, text="Fotos kopieren statt verschieben (Original bleibt erhalten)",
                         variable=self.kopieren).grid(row=2, column=1, sticky="w", pady=(5, 0))

        aktionen = ttk.Frame(self, padding=(10, 0))
        aktionen.pack(fill="x")
        self.scan_button = ttk.Button(aktionen, text="1. Fotos einlesen und gruppieren", command=self._starte_scan)
        self.scan_button.pack(side="left")

        self.status_label = ttk.Label(aktionen, text="Bereit.")
        self.status_label.pack(side="left", padx=15)

        # Trennlinie
        ttk.Separator(self).pack(fill="x", pady=8)

        # Scrollbarer Bereich für die erkannten Gruppen
        rahmen = ttk.Frame(self)
        rahmen.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(rahmen, borderwidth=0)
        scrollbar = ttk.Scrollbar(rahmen, orient="vertical", command=canvas.yview)
        self.gruppen_frame = ttk.Frame(canvas)

        self.gruppen_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.gruppen_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Fußbereich: Sortieren-Button
        fuss = ttk.Frame(self, padding=10)
        fuss.pack(fill="x")
        self.sortieren_button = ttk.Button(
            fuss, text="2. Bestätigte Gruppen jetzt einsortieren",
            command=self._starte_sortierung, state="disabled"
        )
        self.sortieren_button.pack(side="right")

    # -- Ordnerauswahl --------------------------------------------------------

    def _waehle_eingangsordner(self):
        pfad = filedialog.askdirectory(title="Eingangsordner wählen")
        if pfad:
            self.eingangsordner.set(pfad)
            self._speichere_einstellungen()

    def _waehle_zielordner(self):
        pfad = filedialog.askdirectory(title="Zielordner wählen")
        if pfad:
            self.zielordner.set(pfad)
            self._speichere_einstellungen()

    # -- Scan & Gruppierung ----------------------------------------------------

    def _starte_scan(self):
        eingang = self.eingangsordner.get().strip()
        if not eingang or not os.path.isdir(eingang):
            messagebox.showerror("Fehler", "Bitte einen gültigen Eingangsordner wählen.")
            return
        self.scan_button.config(state="disabled")
        self.status_label.config(text="Lese Fotos ein...")
        threading.Thread(target=self._scan_arbeiten, args=(eingang,), daemon=True).start()

    def _scan_arbeiten(self, eingang):
        fotos = logik.scanne_ordner(eingang)
        self._setze_status(f"{len(fotos)} Fotos gefunden. Gruppiere...")

        gruppen = logik.gruppiere_fotos(fotos)

        for i, gruppe in enumerate(gruppen, 1):
            self._setze_status(f"Ermittle Adresse für Gruppe {i}/{len(gruppen)}...")
            adresse = logik.bestimme_adresse(gruppe, self.adressbuch)
            gruppe.adresse_vorschlag = adresse

        self.gruppen = gruppen
        self.after(0, self._zeige_gruppen)

    def _setze_status(self, text):
        self.after(0, lambda: self.status_label.config(text=text))

    # -- Gruppen anzeigen und bearbeiten lassen --------------------------------

    def _zeige_gruppen(self):
        for kind in self.gruppen_frame.winfo_children():
            kind.destroy()
        self.gruppen_widgets = []

        if not self.gruppen:
            ttk.Label(self.gruppen_frame, text="Keine Fotos gefunden.").pack(pady=20)
            self.scan_button.config(state="normal")
            self.status_label.config(text="Fertig.")
            return

        for i, gruppe in enumerate(self.gruppen):
            self._baue_gruppen_zeile(i, gruppe)

        self.scan_button.config(state="normal")
        self.sortieren_button.config(state="normal")
        self.status_label.config(text=f"{len(self.gruppen)} Termine erkannt. Bitte prüfen und bestätigen.")

    def _baue_gruppen_zeile(self, index, gruppe):
        zeile = ttk.Frame(self.gruppen_frame, padding=8, relief="groove", borderwidth=1)
        zeile.pack(fill="x", pady=4, padx=4)

        # Vorschaubild (erstes Foto der Gruppe)
        thumb_label = ttk.Label(zeile)
        thumb_label.grid(row=0, column=0, rowspan=3, padx=(0, 10))
        self._lade_thumbnail(gruppe.fotos[0].pfad, thumb_label)

        anzahl = len(gruppe.fotos)
        min_zeit, max_zeit = gruppe.zeitspanne()
        zeit_text = ""
        if min_zeit:
            if min_zeit.date() == max_zeit.date():
                zeit_text = f"{min_zeit.strftime('%d.%m.%Y %H:%M')} – {max_zeit.strftime('%H:%M')} Uhr"
            else:
                zeit_text = f"{min_zeit.strftime('%d.%m.%Y %H:%M')} – {max_zeit.strftime('%d.%m.%Y %H:%M')}"

        ttk.Label(zeile, text=f"{anzahl} Fotos · {zeit_text}", font=("", 9, "italic")).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(zeile, text="Adresse (Zielordner):").grid(row=1, column=1, sticky="w")
        adresse_var = tk.StringVar(value=gruppe.adresse_vorschlag)
        eingabe = ttk.Entry(zeile, textvariable=adresse_var, width=55)
        eingabe.grid(row=2, column=1, sticky="w")

        uebernehmen_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(zeile, text="einsortieren", variable=uebernehmen_var).grid(
            row=2, column=2, padx=10
        )

        ttk.Button(zeile, text="Alle Fotos ansehen",
                   command=lambda g=gruppe: self._zeige_alle_fotos(g)).grid(row=1, column=2, padx=10)

        self.gruppen_widgets.append((gruppe, adresse_var, uebernehmen_var))

    def _lade_thumbnail(self, pfad, label_widget):
        try:
            with Image.open(pfad) as bild:
                bild.thumbnail((100, 100))
                foto_tk = ImageTk.PhotoImage(bild)
                label_widget.image = foto_tk  # Referenz behalten
                label_widget.config(image=foto_tk)
        except Exception:
            label_widget.config(text="(kein Vorschaubild)")

    def _zeige_alle_fotos(self, gruppe):
        fenster = tk.Toplevel(self)
        fenster.title(f"{len(gruppe.fotos)} Fotos")
        fenster.geometry("650x500")

        canvas = tk.Canvas(fenster)
        scrollbar = ttk.Scrollbar(fenster, orient="vertical", command=canvas.yview)
        innen = ttk.Frame(canvas)
        innen.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=innen, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        spalte, reihe = 0, 0
        for foto in gruppe.fotos:
            rahmen = ttk.Frame(innen, padding=4)
            rahmen.grid(row=reihe, column=spalte)
            bild_label = ttk.Label(rahmen)
            bild_label.pack()
            self._lade_thumbnail(foto.pfad, bild_label)
            ttk.Label(rahmen, text=foto.dateiname, font=("", 7)).pack()
            spalte += 1
            if spalte >= 5:
                spalte = 0
                reihe += 1

    # -- Sortieren --------------------------------------------------------------

    def _starte_sortierung(self):
        ziel = self.zielordner.get().strip()
        if not ziel:
            messagebox.showerror("Fehler", "Bitte einen Zielordner wählen.")
            return
        if not os.path.isdir(ziel):
            try:
                os.makedirs(ziel, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Fehler", f"Zielordner konnte nicht erstellt werden: {e}")
                return

        zu_sortieren = []
        for gruppe, adresse_var, uebernehmen_var in self.gruppen_widgets:
            if not uebernehmen_var.get():
                continue
            adresse = adresse_var.get().strip()
            if not adresse:
                messagebox.showerror("Fehler", "Eine Gruppe hat keine Adresse. Bitte eintragen oder Haken entfernen.")
                return
            gruppe.adresse_bestaetigt = adresse
            zu_sortieren.append(gruppe)

        if not zu_sortieren:
            messagebox.showinfo("Hinweis", "Keine Gruppen zum Einsortieren ausgewählt.")
            return

        anzahl_fotos = sum(len(g.fotos) for g in zu_sortieren)
        aktion = "kopiert" if self.kopieren.get() else "verschoben"
        if not messagebox.askyesno(
            "Bestätigen",
            f"{anzahl_fotos} Fotos aus {len(zu_sortieren)} Gruppen werden jetzt {aktion}. Fortfahren?"
        ):
            return

        self.sortieren_button.config(state="disabled")
        threading.Thread(target=self._sortiere_arbeiten, args=(zu_sortieren, ziel), daemon=True).start()

    def _sortiere_arbeiten(self, gruppen, ziel):
        ergebnisse = []
        for gruppe in gruppen:
            zielpfad, dateien = logik.sortiere_gruppe(gruppe, ziel, kopieren=self.kopieren.get())
            ergebnisse.append((zielpfad, len(dateien)))
            # Adresse fürs nächste Mal merken, wenn GPS bekannt war
            if gruppe.lat is not None:
                self.adressbuch.hinzufuegen(gruppe.lat, gruppe.lon, gruppe.adresse_bestaetigt)

        text = "\n".join(f"{n} Fotos → {p}" for p, n in ergebnisse)
        self.after(0, lambda: self._sortierung_fertig(text))

    def _sortierung_fertig(self, text):
        messagebox.showinfo("Fertig", f"Sortierung abgeschlossen:\n\n{text}")
        self.status_label.config(text="Sortierung abgeschlossen.")
        self.gruppen = []
        self.gruppen_widgets = []
        for kind in self.gruppen_frame.winfo_children():
            kind.destroy()
        self.sortieren_button.config(state="disabled")


if __name__ == "__main__":
    app = FotoSortiererApp()
    app.mainloop()
