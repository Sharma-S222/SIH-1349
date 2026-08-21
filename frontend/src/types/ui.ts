export type EventSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type EventStatus = 'NEW' | 'VERIFIED' | 'DISMISSED' | 'ASSIGNED' | 'RESOLVED';
export type CameraStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'STALE';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type WsStatus = 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED' | 'RECONNECTING';
export type ScreenName = 'command-center' | 'cameras' | 'alerts' | 'incidents' | 'crowd' | 'analytics' | 'system';

export interface RailwayEvent {
  event_id: string;
  camera_id: string;
  camera_name: string;
  zone_id: string;
  zone_name: string;
  timestamp: string;
  event_type: string;
  event_label: string;
  severity: EventSeverity;
  confidence: number;
  people_count: number;
  status: EventStatus;
  verified_at?: string;
  verified_by?: string;
  assigned_at?: string;
  assigned_to?: string;
  assigned_unit?: string;
  assigned_note?: string;
  resolved_at?: string;
  dismissed_at?: string;
  dismissed_reason?: string;
}

export interface Camera {
  camera_id: string;
  name: string;
  zone_id: string;
  zone_name: string;
  status: CameraStatus;
  people_count: number;
  risk: RiskLevel;
  source_type?: string;
  telemetry?: any;
  latest_event?: string;
  last_update: string;
}

export interface Zone {
  zone_id: string;
  name: string;
  risk: RiskLevel;
  source_type?: string;
  telemetry?: any;
  people_count: number;
  trend: 'up' | 'down' | 'stable';
  capacity: number;
}

export interface CrowdDataPoint {
  time: string;
  count: number;
}

export interface AssignPayload {
  unit: string;
  operator: string;
  note: string;
}

export interface TimelineEntry {
  time: string;
  label: string;
  actor?: string;
}


