import type { Camera, Zone, RailwayEvent, CrowdDataPoint } from '../types/ui';

export const ZONES: Zone[] = [
  { zone_id: 'PLT1', name: 'Platform 1', risk: 'LOW', people_count: 80, trend: 'stable', capacity: 300 },
  { zone_id: 'PLT2', name: 'Platform 2', risk: 'MEDIUM', people_count: 73, trend: 'up', capacity: 250 },
  { zone_id: 'PLT3', name: 'Platform 3', risk: 'HIGH', people_count: 181, trend: 'up', capacity: 250 },
  { zone_id: 'CONC', name: 'Main Concourse', risk: 'MEDIUM', people_count: 180, trend: 'stable', capacity: 500 },
  { zone_id: 'STCA', name: 'Staircase A', risk: 'CRITICAL', people_count: 59, trend: 'up', capacity: 80 },
  { zone_id: 'TRKZ', name: 'Track Zone', risk: 'HIGH', people_count: 12, trend: 'up', capacity: 5 },
];

export const CAMERAS: Camera[] = [
  { camera_id: 'CAM_PLATFORM_01', name: 'CAM_PLATFORM_01', zone_id: 'PLT1', zone_name: 'Platform 1', status: 'OFFLINE', people_count: 0, risk: 'LOW', last_update: '-', latest_event: 'AWAITING VIDEO', source_type: 'VIDEO' },
  { camera_id: 'CAM_PLATFORM_02', name: 'CAM_PLATFORM_02', zone_id: 'PLT2', zone_name: 'Platform 2', status: 'OFFLINE', people_count: 0, risk: 'LOW', last_update: '-', latest_event: 'AWAITING VIDEO', source_type: 'VIDEO' },
  { camera_id: 'CAM_PLATFORM_03', name: 'CAM_PLATFORM_03', zone_id: 'PLT3', zone_name: 'Platform 3', status: 'OFFLINE', people_count: 0, risk: 'LOW', last_update: '-', latest_event: 'NOT CONNECTED', source_type: 'LIVE_CAMERA' },
  { camera_id: 'CAM_PLATFORM_04', name: 'CAM_PLATFORM_04', zone_id: 'PLT4', zone_name: 'Platform 4', status: 'OFFLINE', people_count: 0, risk: 'LOW', last_update: '-', latest_event: 'NOT CONNECTED', source_type: 'DISCONNECTED' },
];

export const INITIAL_EVENTS: RailwayEvent[] = [
  {
    event_id: 'EVT_001',
    camera_id: 'CAM_10',
    camera_name: 'Staircase A Upper',
    zone_id: 'STCA',
    zone_name: 'Staircase A',
    timestamp: '2026-08-20T21:15:22+05:30',
    event_type: 'person_down',
    event_label: 'Possible Person Down',
    severity: 'CRITICAL',
    confidence: 0.88,
    people_count: 28,
    status: 'NEW',
  },
  {
    event_id: 'EVT_002',
    camera_id: 'CAM_06',
    camera_name: 'Platform 3 South',
    zone_id: 'PLT3',
    zone_name: 'Platform 3',
    timestamp: '2026-08-20T21:18:44+05:30',
    event_type: 'crowd_overload',
    event_label: 'Potential Crowd Overload',
    severity: 'HIGH',
    confidence: 0.94,
    people_count: 94,
    status: 'VERIFIED',
    verified_at: '2026-08-20T21:19:12+05:30',
    verified_by: 'operator_01',
  },
  {
    event_id: 'EVT_003',
    camera_id: 'CAM_04',
    camera_name: 'Track / Restricted Zone',
    zone_id: 'TRKZ',
    zone_name: 'Track Zone',
    timestamp: '2026-08-20T21:15:22+05:30',
    event_type: 'restricted_zone_intrusion',
    event_label: 'Potential Restricted Zone Intrusion',
    severity: 'HIGH',
    confidence: 0.92,
    people_count: 12,
    status: 'ASSIGNED',
    verified_at: '2026-08-20T21:16:10+05:30',
    verified_by: 'operator_01',
    assigned_at: '2026-08-20T21:16:44+05:30',
    assigned_to: 'operator_01',
    assigned_unit: 'RPF Team 1',
    assigned_note: 'Investigate Track Zone immediately',
  },
  {
    event_id: 'EVT_004',
    camera_id: 'CAM_13',
    camera_name: 'Ticket Counter',
    zone_id: 'CONC',
    zone_name: 'Main Concourse',
    timestamp: '2026-08-20T21:22:11+05:30',
    event_type: 'abandoned_object',
    event_label: 'Suspected Abandoned Object',
    severity: 'MEDIUM',
    confidence: 0.76,
    people_count: 67,
    status: 'NEW',
  },
  {
    event_id: 'EVT_005',
    camera_id: 'CAM_05',
    camera_name: 'Platform 3 North',
    zone_id: 'PLT3',
    zone_name: 'Platform 3',
    timestamp: '2026-08-20T21:19:30+05:30',
    event_type: 'crowd_overload',
    event_label: 'Potential Crowd Overload',
    severity: 'MEDIUM',
    confidence: 0.81,
    people_count: 87,
    status: 'NEW',
  },
  {
    event_id: 'EVT_006',
    camera_id: 'CAM_11',
    camera_name: 'Staircase A Lower',
    zone_id: 'STCA',
    zone_name: 'Staircase A',
    timestamp: '2026-08-20T21:20:15+05:30',
    event_type: 'possible_fall',
    event_label: 'Possible Fall Detected',
    severity: 'HIGH',
    confidence: 0.83,
    people_count: 31,
    status: 'VERIFIED',
    verified_at: '2026-08-20T21:21:05+05:30',
    verified_by: 'operator_02',
  },
  {
    event_id: 'EVT_007',
    camera_id: 'CAM_08',
    camera_name: 'Main Entrance North',
    zone_id: 'ENTR',
    zone_name: 'Main Entrance',
    timestamp: '2026-08-20T21:10:05+05:30',
    event_type: 'suspicious_behavior',
    event_label: 'Potential Safety Event',
    severity: 'LOW',
    confidence: 0.68,
    people_count: 45,
    status: 'RESOLVED',
    verified_at: '2026-08-20T21:11:00+05:30',
    verified_by: 'operator_02',
    assigned_at: '2026-08-20T21:11:30+05:30',
    assigned_to: 'operator_03',
    assigned_unit: 'Security Team B',
    assigned_note: 'Monitor entrance',
    resolved_at: '2026-08-20T21:19:02+05:30',
  },
];

