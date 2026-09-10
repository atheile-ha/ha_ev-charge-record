# ha_ev-charge-record

Home-Assistant-Integration zur Erfassung von Ladevorgängen an einer Wallbox und über die Fahrzeugschnittstelle.

## Funktionsumfang

- Erfassung von Ladevorgängen an der Wallbox mit Fahrzeugzuordnung über RFID oder eMAID
- Erfassung externer Ladevorgänge über die Fahrzeugschnittstelle, mehrere gleichzeitig
- Gliederung eines Steckvorgangs in Ladephasen, Ausweis von Netto-Ladedauer und Pausen
- Ermittlung von Netz- und Sonnenanteil sowie Kosten je Ladevorgang und je Phase
- Liste offener Nacherfassungen für nicht ermittelbare Werte
- Wirkungsgrad je Fahrzeug und Ladeart aus dem eigenen Datenbestand
- Panel für die Historie, Lovelace-Karten für die Live-Ansicht

Die Integration führt keine Steuerung aus.

## Voraussetzungen

- Home Assistant 2026.9 oder neuer
- Wallbox mit Ladeleistung und mindestens einem Energiezähler als Entität
- Optional Fahrzeugentitäten für Ladestand, Kilometerstand, Ladezustand und Standort

Herstellerunabhängig. Die Zuordnung erfolgt über normalisierte Rollen bei der Einrichtung.

## Installation

HACS, benutzerdefiniertes Repository, Kategorie Integration. Anschließend unter Geräte und Dienste hinzufügen.

## Datenhaltung

Ladedaten liegen in `.storage` und sind Teil der Home-Assistant-Sicherung. Beim Entfernen der Integration werden sie nicht gelöscht. Für eine vollständige Entfernung vor der Deinstallation `ev_charging.delete_all_data` aufrufen.

Optional werden Koordinaten externer Ladevorgänge an einen Geocoding-Dienst übermittelt. Abschaltbar.

## Entwicklung

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
pytest
```

```bash
cd frontend && npm install && npm run build
```

Das gebaute Bundle wird committet.

## Änderungen

Siehe `CHANGELOG.md`.

## Lizenz

MIT
