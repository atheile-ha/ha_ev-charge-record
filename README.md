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

## Panel und Karten

Nach dem Einrichten erscheint in der Seitenleiste das Panel „EV Charging“. Es zeigt die erfassten Ladevorgänge und ist für alle angemeldeten Benutzer lesbar.

- Übersicht: Monatsauswahl, Summen für Energie, Kosten und Ladedauer, Anzahl der Ladevorgänge und der offenen Nacherfassungen, Monatsbalken über das Jahr
- Detailliste: Ladevorgänge des Monats mit Filtern für Fahrzeug, Ladeort, Ladeart, Karte und Status. Jeder Eintrag lässt sich aufklappen und zeigt Zeiten, Ladestand, Kilometerstand, Netz- und Sonnenanteil sowie die Ladephasen

Ladevorgänge ohne Fahrzeug werden als „Nicht zugeordnet“ geführt und zählen in die Summen. Ladevorgänge über mehrere Tage werden dem Monat des Ansteckens zugeordnet. Geschätzte Werte sind mit ~ gekennzeichnet.

In der Kartenauswahl eines Dashboards stehen zwei Karten zur Verfügung, sie erscheinen unter ihrem Kartentyp:

| Karte | Inhalt |
|---|---|
| `ev-charging-panel-card` | dieselben Ansichten wie das Panel, für eine Dashboard-Ansicht vom Typ Panel |
| `ev-charging-recent-card` | die letzten Ladevorgänge, Einstellung `count` (1 bis 20, Standard 3) |

## Kennungen (RFID/eMAID)

Beim Fahrzeug wird stets die vollständige, aufgedruckte Seriennummer hinterlegt. Meldet die Wallbox nur einen
Ausschnitt, wie die KEBA P40 mit den letzten vier Bytes der Seriennummer, prüft der Abgleich zur Laufzeit, ob
der gemeldete Ausschnitt das Ende der hinterlegten Kennung bildet. Ein fehlender vorangestellter Teil ist beim
Anlegen der Kennung von Hand zu ergänzen.

## Installation

HACS, benutzerdefiniertes Repository, Kategorie Integration. Anschließend unter Geräte und Dienste hinzufügen.

## Datenhaltung

Ladedaten liegen in `.storage` und sind Teil der Home-Assistant-Sicherung. Beim Entfernen der Integration werden sie nicht gelöscht. Für eine vollständige Entfernung vor der Deinstallation `ev_charging.delete_all_data` aufrufen.

Optional werden Koordinaten externer Ladevorgänge an einen Geocoding-Dienst übermittelt. Abschaltbar.

## Entwicklung

Python 3.14 oder neuer. Die Testabhängigkeiten setzen eine Linux- oder macOS-Umgebung voraus.

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
pytest
```

```bash
cd frontend && npm install && npm run typecheck && npm test && npm run build
```

Das gebaute Bundle wird committet.

## Änderungen

Siehe `CHANGELOG.md`.

## Lizenz

MIT