const seed = (n: number) => Math.sin(n * 127.1) * 0.5 + 0.5;

export const CROWD_TREND_DATA: CrowdDataPoint[] = Array.from({ length: 60 }, (_, i) => {
  const mins = 59 - i;
  const baseCount = 370 + mins * 1.2;
  const noise = (seed(i) - 0.5) * 60;
  return {
    time: `${String(Math.floor((21 * 60 + 25 - mins) / 60) % 24).padStart(2, '0')}:${String((21 * 60 + 25 - mins) % 60).padStart(2, '0')}`,
    count: Math.max(290, Math.round(baseCount + noise)),
  };
});

export const INCIDENT_TREND: { hour: string; count: number }[] = [
  { hour: '00', count: 1 }, { hour: '01', count: 0 }, { hour: '02', count: 0 },
  { hour: '03', count: 1 }, { hour: '04', count: 0 }, { hour: '05', count: 0 },
  { hour: '06', count: 2 }, { hour: '07', count: 3 }, { hour: '08', count: 5 },
  { hour: '09', count: 4 }, { hour: '10', count: 6 }, { hour: '11', count: 7 },
  { hour: '12', count: 5 }, { hour: '13', count: 8 }, { hour: '14', count: 6 },
  { hour: '15', count: 9 }, { hour: '16', count: 11 }, { hour: '17', count: 13 },
  { hour: '18', count: 10 }, { hour: '19', count: 12 }, { hour: '20', count: 9 },
  { hour: '21', count: 7 }, { hour: '22', count: 0 }, { hour: '23', count: 0 },
];

export const INCIDENT_CATEGORIES = [
  { name: 'Crowd Overload', count: 34 },
  { name: 'Restricted Zone Intrusion', count: 21 },
  { name: 'Possible Fall', count: 18 },
  { name: 'Abandoned Object', count: 15 },
  { name: 'Possible Violence', count: 8 },
  { name: 'Fire / Smoke', count: 3 },
];

export const SEVERITY_DISTRIBUTION = [
  { name: 'CRITICAL', count: 8, color: '#ef4444' },
  { name: 'HIGH', count: 24, color: '#f97316' },
  { name: 'MEDIUM', count: 41, color: '#f59e0b' },
  { name: 'LOW', count: 26, color: '#22c55e' },
];

export const BUSIEST_ZONES = [
  { name: 'Platform 3', incidents: 29 },
  { name: 'Staircase A', incidents: 22 },
  { name: 'Track Zone', incidents: 18 },
  { name: 'Main Concourse', incidents: 15 },
  { name: 'Platform 2', incidents: 11 },
  { name: 'Platform 1', incidents: 4 },
];

export const RESPONSE_STATS = {
  avgVerification: '00:52',
  avgAssignment: '01:34',
  avgResolution: '08:17',
  totalToday: 99,
  resolvedToday: 88,
};

