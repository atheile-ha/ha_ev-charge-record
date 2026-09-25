import type { Session } from "./types";

// Selection and input handling for merging sessions in the correction view.
// Whether a selection may be merged is decided by the server alone.

export function toggleSelection(selection: string[], id: string): string[] {
  return selection.includes(id)
    ? selection.filter((selected) => selected !== id)
    : [...selection, id];
}

// Keeps only the ids that still exist, for instance after a reload.
export function pruneSelection(selection: string[], sessions: Session[]): string[] {
  const known = new Set(sessions.map((session) => session.id));
  return selection.filter((id) => known.has(id));
}

// The selected sessions without a stored odometer reading, earliest first.
export function sessionsWithoutOdometer(selection: string[], sessions: Session[]): Session[] {
  const selected = new Set(selection);
  return sessions
    .filter((session) => selected.has(session.id) && session.odometer_km === null)
    .sort((a, b) => Date.parse(a.plug_start) - Date.parse(b.plug_start));
}

// Entered odometer readings for the sessions without one; empty or invalid
// input is left out, so the server reports the reading as missing.
export function odometerPayload(
  missing: Session[],
  inputs: Record<string, string>,
): Record<string, number> {
  const payload: Record<string, number> = {};
  for (const session of missing) {
    const raw = inputs[session.id]?.trim();
    if (!raw) {
      continue;
    }
    const value = Number(raw);
    if (Number.isFinite(value) && value >= 0) {
      payload[session.id] = value;
    }
  }
  return payload;
}
