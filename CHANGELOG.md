# Änderungsverlauf

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [Unveröffentlicht]

## [0.6.4] - 2026-10-25

### Hinzugefügt

- Wirkungsgrad je Fahrzeug und Ladeart als Diagnose-Entitäten `sensor.<fahrzeug>_efficiency_ac` und `_dc`, zusätzlich im Diagnose-Download

## [0.6.3] - 2026-10-25

### Hinzugefügt

- Protokoll aller Ereignisse und Entscheidungen der Erfassung, 90 Tage aufbewahrt, höchstens 20.000 Einträge
- Diagnose-Download mit globalen Einstellungen, Wallbox und Fahrzeugen, laufendem Ladevorgang und Protokoll; Fahrgestellnummer, Kartenkennungen, Kartenbezeichnungen, Adressen und Koordinaten sind entfernt, Kartenkennungen im Protokoll auf die letzten vier Zeichen gekürzt

### Geändert

- `ev_charging.delete_all_data` löscht auch das Protokoll
- Beim Entfernen der Integration werden der Stand des laufenden Ladevorgangs und das Protokoll verworfen; die Ladedaten bleiben erhalten

## [0.6.2] - 2026-10-22

### Hinzugefügt

- Eigenes Symbol der Integration in Home Assistant

### Geändert

- Meldung zum Ladeende nennt Beginn und Ende, bei gleichem Datum mit einem Datum und beiden Uhrzeiten, sowie den Kilometerstand
- Meldung zum Ladeende zeigt den Sonnenanteil in Prozent statt Netz- und Sonnenanteil in kWh
- Meldung zum Ladeende zeigt die Kosten mit Währungssymbol, etwa „4,87 €“
- Meldung zum Ladeende zeigt die Dauer als „Gesamtdauer: 13:28 (netto: 6:52 mit 4 Phasen)“
- Meldung zum Ladefehler nennt Fehler und Quelle, etwa „Ladefehler (Fahrzeug)“, statt eines Gerätecodes
- Live-Karte zeigt einen Ladefehler nur noch, solange er besteht
- Detailliste zeigt keinen Ladefehler mehr an

## [0.6.1] - 2026-10-20

### Hinzugefügt

- Meldung zum Beginn eines Ladevorgangs zu Hause, sobald das Fahrzeug erkannt ist, mit Fahrzeug, Ladestand und Kilometerstand; einzeln abschaltbar

## [0.6.0] - 2026-10-20

### Hinzugefügt

- Entität `binary_sensor.ev_charging_problem`, an, solange Wallbox oder Fahrzeug einen Ladefehler meldet
- Benachrichtigungen in Home Assistant und an bis zu zwei Ziele, etwa die Companion-App
- Meldungen bei Ladeende, externem Ladebeginn und -ende, Ladefehler und offener Nacherfassung, je einzeln abschaltbar, im Abschnitt „Benachrichtigungen“ der globalen Einstellungen
- Meldung, wenn ein Ladevorgang nach 12 Stunden ohne Rückmeldung der Quelle geschlossen wird
- Hinweis unter Reparaturen, wenn ein Benachrichtigungsziel nicht mehr vorhanden ist

### Geändert

- Ein Ladefehler gilt nach 5 Sekunden, auch ohne laufenden Ladevorgang und an jedem Ladeort
- Live-Karte nennt bei einem Ladefehler die Quelle, Wallbox oder Fahrzeug
- Panel: Reiter „Letzte 5“ entfällt, die letzten Ladevorgänge zeigt die Karte `ev-charging-recent-card`
- Panel: Nacherfassung steht oben in der Ansicht „Korrektur“ statt in einem eigenen Reiter
- Panel: Detailliste ohne Monatssummen über der Tabelle
- Panel lädt nach einem Neustart von Home Assistant von selbst neu

## [0.5.6] - 2026-09-30

### Behoben

- Installation neben aktuellen Home-Assistant-Versionen

## [0.5.5] - 2026-09-30

### Behoben

- Wird ein Ladevorgang erst nachträglich über die Karte einem Fahrzeug zugeordnet, werden Ladestand und Kilometerstand bei Beginn ergänzt
- Nach einer Korrektur verschwinden alle Felder aus der Nacherfassung, die nun einen Wert haben
- Korrekturen berechnen die geschätzte Energie richtig
- Nach dem Speichern zeigen alle Ansichten des Panels den aktuellen Stand

## [0.5.4] - 2026-09-25

### Hinzugefügt

- Zusammenführen ausgewählter Ladevorgänge in der Ansicht „Korrektur“, mit Vorschau und Bestätigung, und Service `ev_charging.merge_sessions`

## [0.5.3] - 2026-09-25

### Geändert

- Ein Fahrzeug, das zu Hause einen Ladevorgang meldet, erhält erst nach 90 Sekunden einen eigenen Ladevorgang und nur, wenn die Wallbox es nicht erfasst

### Behoben

