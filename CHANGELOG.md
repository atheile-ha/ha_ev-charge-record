# Änderungsverlauf

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [SemVer](https://semver.org/lang/de/).

## [Unveröffentlicht]

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
