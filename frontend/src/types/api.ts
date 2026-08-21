/**
 * Frontend TypeScript types matching the real SIH1349 backend API.
 * Based on actual backend implementation and event-v1 schema.
 */

// ============================================================
// Event Types (event-v1 schema compliant)
// ============================================================

export type EventSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Evidence {
  snapshot_path?: string | null;
  clip_path?: string | null;
}

export interface AIEvent {
  schema_version: "event-v1";
  event_id: string;
  camera_id: string;
  timestamp: number; // Unix epoch milliseconds (integer)
  event_type: string;
  severity: EventSeverity;
  confidence: number; // 0.0 - 1.0
  track_ids?: string[] | null;
  zone_id?: string | null;
  persistence_ms?: number | null;
  people_count?: number | null;
  metadata: Record<string, unknown>;
  evidence: Evidence;
}

// Event as returned by GET /api/events
export interface EventResponse {
  event_id: string;
  camera_id: string;
  event_type: string;
  severity: EventSeverity;
  confidence: number;
  timestamp: string; // ISO string from backend (e.timestamp)
  zone_id: string | null;
  people_count: number | null;
  track_ids?: string[] | null;
}

export interface EventsApiResponse {
  ok: true;
  data: EventResponse[];
}

// Event as broadcast via WebSocket (event.created)
export interface WebSocketEventCreated {
  event_id: string;
  camera_id: string;
  event_type: string;
  severity: EventSeverity;
  confidence: number;
  timestamp: string; // ISO string from backend
}

// ============================================================
// Crowd Types
// ============================================================

export interface CrowdMetricResponse {
  camera_id: string;
  zone_id: string | null;
  people_count: number;
  timestamp: string; // ISO string
}

export interface CrowdApiResponse {
  ok: true;
  data: CrowdMetricResponse[];
}

// Dashboard crowd summary (what frontend expects)
export interface CrowdSummary {
  risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNKNOWN";
  current_count: number;
  trend: "INCREASING" | "DECREASING" | "STABLE" | "UNKNOWN";
  zones: Array<{
    zone_id: string;
    people_count: number;
    risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  }>;
}

// ============================================================
// Incident Types
// ============================================================

export type IncidentStatus = "NEW" | "VERIFIED" | "ASSIGNED" | "RESOLVED" | "DISMISSED";

export interface IncidentResponse {
  incident_id: number;
  event_id: string;
  status: IncidentStatus;
  assigned_to: string | null;
  created_at: string; // ISO string
  resolved_at: string | null;
}

export interface IncidentsApiResponse {
  ok: true;
  data: IncidentResponse[];
}

export interface OperatorPayload {
  user: string;
  note?: string;
}

export interface AssignPayload {
  assigned_to: string;
  user: string;
  note?: string;
}

export interface IncidentActionResponse {
  ok: true;
  data: {
    incident_id: number;
    event_id: string;
    status: IncidentStatus;
    assigned_to?: string | null;
    resolved_at?: string | null;
  };
}

// WebSocket incident.updated message
export interface WebSocketIncidentUpdated {
  incident_id: number;
  event_id: string;
  status: IncidentStatus;
  assigned_to: string | null;
}

// ============================================================
// WebSocket Types
// ============================================================

export type WebSocketStatus = "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "RECONNECTING";

export type WebSocketMessageType =
  | "connection-established"
  | "event.created"
  | "crowd.updated"
  | "incident.updated";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: Record<string, unknown>;
}

export interface ConnectionEstablishedData {
  client_id: string;
}

export interface CrowdUpdatedData {
  camera_id: string;
  zone_id: string;
  people_count: number;
  timestamp: string; // ISO string
}

// Union type for all possible WebSocket data payloads
export type WebSocketData =
  | ConnectionEstablishedData
  | WebSocketEventCreated
  | CrowdUpdatedData
  | WebSocketIncidentUpdated
  | Record<string, unknown>;

// ============================================================
// Health & Status
// ============================================================

export interface HealthResponse {
  ok: true;
  data: { status: "ready" };
}

export type SystemStatus = "ONLINE" | "CONNECTING" | "DEGRADED" | "OFFLINE";

// ============================================================
// Camera Types (mock/config only - no backend endpoint yet)
// ============================================================

export interface CameraConfig {
  camera_id: string;
  name: string;
  location: string;
  status: "ONLINE" | "OFFLINE" | "UNKNOWN";
  people_count: number;
  risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNKNOWN";
}

// ============================================================
// API Error Types
// ============================================================

export interface ApiError {
  ok: false;
  error: {
    code: string;
    message: string;
  };
}

export type ApiResponse<T> = { ok: true; data: T } | ApiError;