- Der Ladevorgang eines Fahrzeugs endet beim Abstecken, auch wenn das Fahrzeug das Abstecken vor der Wallbox meldet
- Die Karten zeigen nicht mehr zeitweise „Custom element doesn't exist“

## [0.5.2] - 2026-09-24

### Geändert

- Für das Fahrzeug an der Wallbox entsteht kein zweiter Ladevorgang mehr
- Der Steckerzustand des Fahrzeugs beendet dessen Ladevorgang
- Zugeordnete Entitäten stehen in den Dialogen im Feld und lassen sich leeren

### Behoben

- Karten laden nach einem Neustart von Home Assistant zuverlässiger

## [0.5.1] - 2026-09-23

### Hinzugefügt

- Panel-Ansichten Nacherfassung und Korrektur: fehlende Werte eintragen, Ladevorgänge bearbeiten oder löschen, Fahrzeug korrigieren, vergangene Ladevorgänge nachtragen
- Services `ev_charging.update_session`, `delete_session`, `create_session`, `close_followup` und `correct_vehicle`, nur für Administratoren

### Geändert

- Wird ein Ladevorgang automatisch nachträglich einem Fahrzeug zugeordnet, werden Ladestand und Kilometerstand bei Beginn aus dem Verlauf ergänzt

## [0.5.0] - 2026-09-22

### Hinzugefügt

- Erfassung von Ladevorgängen über die Fahrzeugintegration: zu Hause ohne Wallbox und unterwegs, auch mehrere gleichzeitig
- Adresse externer Ladevorgänge aus dem Standort des Fahrzeugs
- Service `ev_charging.retry_address`
- Entität `binary_sensor.<fahrzeug>_session_active` sowie deaktivierte Sensoren je Fahrzeug für Zustand, Ladeort, Ladestand, Kilometerstand, Energie, Ladedauer und Ladeende

### Geändert

- Live-Karte zeigt jeden laufenden Ladevorgang in einem eigenen Block
- Live-Karte zeigt ohne Fahrzeug „Kein Fahrzeug an Wallbox verbunden“
- Panel und Karten laden nach einem Verbindungsabbruch von selbst erneut

## [0.4.4] - 2026-09-20

### Geändert

- Live-Karte: kompaktere Darstellung von Fahrzeug, Kilometerstand und Ladestand, zwei Spalten auch auf schmalen Anzeigen
- Live-Karte: voraussichtliches Ende nur, solange geladen wird
- Live-Karte: „Kennung gelesen“ verschwindet, sobald das Fahrzeug angezeigt wird
- Die Wallbox erscheint auf der Seite der Integration nur noch einmal; Entitäten und ihre IDs bleiben erhalten

## [0.4.3] - 2026-09-20

### Geändert

- Die Kartenkennung wird aus der Wallbox gelesen, sobald im Wallbox-Dialog „Kennung aus dem Register der Wallbox lesen“ gewählt ist; ein eigener Schalter entfällt
- Kürzere Beschreibungen im Wallbox-Dialog

## [0.4.2] - 2026-09-20

### Hinzugefügt

- Ausführlichere Debug-Protokollierung

### Geändert

- Meldet die Wallbox nur einen Teil der Kartenkennung, wird er sowohl am Anfang als auch am Ende der hinterlegten Seriennummer gesucht

## [0.4.1] - 2026-09-20

### Hinzugefügt

- Optionales Lesen der Kartenkennung direkt von der KEBA P40 über Modbus TCP, ausschließlich lesend
- Nachträgliche Zuordnung, wenn die Kartenkennung erst später gelesen wird
- Ein Ladevorgang beginnt beim Anstecken, auch wenn noch keine Leistung fließt, und wartet dann im Zustand „pausiert“
- Ansteckvorgänge ohne Ladung werden nicht gespeichert
- Live-Karte zeigt Zustand, Herkunft der Fahrzeugzuordnung, Stand des Kartenlesens und den Grund fehlender Angaben
- Hinweise unter Reparaturen, wenn die Wallbox nicht erreichbar ist oder keine Kennung liefert

### Geändert

- Die Leistungsschwelle beginnt keinen Ladevorgang mehr, sondern öffnet und schließt nur Ladephasen
- Live-Karte zeigt „Fahrzeug wird erkannt“, bis das Fahrzeug feststeht

## [0.4.0] - 2026-09-20

### Hinzugefügt

- Erfassung von Ladevorgängen an der Wallbox mit Ladephasen, Netto-Ladedauer und Pausen
- Netz- und Sonnenanteil sowie Kosten je Ladevorgang
- Fahrzeugzuordnung über Kartenkennung oder Fahrzeugintegration
- Fortsetzung eines laufenden Ladevorgangs nach einem Neustart
- Entitäten für Zustand, Fahrzeug, Kosten, Netz- und Sonnenanteil, Preis und offene Nacherfassungen
- Karten `ev-charging-live-card` und `ev-charging-month-card`
- Hinweise unter Reparaturen bei unbekannter Kennung, Wechsel des Energiezählers und unbekanntem Zustandswert

