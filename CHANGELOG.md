# Änderungsverlauf

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [Unveröffentlicht]

## [0.2.2] - 2026-09-15

### Geändert

- Der Zuordnungsschritt für Steckerzustand, Fehler, Ladezustand und Ladeart entfällt beim Einrichten vollständig, sobald ein mitgeliefertes Preset die betroffene Entität bereits vollständig abdeckt
- Presets für Steckerzustand, Fehler, Ladezustand und Ladeart tragen die bekannten Rohwerte jetzt einheitlich unter einem eigenen Feld `values`
- Mercedes-Me-Preset liefert damit Ladezustand und Ladeart ohne manuellen Zuordnungsschritt
- Erklärungstexte der Entitätsrollen im Anlegen- und im Bearbeiten-Dialog von Wallbox und Fahrzeug vereinheitlicht
- Beschreibungstexte der Formularfelder enden nicht mehr auf einen Punkt

### Behoben

- Erklärungstext des Kostenmodus erscheint im Fahrzeugdialog jetzt direkt unter dem Feld statt nach der ausgewählten Option

## [0.2.1] - 2026-09-14

### Behoben

- `recorder` als `after_dependencies` im Manifest eingetragen
- Auswahlwert „noch nicht klassifiziert“ in den Zuordnungsschritten auf einen gültigen Übersetzungsschlüssel umbenannt

## [0.2.0] - 2026-09-14

### Hinzugefügt

- Entitätsrollen für Wallbox, Fahrzeug und Hauptentry, zuordenbar über den Config Flow: Ladeleistung, Energiezähler, Steckerzustand, Kennung und Fehler an der Wallbox; Ladezustand, Ladeart, Ladestand, Kilometerstand, Standort, Ladeende, Reichweite und Sessionenergie am Fahrzeug; Netzsaldo, Netzbezug, Netzeinspeisung sowie Netz- und Einspeisepreis am Hauptentry
- Zustandsmapping für Steckerzustand, Fehler, Ladezustand und Ladeart: Voreinstellung aus mitgelieferten Presets, Ergänzung um die über den Recorder real aufgetretenen Werte, freie Eingabe
- Presets für die OpenEMS-Anbindung der KEBA P40 und für Mercedes Me
- Fehlerrolle der Wallbox akzeptiert einen `binary_sensor` mit `device_class: problem` oder eine beliebige Zustandsentität mit eigenem Mapping
- Auflösung von Entitätsrollen über die Entity-Registry-Eintrags-ID, mit Rückfall auf die `entity_id` für Entitäten ohne Registry-Eintrag
- Repair Issue bei entfernter Rollenentität und bei geänderter Einheit
- Schalter „Identifikation über die Fahrzeugintegration“ am Fahrzeug, wählbar bei zugeordnetem Ladezustand und Standort
- Hinweis im Fahrzeugdialog auf den aktuell von der Wallbox gemeldeten Kennungswert
- Abschnitt zu Kennungen in der README

### Geändert

- Ein aktives Fahrzeug benötigt mindestens eine Karte oder die Identifikation über die Fahrzeugintegration
- Kartentyp-Auswahl im Fahrzeugdialog verwendet feste Beschriftungen „RFID“ und „EMAID“
- Schemaversion des Config Entrys und der Subentries auf 3 angehoben, bestehende Einträge werden migriert

## [0.1.5] - 2026-09-14

### Hinzugefügt

- Globale Einstellungen am Hauptentry: Veröffentlichungsintervall, Sonnenbewertung, Geocoding-Aktivierung, Geocoding-URL, Geocoding-Kontaktangabe, Schwelle für unsichere Schätzung. Bearbeitbar über „Neu konfigurieren“
- Erkennungsfenster im Wallbox-Dialog
- Hersteller und Modell im Wallbox- und im Fahrzeugdialog
- Kartentyp (RFID oder eMAID) je Karteneintrag
- Ablehnung der Werte `0`, `unknown`, `unavailable` und der leeren Zeichenkette als Kartenkennung

