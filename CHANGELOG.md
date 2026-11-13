# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning according to [SemVer](https://semver.org/).

## [0.6.5] - 2026-11-13

### Fixed

- If the vehicle reported charging before its location changed to "home" and the wallbox session was then assigned the same vehicle, two charging sessions of the same vehicle existed at the same time and both were stored. The vehicle's own session is now discarded as soon as the wallbox session holds the vehicle

## [0.6.4] - 2026-10-25

### Added

- Efficiency per vehicle and charge type as diagnostic entities `sensor.<vehicle>_efficiency_ac` and `_dc`, also in the diagnostics download

## [0.6.3] - 2026-10-25

### Added

- Log of all events and decisions of the recording, kept for 90 days, at most 20,000 entries
- Diagnostics download with global settings, wallbox and vehicles, running charging session and log; vehicle identification number, card identifiers, card labels, addresses and coordinates are removed, card identifiers in the log are shortened to their last four characters

### Changed

- `ev_charging.delete_all_data` also deletes the log
- When the integration is removed, the state of the running charging session and the log are discarded; the charging data is kept

## [0.6.2] - 2026-10-22

### Added

- Own icon of the integration in Home Assistant

### Changed

- Notification at the end of a charging session names start and end, with one date and both times if the date is the same, as well as the odometer reading
- Notification at the end of a charging session shows the solar share in percent instead of grid and solar share in kWh
- Notification at the end of a charging session shows the cost with currency symbol, for example "€4.87"
- Notification at the end of a charging session shows the duration as "Duration: 13:28 (net: 6:52 in 4 phases)"
- Notification on a charging error names the error and the source, for example "Charging error (vehicle)", instead of a device code
- Live card shows a charging error only while it persists
- Detail list no longer shows a charging error

## [0.6.1] - 2026-10-20

### Added

- Notification at the start of a charging session at home, as soon as the vehicle is identified, with vehicle, state of charge and odometer reading; can be switched off individually

## [0.6.0] - 2026-10-20

### Added

- Entity `binary_sensor.ev_charging_problem`, on while the wallbox or the vehicle reports a charging error
- Notifications in Home Assistant and to up to two targets, for example the companion app
- Notifications on the end of a session, start and end of an external session, charging error and open follow-up, each can be switched off individually, in the "Notifications" section of the global settings
- Notification when a charging session is closed after 12 hours without a response from the source
- Repair issue when a notification target no longer exists

### Changed

- A charging error counts after 5 seconds, also without a running charging session and at every charging location
- Live card names the source of a charging error, wallbox or vehicle
- Panel: the "Last 5" tab is removed; the most recent charging sessions are shown by the card `ev-charging-recent-card`
- Panel: follow-up entry is at the top of the "Correction" view instead of in a separate tab
- Panel: detail list without monthly totals above the table
- Panel reloads by itself after a restart of Home Assistant

## [0.5.6] - 2026-09-30

### Fixed

- Installation alongside current Home Assistant versions

## [0.5.5] - 2026-09-30

### Fixed

- If a charging session is assigned to a vehicle afterwards through the card, state of charge and odometer reading at the start are filled in
- After a correction, all fields that now have a value disappear from the follow-up
- Corrections calculate the estimated energy correctly
- After saving, all views of the panel show the current state

## [0.5.4] - 2026-09-25

### Added

- Merging selected charging sessions in the "Correction" view, with preview and confirmation, and service `ev_charging.merge_sessions`

## [0.5.3] - 2026-09-25

### Changed

- A vehicle that reports a charging session at home gets a session of its own only after 90 seconds, and only if the wallbox does not record it

### Fixed

- The charging session of a vehicle ends on unplugging, even if the vehicle reports the unplugging before the wallbox
- The cards no longer intermittently show "Custom element doesn't exist"

## [0.5.2] - 2026-09-24

### Changed

- No second charging session is created for the vehicle at the wallbox
- The plug state of the vehicle ends its charging session
- Assigned entities are shown in the field in the dialogs and can be cleared

### Fixed

- Cards load more reliably after a restart of Home Assistant

## [0.5.1] - 2026-09-23

### Added

- Panel views Follow-up and Correction: enter missing values, edit or delete charging sessions, correct the vehicle, add past charging sessions
- Services `ev_charging.update_session`, `delete_session`, `create_session`, `close_followup` and `correct_vehicle`, administrators only

### Changed

- If a charging session is automatically assigned to a vehicle afterwards, state of charge and odometer reading at the start are filled in from the history

## [0.5.0] - 2026-09-22

### Added

- Recording of charging sessions through the vehicle integration: at home without a wallbox and on the road, also several at the same time
- Address of external charging sessions from the location of the vehicle
- Service `ev_charging.retry_address`
- Entity `binary_sensor.<vehicle>_session_active` as well as disabled sensors per vehicle for state, charging location, state of charge, odometer reading, energy, charging duration and charge end

### Changed

- Live card shows every running charging session in a block of its own
- Live card shows "No vehicle connected to wallbox" when there is no vehicle
- Panel and cards reload by themselves after a connection loss

## [0.4.4] - 2026-09-20

### Changed