### Geändert

- Offene Nacherfassungen zeigen das Fahrzeug
- Karten werden nach einem Update zuverlässig neu geladen

## [0.3.10] - 2026-09-19

### Geändert

- Filterleiste oben in Übersicht und Detailliste; die Filter wirken auf alle Summen und Grafiken

## [0.3.9] - 2026-09-19

### Hinzugefügt

- Anzahl der Ladevorgänge in `ev-charging-recent-card` im Kartendialog einstellbar
- Link zu Google Maps hinter der Adresse eines Ladevorgangs

### Geändert

- `ev-charging-recent-card` zeigt die Details aufklappbar
- Jahreszusammenfassung und Monatswerte auf ganze Zahlen gerundet

## [0.3.8] - 2026-09-19

### Hinzugefügt

- Jahreszusammenfassung unter den Monatsbalken, gesamt, intern und extern
- Wert jedes Monats unter seinem Balken
- Kartenfilter mit den hinterlegten Karten

### Geändert

- Energie mit drei Nachkommastellen
- Detailliste als Tabelle, mobil mit einheitlichem Aufbau
- Deutlichere Beschriftungen für Ladeort, Ladeart und Status

## [0.3.7] - 2026-09-19

### Hinzugefügt

- Panel „EV Charging“ mit Übersicht und Detailliste
- Karten `ev-charging-panel-card` und `ev-charging-recent-card`
- Ladevorgänge ohne Fahrzeug erscheinen als „Nicht zugeordnet“
- Geschätzte Werte sind mit ~ gekennzeichnet

## [0.3.6] - 2026-09-18

### Geändert

- Wartung ohne sichtbare Änderung

## [0.3.5] - 2026-09-18

### Hinzugefügt

- Speicherung der Ladevorgänge
- Service `ev_charging.delete_all_data` mit Pflichtbestätigung, nur für Administratoren

## [0.3.4] - 2026-09-17

### Behoben

- Fehler bei der Prüfung der Übersetzungen

## [0.3.3] - 2026-09-17

### Geändert

- Nicht installierte Integrationen stehen im Gerätedialog in einem eingeklappten Abschnitt

### Behoben

- Hinweis zu nicht angebotenen Geräten erscheint in der eingestellten Sprache

## [0.3.2] - 2026-09-17

### Hinzugefügt

- Unterstützung für Škoda mit MySkoda connect
- Steckerzustand des Fahrzeugs als optionale Angabe

### Geändert

- Klarere Feldnamen in Wallbox- und Fahrzeugdialog
- Eigene Auswahl „Fahrzeug ohne Online-Anbindung“

## [0.3.1] - 2026-09-17

### Geändert

- Geräteauswahl nennt auch die Quellintegration

## [0.3.0] - 2026-09-16

### Hinzugefügt

- Unterstützung für zehn Wallboxen und Fahrzeuge, Auswahl des Geräts als erster Schritt im Dialog
- Hinweis auf Geräte, deren Integration fehlt oder zu alt ist

### Geändert

- Die Zuordnung von Zustandswerten von Hand entfällt; das gewählte Gerät ist nach dem Update einmal neu zu wählen

## [0.2.2] - 2026-09-15

### Geändert

- Weniger Einrichtungsschritte für bekannte Geräte
- Einheitlichere Texte in den Dialogen

## [0.2.1] - 2026-09-14

### Behoben

- Fehler beim Laden und in den Übersetzungen

## [0.2.0] - 2026-09-14

### Hinzugefügt

- Zuordnung der Entitäten von Wallbox, Fahrzeug und Stromtarif im Einrichtungsdialog
- Zuordnungen bleiben bei Umbenennung von Entitäten erhalten
- Hinweise unter Reparaturen bei entfernter Entität und geänderter Einheit
- Erkennung eines Fahrzeugs über die Fahrzeugintegration
- Anzeige der zuletzt gemeldeten Kartenkennung im Fahrzeugdialog

### Geändert

- Ein aktives Fahrzeug braucht mindestens eine Karte oder die Erkennung über die Fahrzeugintegration

## [0.1.5] - 2026-09-14

### Hinzugefügt

- Globale Einstellungen, über „Neu konfigurieren“ änderbar
- Hersteller und Modell bei Wallbox und Fahrzeug
- Kartentyp RFID oder eMAID

### Entfernt

- Standardfahrzeug an der Wallbox
- Fester Ladepreis am Fahrzeug

## [0.1.3] - 2026-09-13

### Geändert

- Vereinfachter Wallbox-Dialog mit eingeklappten Expertenoptionen

## [0.1.2] - 2026-09-13

### Hinzugefügt

- Einrichtung und Entfernung der Integration
- Anlegen von Wallbox und Fahrzeugen mit Stammdaten und Karten
- Deutsche und englische Texte