### Geändert

- Startentprellung der Wallbox: Standardwert 2 Sekunden, Bereich 0 bis 30 Sekunden, umbenannt in „Entprellzeit Sessionsstart“
- Erklärungstext des Erkennungsfensters präzisiert
- Erklärungstext des Gastfahrzeug-Felds präzisiert
- Kostenmodus am Fahrzeug ist vorgemerkt und wirkt sich nicht auf die Erfassung aus, Erklärungstext direkt am Feld
- Beschriftung „Dynamisch“ beim Kostenmodus präzisiert
- Kartentyp-Auswahl zeigt „RFID“ und „EMAID“ in Großschreibung
- Feld „Kennung“ der Freischalt-Referenz umbenannt in „Kennung / Seriennummer“
- Schemaversion des Config Entrys und der Subentries auf 2 angehoben, bestehende Einträge werden migriert

### Entfernt

- Standardfahrzeug-Feld am Wallbox-Subentry
- Fester Ladepreis und Sonnenbewertung am Fahrzeug-Subentry

## [0.1.3] - 2026-09-13

### Hinzugefügt

- Zweiter Schritt im Fahrzeugdialog: je nach Kostenmodus wird nur noch der fixe Ladepreis oder nur die Sonnenbewertung abgefragt

### Geändert

- Wallbox-Dialog auf Name, Stromart und maximale Leistung reduziert; Leistungsschwelle und Startentprellung stehen unter „Expertenoptionen“, eingeklappt
- Beschriftung des Kostenmodus im Fahrzeugformular korrigiert
- Kartenfeld im Fahrzeugformular umbenannt in „Freischalt-Referenz“, mit Erklärung zu RFID/eMAID

### Entfernt

- Konfigurierbarkeit von Mindestpause und maximalem Alter der Kennung der Wallbox; diese Werte sind fest
- Auswahl eines Standardfahrzeugs im Wallbox-Dialog, bis Entitätsrollen umgesetzt sind

## [0.1.2] - 2026-09-13

### Hinzugefügt

- Projektgerüst, CI-Konfiguration, Frontend-Werkzeugkette
- Einrichtung und Entfernung der Integration über den Config Flow, genau ein Eintrag je Instanz
- Deutsche und englische Texte des Einrichtungsdialogs
- Wallbox-Subentry mit Stammdaten, auf eine Instanz begrenzt
- Fahrzeug-Subentry mit Stammdaten, Kartenverwaltung und fortlaufenden, nie wiederverwendeten IDs
- Prüfung von Kartenkennungen gegen aktive Fahrzeuge samt Normalisierung
- Deutsche und englische Texte der Wallbox- und Fahrzeugdialoge
- Kartenverwaltung als einzelnes Feld im Fahrzeugformular, ohne eigenen Dialogschritt
- Automatisches Entfernen der Kennungen beim Inaktivsetzen eines Fahrzeugs, Pflicht zur Neuvergabe bei Reaktivierung
- Kostenmodus je Fahrzeug: fester Preis für den gesamten Ladevorgang oder dynamische Bewertung von Netz- und Sonnenanteil

### Geändert

- Sessions der Wallbox werden ausschließlich über den Steckerzustand begrenzt, nicht mehr über eine wählbare Strategie
- Der feste Sonnenpreis ist jetzt ein fester Gesamtpreis für den Ladevorgang und Teil des Kostenmodus, nicht mehr eine Ausprägung der Sonnenbewertung

### Entfernt

- Konfigurierbarkeit von Nachlauf auf Endwerte, Fehlerentprellung und Session-Timeout der Wallbox; diese Werte sind fest

### Behoben

- Fehlende Menütexte für das Anlegen und Bearbeiten von Wallbox- und Fahrzeug-Subentries in allen Sprachdateien ergänzt
- Übersetzungsverweise, die zur Laufzeit nicht aufgelöst wurden, durch den tatsächlichen Text ersetzt