- Live card: more compact display of vehicle, odometer reading and state of charge, two columns also on narrow displays
- Live card: expected end only while charging
- Live card: "Card read" disappears as soon as the vehicle is shown
- The wallbox appears only once on the page of the integration; entities and their IDs are kept

## [0.4.3] - 2026-09-20

### Changed

- The card identification is read from the wallbox as soon as "Read identification from the wallbox register" is selected in the wallbox dialog; a separate switch is removed
- Shorter descriptions in the wallbox dialog

## [0.4.2] - 2026-09-20

### Added

- More detailed debug logging

### Changed

- If the wallbox reports only a part of the card identification, it is searched at both the start and the end of the stored serial number

## [0.4.1] - 2026-09-20

### Added

- Optional reading of the card identification directly from the KEBA P40 over Modbus TCP, read-only
- Subsequent assignment when the card identification is read only later
- A charging session begins on plugging in, even if no power flows yet, and then waits in the "paused" state
- Plug-in events without charging are not stored
- Live card shows state, origin of the vehicle assignment, state of the card reading and the reason for missing values
- Repair issues when the wallbox is unreachable or provides no identification

### Changed

- The power threshold no longer begins a charging session, it only opens and closes charging phases
- Live card shows "Vehicle is being identified" until the vehicle is determined

## [0.4.0] - 2026-09-20

### Added

- Recording of charging sessions at the wallbox with charging phases, net charging duration and pauses
- Grid and solar share as well as cost per charging session
- Vehicle assignment by card identification or vehicle integration
- Continuation of a running charging session after a restart
- Entities for state, vehicle, cost, grid and solar share, price and open follow-ups
- Cards `ev-charging-live-card` and `ev-charging-month-card`
- Repair issues for unknown identification, change of the energy counter and unknown state value

### Changed

- Open follow-ups show the vehicle
- Cards are reliably reloaded after an update

## [0.3.10] - 2026-09-19

### Changed

- Filter bar at the top of overview and detail list; the filters apply to all totals and charts

## [0.3.9] - 2026-09-19

### Added

- Number of charging sessions in `ev-charging-recent-card` can be set in the card dialog
- Link to Google Maps behind the address of a charging session

### Changed

- `ev-charging-recent-card` shows the details expandable
- Yearly summary and monthly values rounded to whole numbers

## [0.3.8] - 2026-09-19

### Added

- Yearly summary below the monthly bars, total, internal and external
- Value of each month below its bar
- Card filter with the stored cards

### Changed

- Energy with three decimal places
- Detail list as a table, with a uniform layout on mobile
- Clearer labels for charging location, charge type and status

## [0.3.7] - 2026-09-19

### Added

- Panel "EV Charging" with overview and detail list
- Cards `ev-charging-panel-card` and `ev-charging-recent-card`
- Charging sessions without a vehicle appear as "Not assigned"
- Estimated values are marked with ~

## [0.3.6] - 2026-09-18

### Changed

- Maintenance without visible change

## [0.3.5] - 2026-09-18

### Added

- Storage of charging sessions
- Service `ev_charging.delete_all_data` with mandatory confirmation, administrators only

## [0.3.4] - 2026-09-17

### Fixed

- Error in the validation of the translations

## [0.3.3] - 2026-09-17

### Changed

- Integrations that are not installed are listed in a collapsed section of the device dialog

### Fixed

- The notice on devices that are not offered appears in the configured language

## [0.3.2] - 2026-09-17

### Added

- Support for Škoda with MySkoda connect
- Plug state of the vehicle as an optional value

### Changed

- Clearer field names in the wallbox and vehicle dialogs
- Separate choice "Vehicle without online connection"

## [0.3.1] - 2026-09-17

### Changed

- Device selection also names the source integration

## [0.3.0] - 2026-09-16

### Added

- Support for ten wallboxes and vehicles, choice of the device as the first step in the dialog
- Notice on devices whose integration is missing or too old

### Changed

- Manual assignment of state values is removed; after the update, the chosen device has to be selected once again

## [0.2.2] - 2026-09-15

### Changed

- Fewer setup steps for known devices
- More consistent texts in the dialogs

## [0.2.1] - 2026-09-14

### Fixed

- Errors on loading and in the translations

## [0.2.0] - 2026-09-14

### Added

- Assignment of the entities of wallbox, vehicle and electricity tariff in the setup dialog
- Assignments are kept when entities are renamed
- Repair issues on a removed entity and a changed unit
- Detection of a vehicle through the vehicle integration
- Display of the most recently reported card identification in the vehicle dialog

### Changed

- An active vehicle needs at least one card or detection through the vehicle integration

## [0.1.5] - 2026-09-14

### Added

- Global settings, changeable through "Reconfigure"
- Manufacturer and model for wallbox and vehicle
- Card type RFID or eMAID

### Removed

- Default vehicle at the wallbox
- Fixed charging price on the vehicle

## [0.1.3] - 2026-09-13

### Changed

- Simplified wallbox dialog with collapsed expert options

## [0.1.2] - 2026-09-13

### Added

- Setup and removal of the integration
- Adding wallbox and vehicles with master data and cards
- German and English texts
