# Änderungsverlauf

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [Unveröffentlicht]

## [0.3.8] - 2026-09-19

### Hinzugefügt

- Reiter „Letzte 5 Ladevorgänge“ im Panel, mit allen Details aufgeklappt
- Jahreszusammenfassung unter den Monatsbalken für Energie, Kosten, Ladedauer und Ladevorgänge, gesamt, intern und extern
- Der Wert jedes Monats steht unter seinem Balken
- Monatssummen für Energie, Kosten, Ladedauer, Ladevorgänge und offene Nacherfassungen auch über der Detailliste
- Kartenfilter der Detailliste bietet die bei den Fahrzeugen hinterlegten Karten
- Antwort von `ev_charging/vehicles/list` enthält die Karten der Fahrzeuge, Antwort von `ev_charging/sessions/stats` die Jahreszusammenfassung und je Monat die Anzahl offener Nacherfassungen

### Geändert

- Energie wird mit drei Nachkommastellen angezeigt
- Detailliste als Tabelle mit Spaltenüberschriften und ausgerichteten Spalten, in der mobilen Ansicht mit einheitlichem Aufbau je Eintrag
- Beschriftungen der Ladeorte, Ladearten und Status als gefüllte, größere Label
- Die Anzahl offener Nacherfassungen gilt für den gewählten Monat
- Eigene Meldung, wenn Filter alle Ladevorgänge des Monats ausblenden

## [0.3.7] - 2026-09-19

### Hinzugefügt

- Panel „EV Charging“ in der Seitenleiste mit den Ansichten Übersicht (Monatsauswahl, Summen für Energie, Kosten und Ladedauer, Monatsbalken über das Jahr) und Detailliste (Filter für Fahrzeug, Ladeort, Ladeart, Karte und Status, aufklappbare Ladevorgänge mit Phasen)
- Lovelace-Karte `ev-charging-panel-card` mit denselben Ansichten wie das Panel, für eine Dashboard-Ansicht vom Typ Panel
- Lovelace-Karte `ev-charging-recent-card` mit den letzten Ladevorgängen, Einstellung `count` (Standard 3)
- Ladevorgänge ohne Fahrzeug erscheinen als „Nicht zugeordnet“, sind filterbar und zählen in den Summen
- Geschätzte Energiewerte sind mit einer Tilde gekennzeichnet
- WebSocket-Kommandos `ev_charging/sessions/list`, `ev_charging/sessions/stats`, `ev_charging/sessions/open` und `ev_charging/vehicles/list`, für alle angemeldeten Benutzer lesbar
- Frontend-Bundle `ev-charging.js`, ausgeliefert mit der Integrationsversion im Skriptpfad
- `frontend`, `http`, `panel_custom` und `websocket_api` als `after_dependencies` im Manifest

## [0.3.6] - 2026-09-18

### Geändert

- Sicherungskopie vor einer Schemamigration ist jetzt eine eigenständige, unabhängig testbare Funktion

## [0.3.5] - 2026-09-18

### Hinzugefügt

- Datenmodell für Sessions und Ladephasen
- Jahresweise Session-Speicherung mit Schemaversion, Migrationsfunktion und Sicherungskopie vor einer Migration
- Service `delete_all_data` mit Pflichtbestätigung, nur für Administratoren

## [0.3.4] - 2026-09-17

### Behoben

- Übersetzungsstruktur für den Hinweistext zu nicht angebotenen Geräten entsprach nicht dem von `hassfest` geforderten Schema für die Kategorie `selector`

## [0.3.3] - 2026-09-17

### Geändert

- Nicht angebotene Geräte/Integrationen stehen jetzt in einem eingeklappten Abschnitt „Derzeit nicht installierte Integrationen“ am Ende des Gerätedialogs statt im Beschreibungstext

### Behoben

- Hinweistext zu nicht angebotenen Geräten war fest auf Englisch codiert statt aus `translations/` zu kommen

## [0.3.2] - 2026-09-17

### Hinzugefügt

- Mitgelieferte Mapping-Datei für Škoda-Fahrzeuge mit MySkoda connect
- Neue optionale Fahrzeugrolle `plug_state`, klassifiziert wie die gleichnamige Wallbox-Rolle

### Geändert

- Feld „Gerät“ im Wallbox-Dialog umbenannt in „Wallbox“
- Feld „Gerät“ im Fahrzeugdialog umbenannt in „Fahrzeugintegration“, Auswahltext für Mercedes Me gekürzt auf „Mercedes me connect“
- Fahrzeug ohne Online-Anbindung ist jetzt eine eigene Auswahlmöglichkeit („Fahrzeug ohne Online-Anbindung“) statt eines leeren Felds
- Beschreibungstext der Fahrzeugintegration präzisiert

## [0.3.1] - 2026-09-17

### Geändert

- Geräteauswahl nennt neben Hersteller und Modell auch die Quellintegration, etwa „KEBA KeContact P40 (via FENECON FEMS)“

## [0.3.0] - 2026-09-16

### Hinzugefügt

- Mitgelieferte Mapping-Dateien für zehn Geräte (KEBA P40, KEBA P20/P30 über UDP, Webasto Next, Spelsberg SMART, ABL eMH, Alfen Eve, Hardy Barth cPH2/Salia, Heidelberg Energy Control Connect, Mennekes Amtron, Mercedes Me) im Ordner `mappings/`
- Gerätewahl als erster Schritt im Wallbox- und im Fahrzeug-Subentry: Zustandsklassen kommen ausschließlich aus der gewählten Mapping-Datei
- Hinweis im Gerätedialog auf Geräte, deren Quellintegration nicht installiert oder zu alt ist
- Repair Issue, wenn die Quellintegration eines bereits gewählten Geräts unter die Mindestversion fällt

### Geändert

- Der Zuordnungsschritt für Steckerzustand, Fehler, Ladezustand und Ladeart entfällt vollständig; die Klassifikation kommt aus der gewählten Mapping-Datei
- Schemaversion des Config Entrys und der Subentries auf 4 angehoben, bestehende Einträge werden migriert; das gewählte Gerät ist danach neu zu vergeben

### Entfernt

- Presets, Recorder-Abfrage und freie Eingabe zur Ermittlung von Zustandszuordnungen

## [0.2.2] - 2026-09-15

### Geändert

- Der Zuordnungsschritt für Steckerzustand, Fehler, Ladezustand und Ladeart entfällt beim Einrichten vollständig, sobald ein mitgeliefertes Preset die betroffene Entität bereits vollständig abdeckt
- Presets für Steckerzustand, Fehler, Ladezustand und Ladeart tragen die bekannten Rohwerte jetzt einheitlich unter einem eigenen Feld `values`
- Mercedes-Me-Preset liefert damit Ladezustand und Ladeart ohne manuellen Zuordnungsschritt
- Erklärungstexte der Entitätsrollen im Anlegen- und im Bearbeiten-Dialog von Wallbox und Fahrzeug vereinheitlicht
- Beschreibungstexte der Formularfelder enden nicht mehr auf einen Punkt
- Reihenfolge der Kostenmodus-Auswahl im Fahrzeugdialog: Dynamisch vor Fester Preis

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
