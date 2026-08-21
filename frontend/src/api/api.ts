import type { CrowdSummary } from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/* ============================================================
   ERROR HANDLING
=========================================================== */

class ApiCallError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiCallError";
    this.code = code;
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const error = payload as { error?: { code: string; message: string } } | null;
    throw new ApiCallError(
      error?.error?.code || "API_ERROR",
      error?.error?.message || `HTTP ${response.status}`,
      response.status
    );
  }

  return payload as T;
}

/* ============================================================
   EVENTS
=========================================================== */

import type { EventSeverity } from "../types/api";

export function normalizeSeverity(severity: string): EventSeverity {
  const normalized = severity.toUpperCase();
  if (normalized === "LOW" || normalized === "MEDIUM" || normalized === "HIGH" || normalized === "CRITICAL") {
    return normalized;
  }
  console.warn(`Unknown severity from backend: ${severity}, defaulting to LOW`);
  return "LOW";
}

export async function fetchEvents() {
  const response = await fetch(`${API_BASE_URL}/api/events`);
  const raw = await handleResponse<{ ok: true; data: Array<{
    event_id: string;
    camera_id: string;
    event_type: string;
    severity: string;
    confidence: number;
    timestamp: string;
    zone_id: string | null;
    people_count: number | null;
    track_ids?: string[] | null;
  }> }>(response);
  
  return {
    ...raw,
    data: raw.data.map(event => ({
      ...event,
      severity: normalizeSeverity(event.severity)
    }))
  };
}

/* ============================================================
   CAMERAS (no backend endpoint yet - returns mock-compatible empty)
=========================================================== */

export async function fetchCameras() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/cameras`);

    if (!response.ok) {
      console.warn(
        `Camera API returned ${response.status}. Using mock camera data.`
      );
      return { ok: false, data: [] };
    }

    return response.json();
  } catch (error) {
    console.warn("Camera API unavailable. Using mock camera data.", error);
    return { ok: false, data: [] };
  }
}

/* ============================================================
   CROWD
=========================================================== */

export async function fetchCrowdHistory() {
  const response = await fetch(`${API_BASE_URL}/api/crowd`);
  return handleResponse<{ ok: true; data: Array<{
    camera_id: string;
    zone_id: string | null;
    people_count: number;
    timestamp: string;
  }> }>(response);
}

/**
 * Transforms backend crowd history into dashboard summary format.
 * Backend returns array of history records; we compute the summary.
 */
export async function fetchCrowdSummary(): Promise<{ ok: true; data: CrowdSummary }> {
  const history = await fetchCrowdHistory();

  if (!history.ok || !history.data?.length) {
    return {
      ok: true,
      data: {
        risk: "UNKNOWN",
        current_count: 0,
        trend: "UNKNOWN",
        zones: [],
      },
    };
  }

  // Aggregate by zone
  const zoneMap = new Map<
    string,
    { people_count: number; latest_time: Date }
  >();

  for (const record of history.data) {
    const zoneKey = record.zone_id || "UNKNOWN";
    const recordTime = new Date(record.timestamp);
    const existing = zoneMap.get(zoneKey);

    if (!existing || recordTime > existing.latest_time) {
      zoneMap.set(zoneKey, {
        people_count: record.people_count,
        latest_time: new Date(record.timestamp),
      });
    }
  }

  const zones = Array.from(zoneMap.entries()).map((entry) => ({
    zone_id: entry[0],
    people_count: entry[1].people_count,
    risk: calculateRisk(entry[1].people_count),
  }));

  const totalPeople = zones.reduce((sum, z) => sum + z.people_count, 0);
  const overallRisk = calculateOverallRisk(zones);

  return {
    ok: true,
    data: {
      risk: overallRisk,
      current_count: totalPeople,
      trend: "STABLE",
      zones,
    },
  };
}

function calculateRisk(count: number): EventSeverity {
  if (count >= 50) return "CRITICAL";
  if (count >= 30) return "HIGH";
  if (count >= 15) return "MEDIUM";
  return "LOW";
}

function calculateOverallRisk(
  zones: Array<{ risk: EventSeverity }>
): EventSeverity {
  const maxRisk = zones.reduce((max, z) => {
    const order = { LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3 };
    return Math.max(max, order[z.risk] || 0);
  }, 0);
  const riskLevels: EventSeverity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
  return riskLevels[maxRisk] || "LOW";
}

/* ============================================================
   INCIDENTS
=========================================================== */

export async function fetchIncidents() {
  const response = await fetch(`${API_BASE_URL}/api/incidents`);
  return handleResponse<{ ok: true; data: Array<{
    incident_id: number;
    event_id: string;
    status: string;
    assigned_to: string | null;
    created_at: string;
    resolved_at: string | null;
  }> }>(response);
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse<{ ok: true; data: { status: string } }>(response);
}

/* ============================================================
   INCIDENT ACTIONS
=========================================================== */

async function incidentAction(
  incidentId: string,
  action: "verify" | "dismiss" | "assign" | "resolve",
  payload: { user: string; note?: string; assigned_to?: string }
) {
  const response = await fetch(
    `${API_BASE_URL}/api/incidents/${incidentId}/${action}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse<{ ok: true; data: any }>(response);
}

export async function verifyIncident(
  incidentId: string,
  user = "operator_01",
  note?: string
) {
  return incidentAction(incidentId, "verify", { user, note });
}

export async function dismissIncident(
  incidentId: string,
  user = "operator_01",
  note?: string
) {
  return incidentAction(incidentId, "dismiss", { user, note });
}

export async function assignIncident(
  incidentId: string,
  assignedTo: string,
  user = "operator_01",
  note?: string
) {
  return incidentAction(incidentId, "assign", { user, note, assigned_to: assignedTo });
}

export async function resolveIncident(
  incidentId: string,
  user = "operator_01",
  note?: string
) {
  return incidentAction(incidentId, "resolve", { user, note });
}
