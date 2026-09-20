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
- Wallbox mit Ladeleistung, Steckerzustand und mindestens einem Energiezähler als Entität
- Optional Fahrzeugentitäten für Ladestand, Kilometerstand, Ladezustand und Standort
- Optional Modbus-TCP-Zugriff auf die Wallbox, um die Kennung der RFID-Karte unmittelbar zu lesen (KEBA P40, siehe „Direktes Lesen der Wallbox“)

Herstellerunabhängig. Die Zuordnung erfolgt über normalisierte Rollen bei der Einrichtung.

## Erfassung an der Wallbox

Ein Ladevorgang beginnt, sobald die Ladeleistung die Schwelle der Wallbox überschreitet. Er endet, wenn der Steckerzustand der Wallbox meldet, dass kein Fahrzeug mehr verbunden ist. Ausbleibende Leistung, ein gemeldeter Ladefehler und ein unbekannter Zustandswert beenden ihn nicht. Meldet der Steckerzustand länger als 12 Stunden keinen verwertbaren Wert, wird der Ladevorgang geschlossen und als markiert gekennzeichnet.

- Phasen: Unterbrechungen unter 15 Minuten bleiben Teil der Ladephase, längere Pausen beginnen eine neue Phase. Netto-Ladedauer und Pausen werden ausgewiesen.
- Zustände: `idle`, `candidate`, `charging`, `paused`, `error`, `awaiting_final`. Der Kandidat wird sofort veröffentlicht, die Entprellzeit entscheidet nur, ob der Ladevorgang bestehen bleibt.
- Energie: Beide Energiezähler werden inkrementell akkumuliert. Ein Rückgang gilt als Rücksetzung des Zählers. Ein Zuwachs, den die Wallbox mit der Nennleistung zuzüglich 15 Prozent nicht liefern kann, wird nicht gezählt und markiert den Ladevorgang. Steht der Gesamtzähler während des Ladens still und der Sitzungszähler steigt, wechselt die Erfassung auf den Sitzungszähler und erzeugt eine Repair Issue. Weichen beide Zähler am Ende um mehr als 5 Prozent ab, ist der Ladevorgang markiert.
- Netz- und Sonnenanteil: Aus dem geglätteten Netzsaldo der globalen Einstellungen (Mittel über 60 Sekunden) und der Ladeleistung. Kosten aus Netzpreis und Sonnenbewertung. Ohne Netzsaldo wird die Energie nicht aufgeteilt, ohne Netzpreis werden keine Kosten ermittelt.
- Fahrzeugzuordnung nach `identification_window_s` (Standard 15 Sekunden): erstens über die gemeldete Kennung, die höchstens 5 Minuten alt sein darf und als Ende einer hinterlegten Kennung passen muss, zweitens über genau ein aktives Fahrzeug mit Fahrzeugidentifikation, das den Standort `home` meldet, sonst bleibt der Ladevorgang unzugeordnet. Eine gemeldete Kennung, die kein Fahrzeug hinterlegt hat, führt zu einem unzugeordneten Ladevorgang und einer Repair Issue. Ein unzugeordneter Ladevorgang wird, solange er läuft, dem Fahrzeug zugeordnet, sobald genau ein Fahrzeug mit Fahrzeugidentifikation `charging` meldet; Ladestand und Kilometerstand bei Beginn bleiben dann offen. Widersprechen sich Kennung und Fahrzeugmeldung, gilt die Kennung, und der Ladevorgang ist markiert.
- Neustart: Ein laufender Ladevorgang wird fortgesetzt. Energie, die während des Ausfalls geliefert wurde, geht in die Gesamtmenge ein und wird als nicht zugeordnet ausgewiesen.
- Ladeort ist `home`, die Ladeart die der Wallbox. Meldet der Standort des zugeordneten Fahrzeugs `not_home`, während die Wallbox lädt, erhält der Ladevorgang den Vermerk Standortwiderspruch.

### Entitäten

Alle Entitäten liegen am Gerät „EV Charging“. Sie werden höchstens im Takt von `update_interval_s` fortgeschrieben, ein Zustandswechsel wird sofort veröffentlicht.

| Entität | Inhalt |
|---|---|
| `binary_sensor.ev_charging_wallbox_session` | an, solange ein Kandidat oder Ladevorgang besteht |
| `sensor.ev_charging_wallbox_state` | Zustand des Ladevorgangs |
| `sensor.ev_charging_active_vehicle` | Name des Fahrzeugs, `guest`, `unresolved` oder `none` |
| `sensor.ev_charging_session_cost` | Kosten des Ladevorgangs |
| `sensor.ev_charging_session_energy_grid`, `sensor.ev_charging_session_energy_solar` | Netz- und Sonnenanteil in kWh |
| `sensor.ev_charging_price_effective` | Preis je kWh aus Netz- und Sonnenanteil |
| `sensor.ev_charging_open_followups` | Anzahl offener Nacherfassungen |

Standardmäßig deaktiviert, in der Entitätsverwaltung aktivierbar: `sensor.ev_charging_active_vehicle_soc`, `_soc_target`, `_charge_state`, `_charge_end`, `sensor.ev_charging_session_soc_start`, `_odometer_start`, `_duration_net` und `sensor.ev_charging_grid_share`.

Ohne laufenden Ladevorgang haben die Sensoren des Ladevorgangs keinen Wert. `vin`, Kennungen, Adressen und Koordinaten erscheinen in keiner Entität.

## Panel und Karten

Nach dem Einrichten erscheint in der Seitenleiste das Panel „EV Charging“. Es zeigt die erfassten Ladevorgänge und ist für alle angemeldeten Benutzer lesbar.

