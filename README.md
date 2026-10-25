# ha_ev-charge-record

Home-Assistant-Integration, die Ladevorgänge von Elektrofahrzeugen erfasst: an der eigenen Wallbox und unterwegs über die Fahrzeugintegration.

## Funktionen

- Erfassung jedes Ladevorgangs an der Wallbox, vom Anstecken bis zum Abstecken, mit Ladephasen, Pausen und Netto-Ladedauer
- Zuordnung zum Fahrzeug über RFID-Karte, eMAID oder die Fahrzeugintegration
- Netz- und Sonnenanteil sowie Kosten je Ladevorgang
- Erfassung von Ladevorgängen zu Hause ohne Wallbox und unterwegs, auch mehrere gleichzeitig, mit Adresse des Ladeorts
- Nacherfassung fehlender Werte und Korrektur gespeicherter Ladevorgänge
- Benachrichtigungen bei Beginn, Ende und Ladefehler
- Panel für die Historie, Karten für das Dashboard

Die Integration erfasst nur. Sie steuert weder Wallbox noch Fahrzeug.

## Voraussetzungen

- Home Assistant 2026.9 oder neuer
- Eine unterstützte Wallbox, eingebunden über ihre Quellintegration
- Optional eine unterstützte Fahrzeugintegration

### Unterstützte Geräte

| Gerät | Quellintegration |
|---|---|
| KEBA KeContact P40 | FENECON FEMS / OpenEMS (`ha_openems`) ab 1.7.2 |
| KEBA KeContact P20 / P30 (UDP) | `ha_openems` ab 1.7.2 |
| Webasto Next | `ha_openems` ab 1.7.2 |
| Spelsberg SMART | `ha_openems` ab 1.7.2 |
| ABL eMH (Modbus) | `ha_openems` ab 1.7.2 |
| Alfen Eve (Modbus) | `ha_openems` ab 1.7.2 |
| Hardy Barth cPH2 / Salia | `ha_openems` ab 1.7.2 |
| Heidelberg Energy Control Connect | `ha_openems` ab 1.7.2 |
| Mennekes Amtron (Modbus) | `ha_openems` ab 1.7.2 |
| Mercedes-Benz mit Mercedes me connect | `mbapi2020` ab 0.29.2 |
| Škoda mit MySkoda connect | `myskoda` ab 1.36.1 |

Fahrzeuge ohne Online-Anbindung lassen sich ebenfalls anlegen.

## Installation

1. In HACS das Repository als benutzerdefiniertes Repository der Kategorie Integration hinzufügen und installieren.
2. Home Assistant neu starten.
3. Unter Einstellungen → Geräte & Dienste die Integration „EV Charging“ hinzufügen.

## Einrichtung

1. **Globale Einstellungen:** Netzstrompreis, Einspeisevergütung, Netzsaldo und Benachrichtigungen. Ohne Netzsaldo wird nicht nach Netz und Sonne aufgeteilt, ohne Netzstrompreis werden keine Kosten ermittelt.
2. **Wallbox:** Gerät wählen und Entitäten für Ladeleistung, Steckerzustand und mindestens einen Energiezähler zuordnen.
3. **Fahrzeuge:** je Fahrzeug Integration, Kapazität und Karten anlegen. Jedes aktive Fahrzeug braucht mindestens eine Karte oder die Erkennung über die Fahrzeugintegration.

Für die RFID-Karte wird immer die vollständige, aufgedruckte Seriennummer eingetragen, auch wenn die Wallbox nur einen Teil davon meldet.

### KEBA P40: Kartenkennung direkt lesen

Die Kennung der RFID-Karte stellt `ha_openems` nicht bereit. Die Integration kann sie lesend über Modbus TCP von der Wallbox holen:

1. In der KEBA-eMobility-App Modbus TCP und das Auslesen der Kartenkennung freigeben.
2. Im Wallbox-Dialog bei der Kennung „Kennung aus dem Register der Wallbox lesen“ wählen.
3. Unter Expertenoptionen Adresse, Port und Unit-ID der Wallbox eintragen.

## Bedienung

**Panel „EV Charging“** in der Seitenleiste: Übersicht mit Monats- und Jahressummen, Detailliste aller Ladevorgänge und, für Administratoren, die Ansicht „Korrektur“ für Nacherfassung, Bearbeiten, Löschen und Zusammenführen.

**Karten** für das Dashboard, in der Kartenauswahl:

| Karte | Inhalt |
|---|---|
| `ev-charging-live-card` | laufende Ladevorgänge mit Fahrzeug, Ladestand, Leistung, Energie und Kosten |
| `ev-charging-recent-card` | die letzten Ladevorgänge |
| `ev-charging-month-card` | Energie, Kosten und Sonnenanteil des aktuellen Monats |
| `ev-charging-panel-card` | das Panel als Dashboard-Ansicht |

**Wichtige Entitäten** für eigene Automationen:

| Entität | Inhalt |
|---|---|
| `binary_sensor.<wallbox>_wallbox_session` | an, solange an der Wallbox ein Ladevorgang besteht |
| `sensor.<wallbox>_wallbox_state` | Zustand des Ladevorgangs an der Wallbox |
| `sensor.<wallbox>_active_vehicle` | erkanntes Fahrzeug |
| `sensor.<wallbox>_session_cost` | Kosten des laufenden Ladevorgangs |
| `binary_sensor.<fahrzeug>_session_active` | an, solange das Fahrzeug außerhalb der Wallbox lädt |
| `binary_sensor.ev_charging_problem` | an bei einem Ladefehler von Wallbox oder Fahrzeug |

Weitere Sensoren sind angelegt, aber standardmäßig deaktiviert.

**Services** (nur für Administratoren): `update_session`, `delete_session`, `create_session`, `close_followup`, `correct_vehicle`, `merge_sessions`, `retry_address`, `delete_all_data`.

## Daten und Datenschutz

- Alle Ladedaten liegen lokal in Home Assistant und sind Teil der Sicherung.
- Beim Entfernen der Integration bleiben die Ladedaten erhalten. Vollständig löschen: vorher `ev_charging.delete_all_data` aufrufen.
- Fahrgestellnummer, Kartenkennungen, Adressen und Koordinaten erscheinen in keiner Entität.
- Die Integration führt ein Protokoll ihrer Ereignisse und Entscheidungen der letzten 90 Tage. Es ist im Diagnose-Download der Integration enthalten (Einstellungen → Geräte & Dienste → EV Charging → Diagnose herunterladen). Fahrgestellnummer, Kartenbezeichnungen, Adressen und Koordinaten sind darin entfernt, Kartenkennungen auf die letzten vier Zeichen gekürzt.
- Für die Adresse externer Ladevorgänge werden Koordinaten an einen Geocoding-Dienst gesendet. Das lässt sich abschalten.

## Lizenz

MIT
