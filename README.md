# ha_ev-charge-record

Home Assistant integration that records charging sessions of electric vehicles: at your own wallbox, and on the road through the vehicle integration.

## Features

- Records every charging session at the wallbox, from plugging in to unplugging, with charging phases, pauses and net charging time
- Assigns the session to a vehicle by RFID card, eMAID or the vehicle integration
- Grid and solar share as well as cost per charging session
- Records sessions at home without a wallbox and on the road, also several at the same time, with the address of the charging location
- Follow-up entry of missing values and correction of stored sessions
- Notifications on start, end and charging errors
- Panel for the history, cards for the dashboard

The integration only records. It does not control the wallbox or the vehicle.

## Requirements

- Home Assistant 2026.9 or newer
- A supported wallbox, connected through its source integration
- Optionally a supported vehicle integration

### Supported devices

| Device | Source integration |
|---|---|
| KEBA KeContact P40 | FENECON FEMS / OpenEMS (`ha_openems`) 1.7.2 or newer |
| KEBA KeContact P20 / P30 (UDP) | `ha_openems` 1.7.2 or newer |
| Webasto Next | `ha_openems` 1.7.2 or newer |
| Spelsberg SMART | `ha_openems` 1.7.2 or newer |
| ABL eMH (Modbus) | `ha_openems` 1.7.2 or newer |
| Alfen Eve (Modbus) | `ha_openems` 1.7.2 or newer |
| Hardy Barth cPH2 / Salia | `ha_openems` 1.7.2 or newer |
| Heidelberg Energy Control Connect | `ha_openems` 1.7.2 or newer |
| Mennekes Amtron (Modbus) | `ha_openems` 1.7.2 or newer |
| Mercedes-Benz with Mercedes me connect | `mbapi2020` 0.29.2 or newer |
| Škoda with MySkoda connect | `myskoda` 1.36.1 or newer |

Vehicles without an online connection can be added as well.

## Installation

1. In HACS, add the repository as a custom repository of the category Integration and install it.
2. Restart Home Assistant.
3. Under Settings → Devices & services, add the integration "EV Charging".

## Setup

1. **Global settings:** grid electricity price, feed-in tariff, grid balance and notifications. Without the grid balance, sessions are not split into grid and solar share; without the grid electricity price, no costs are determined.
2. **Wallbox:** choose the device and assign entities for charging power, plug state and at least one energy counter.
3. **Vehicles:** for each vehicle, add the integration, capacity and cards. Every active vehicle needs at least one card or detection through the vehicle integration.

For the RFID card, always enter the complete serial number printed on the card, even if the wallbox reports only a part of it.

### KEBA P40: read the card identification directly

`ha_openems` does not provide the identification of the RFID card. The integration can read it from the wallbox over Modbus TCP, read-only:

1. In the KEBA eMobility app, enable Modbus TCP and reading of the card identification.
2. In the wallbox dialog, select "Read identification from the wallbox register" for the identification.
3. Under Expert options, enter the address, port and unit ID of the wallbox.

## Usage

**Panel "EV Charging"** in the sidebar: overview with monthly and yearly totals, a detail list of all charging sessions and, for administrators, the "Correction" view for follow-up entry, editing, deleting and merging.

**Cards** for the dashboard, in the card picker:

| Card | Content |
|---|---|
| `ev-charging-live-card` | running charging sessions with vehicle, state of charge, power, energy and cost |
| `ev-charging-recent-card` | the most recent charging sessions |
| `ev-charging-month-card` | energy, cost and solar share of the current month |
| `ev-charging-panel-card` | the panel as a dashboard view |

**Important entities** for your own automations:

| Entity | Content |
|---|---|
| `binary_sensor.<wallbox>_wallbox_session` | on while a charging session exists at the wallbox |
| `sensor.<wallbox>_wallbox_state` | state of the charging session at the wallbox |
| `sensor.<wallbox>_active_vehicle` | detected vehicle |
| `sensor.<wallbox>_session_cost` | cost of the running charging session |
| `binary_sensor.<vehicle>_session_active` | on while the vehicle charges away from the wallbox |
| `binary_sensor.ev_charging_problem` | on while the wallbox or the vehicle reports a charging error |
| `sensor.<vehicle>_efficiency_ac`, `sensor.<vehicle>_efficiency_dc` | efficiency of the vehicle per charge type (diagnostic) |

Further sensors are created but disabled by default.

**Services** (administrators only): `update_session`, `delete_session`, `create_session`, `close_followup`, `correct_vehicle`, `merge_sessions`, `retry_address`, `delete_all_data`.

## Data and privacy

- All charging data is stored locally in Home Assistant and is part of the backup.
- When the integration is removed, the charging data is kept. To delete it completely, call `ev_charging.delete_all_data` first.
- Vehicle identification number, card identifiers, addresses and coordinates appear in no entity.
- The integration keeps a log of its events and decisions for the last 90 days. It is included in the diagnostics download of the integration (Settings → Devices & services → EV Charging → Download diagnostics). Vehicle identification number, card labels, addresses and coordinates are removed from it, and card identifiers are shortened to their last four characters.
- For the address of charging sessions on the road, coordinates are sent to a geocoding service. This can be switched off.

## License

MIT