- Übersicht: Filter für Fahrzeug, Ladeort, Ladeart, Karte und Status, die auf alle Werte der Übersicht wirken, Monatsauswahl, Monatssummen für Energie, Kosten, Ladedauer, Ladevorgänge und offene Nacherfassungen, Monatsbalken über das Jahr mit dem auf ganze Zahlen gerundeten Wert jedes Monats, darunter die gerundete Jahreszusammenfassung gesamt, intern und extern
- Letzte 5: die jüngsten fünf Ladevorgänge über alle Jahre, aufklappbar für alle Details
- Detailliste: dieselben Filter, darunter die Summen der gefilterten Ladevorgänge und die Ladevorgänge des Monats als Tabelle. Jeder Eintrag lässt sich aufklappen und zeigt Zeiten, Ladestand, Kilometerstand, Netz- und Sonnenanteil, die Ladephasen und einen Link zu Google Maps

Energie wird mit drei Nachkommastellen angezeigt. Intern sind Ladevorgänge zu Hause, mit und ohne Wallbox. Ladevorgänge ohne Fahrzeug werden als „Nicht zugeordnet“ geführt und zählen in die Summen. Ladevorgänge über mehrere Tage werden dem Monat des Ansteckens zugeordnet. Geschätzte Werte sind mit ~ gekennzeichnet.

In der Kartenauswahl eines Dashboards stehen vier Karten zur Verfügung, sie erscheinen unter ihrem Kartentyp:

| Karte | Inhalt |
|---|---|
| `ev-charging-panel-card` | dieselben Ansichten wie das Panel, für eine Dashboard-Ansicht vom Typ Panel |
| `ev-charging-recent-card` | die letzten Ladevorgänge, aufklappbar. Die Anzahl `count` (1 bis 20, Standard 3) lässt sich im Kartendialog oder in YAML einstellen |
| `ev-charging-live-card` | der laufende Ladevorgang: Zustand, Fahrzeug, Ladestand von, bis und Ziel, Leistung, Energie, Netz- und Sonnenanteil, Kosten, Preis je kWh, Ladezeit, Dauer des Ansteckens und voraussichtliches Ende. Sie folgt den Quellentitäten und ist nicht an `update_interval_s` gebunden |
| `ev-charging-month-card` | Energie, Kosten und Sonnenanteil des aktuellen Monats. Der Sonnenanteil zählt die Ladevorgänge, für die Netz- und Sonnenanteil erfasst sind |

## Kennungen (RFID/eMAID)

Beim Fahrzeug wird stets die vollständige, aufgedruckte Seriennummer hinterlegt. Meldet die Wallbox nur einen
Ausschnitt, wie die KEBA P40 mit den letzten vier Bytes der Seriennummer, prüft der Abgleich zur Laufzeit, ob
der gemeldete Ausschnitt das Ende der hinterlegten Kennung bildet. Ein fehlender vorangestellter Teil ist beim
Anlegen der Kennung von Hand zu ergänzen.

## Direktes Lesen der Wallbox (optional)

Stellt keine Quellintegration die Kennung der RFID-Karte bereit, kann die Integration sie unmittelbar aus der Wallbox lesen. Unterstützt ist die KEBA P40 (Register 1500) über Modbus TCP. Das direkte Lesen ist ausgeschaltet, bis es in den Expertenoptionen der Wallbox aktiviert wird.

Einrichtung:

1. Am Gerät Modbus TCP und das Auslesen der Kartenkennung freigeben.
2. Im Wallbox-Dialog unter Expertenoptionen „Wallbox direkt lesen (Modbus TCP)“ aktivieren und Adresse, Port (Standard 502) und Unit-ID (Standard 255) eintragen.
3. Unter Entitätsrollen bei der Kennung „Kennung aus dem Register der Wallbox lesen“ wählen. Eine Kennungs-Entität bleibt dann leer.

Ablauf:

- Gelesen wird ausschließlich mit Funktionscode 3 (Halteregister lesen). Die Integration schreibt nie auf die Wallbox.
- Die Kennung wird einmal beim Beginn eines Ladevorgangs gelesen, nicht zyklisch. Für jeden Lesevorgang wird eine Verbindung aufgebaut und wieder geschlossen.
- Liefert das Gerät keine gültige Antwort oder den Wert 0, wird bis zu dreimal im Abstand von 2 Sekunden wiederholt. Danach gilt die Kennung für diesen Ladevorgang als nicht verfügbar, es entsteht eine Repair Issue, und die Fahrzeugzuordnung folgt den übrigen Möglichkeiten. Der Ladevorgang wird dadurch nie beendet.
- Die Fahrzeugzuordnung wartet auf das Ergebnis des Lesens und gleicht die gelesene Kennung wie eine von einer Entität gemeldete ab.

Hinweise:

- Modbus TCP ist bei der KEBA P40 im Auslieferungszustand abgeschaltet und in der KEBA-eMobility-App freizugeben. Das Auslesen von Kartenkennungen ist dort zusätzlich freizugeben; bis dahin liefert das Register den Wert 0.
- Die Schnittstelle ist nicht verschlüsselt und gehört in ein vertrauenswürdiges Netzsegment.
- Die Wallbox nimmt möglicherweise nur einen Modbus-Client an. Ob ein zweiter Client neben einem Energiemanagement angenommen wird, sichert das Gerätehandbuch nicht zu.
- Softwarestände der KEBA P40 vor 1.2.1 melden die Energieregister im zehnfachen Maßstab.

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
