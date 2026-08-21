import { useEffect, useState, useRef, useCallback } from "react";

import {
  fetchEvents,
  fetchCrowdSummary,
  fetchHealth,
  verifyIncident,
  dismissIncident,
  assignIncident,
  resolveIncident,
  normalizeSeverity,
} from "./api/api";

import { createEventWebSocket } from "./api/websocket";

import type { EventResponse, IncidentResponse, IncidentStatus } from "./types/api";
import type { RailwayEvent, ScreenName, WsStatus, AssignPayload } from "./types/ui";

import { Sidebar } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { CommandCenter } from "./components/screens/CommandCenter";
import { CameraGrid } from "./components/screens/CameraGrid";
import { AlertInbox } from "./components/screens/AlertInbox";
import { IncidentDetail } from "./components/screens/IncidentDetail";
import { CrowdIntelligence } from "./components/screens/CrowdIntelligence";
import { Analytics } from "./components/screens/Analytics";
import { SystemStatus } from "./components/screens/SystemStatus";

function eventToRailway(e: EventResponse): RailwayEvent {
  return {
    event_id: e.event_id,
    camera_id: e.camera_id,
    camera_name: e.camera_id,
    zone_id: e.zone_id ?? "",
    zone_name: e.zone_id ?? "",
    timestamp: e.timestamp,
    event_type: e.event_type,
    event_label: e.event_type.replace(/_/g, " "),
    severity: normalizeSeverity(e.severity),
    confidence: e.confidence,
    people_count: e.people_count ?? 0,
    status: "NEW",
  };
}

function incidentToRailway(e: EventResponse, inc?: IncidentResponse): RailwayEvent {
  const base = eventToRailway(e);
  if (!inc) return base;
  return {
    ...base,
    status: inc.status,
    verified_at: inc.status === "VERIFIED" ? inc.created_at : undefined,
    verified_by: inc.status === "VERIFIED" ? inc.assigned_to : undefined,
    assigned_at: inc.status === "ASSIGNED" ? inc.created_at : undefined,
    assigned_to: inc.assigned_to ?? undefined,
    resolved_at: inc.resolved_at ?? undefined,
  };
}

const screenTitles: Record<ScreenName, string> = {
  "command-center": "Command Center",
  cameras: "Camera Grid",
  alerts: "Alert Inbox",
  incidents: "Incident Detail",
  crowd: "Crowd Intelligence",
  analytics: "Analytics",
  system: "System Status",
};

export default function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenName>("command-center");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [wsStatus, setWsStatus] = useState<WsStatus>("CONNECTING");
  const [systemStatus, setSystemStatus] = useState("CONNECTING");

  const [events, setEvents] = useState<EventResponse[]>([]);
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [railwayEvents, setRailwayEvents] = useState<RailwayEvent[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);

  const wsRef = useRef<ReturnType<typeof createEventWebSocket> | null>(null);

  const newAlertCount = railwayEvents.filter((e) => e.status === "NEW").length;

  const loadEvents = useCallback(async () => {
    try {
      const result = await fetchEvents();
      if (result.ok && Array.isArray(result.data)) {
        const sorted = [...result.data].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        setEvents(sorted);
      }
    } catch (error) {
      console.error("Failed to load events:", error);
    }
  }, []);

  const loadCrowd = useCallback(async () => {
    try {
      await fetchCrowdSummary();
    } catch (error) {
      console.error("Failed to load crowd summary:", error);
    }
  }, []);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await fetchHealth();
        if (health.ok && health.data.status === "ready") {
          setSystemStatus("ONLINE");
          setWsStatus("CONNECTED");
        } else {
          setSystemStatus("DEGRADED");
        }
      } catch {
        setSystemStatus("OFFLINE");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // oxlint-disable-next-line react/set-state-in-effect
  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // oxlint-disable-next-line react/set-state-in-effect
  useEffect(() => {
    loadCrowd();
  }, [loadCrowd]);

  useEffect(() => {
    const handleMessage = (message: { type: string; data: Record<string, unknown> }) => {
      switch (message.type) {
        case "connection-established":
          console.log("WebSocket connection established");
          break;
        case "event.created": {
          const event = message.data as {
            event_id: string;
            camera_id: string;
            event_type: string;
            severity: string;
            confidence: number;
            timestamp: string;
          };
          setEvents((prev) => {
            if (prev.some((e) => e.event_id === event.event_id)) return prev;
            return [
              {
                event_id: event.event_id,
                camera_id: event.camera_id,
                event_type: event.event_type,
                severity: normalizeSeverity(event.severity),
                confidence: event.confidence,
                timestamp: event.timestamp,
                zone_id: null,
                people_count: null,
              },
              ...prev,
            ];
          });
          break;
        }
        case "crowd.updated":
          loadCrowd();
          break;
        case "incident.updated": {
          const incident = message.data as {
            incident_id: number;
            event_id: string;
            status: string;
            assigned_to: string | null;
          };
          setIncidents((prev) =>
            prev.map((inc) =>
              inc.event_id === incident.event_id
                ? { ...inc, status: incident.status as IncidentStatus, assigned_to: incident.assigned_to }
                : inc
            )
          );
          break;
        }
        default:
          break;
      }
    };

    const handleStatusChange = (status: "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "RECONNECTING") => {
      setWsStatus(status);
      if (status === "CONNECTED") setSystemStatus("ONLINE");
      else if (status === "DISCONNECTED") setSystemStatus("OFFLINE");
      else if (status === "RECONNECTING") setSystemStatus("DEGRADED");
    };

    const ws = createEventWebSocket(handleMessage, handleStatusChange);
    wsRef.current = ws;
    return () => { ws.close(); };
  // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [loadCrowd]);

  useEffect(() => {
    const merged = events.map((e) => {
      const inc = incidents.find((i) => i.event_id === e.event_id);
      return incidentToRailway(e, inc);
    });
    setRailwayEvents(merged);
  }, [events, incidents]);

  const handleViewIncident = useCallback((id: string) => {
    setSelectedIncidentId(id);
    setActiveScreen("incidents");
  }, []);

  const handleVerify = useCallback(
    async (id: string) => {
      const result = await verifyIncident(id, "operator_01", "Operator action: VERIFY");
      if (result.ok) {
        setIncidents((prev) => {
          const existing = prev.find((i) => i.event_id === id);
          if (existing) {
            return prev.map((i) => (i.event_id === id ? { ...i, status: "VERIFIED" } : i));
          }
          return [...prev, { incident_id: Date.now(), event_id: id, status: "VERIFIED", assigned_to: "operator_01", created_at: new Date().toISOString(), resolved_at: null }];
        });
        setEvents((prev) => prev.map((e) => (e.event_id === id ? { ...e } : e)));
      }
    },
    []
  );

  const handleDismiss = useCallback(
    async (id: string) => {
      const result = await dismissIncident(id, "operator_01", "Operator action: DISMISS");
      if (result.ok) {
        setIncidents((prev) => {
          const existing = prev.find((i) => i.event_id === id);
          if (existing) {
            return prev.map((i) => (i.event_id === id ? { ...i, status: "DISMISSED" } : i));
          }
          return [...prev, { incident_id: Date.now(), event_id: id, status: "DISMISSED", assigned_to: null, created_at: new Date().toISOString(), resolved_at: null }];
        });
      }
    },
    []
  );

  const handleAssign = useCallback(
    async (id: string, payload: AssignPayload) => {
      const result = await assignIncident(id, payload.unit, "operator_01", payload.note);
      if (result.ok) {
        setIncidents((prev) => {
          const existing = prev.find((i) => i.event_id === id);
          if (existing) {
            return prev.map((i) => (i.event_id === id ? { ...i, status: "ASSIGNED", assigned_to: payload.unit } : i));
          }
          return [...prev, { incident_id: Date.now(), event_id: id, status: "ASSIGNED", assigned_to: payload.unit, created_at: new Date().toISOString(), resolved_at: null }];
        });
      }
    },
    []
  );

  const handleResolve = useCallback(
    async (id: string) => {
      const result = await resolveIncident(id, "operator_01", "Operator action: RESOLVE");
      if (result.ok) {
        setIncidents((prev) =>
          prev.map((i) => (i.event_id === id ? { ...i, status: "RESOLVED", resolved_at: new Date().toISOString() } : i))
        );
      }
    },
    []
  );

  return (
    <div className="h-screen flex flex-col bg-background text-foreground overflow-hidden" style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
      <Header wsStatus={wsStatus} newAlertCount={newAlertCount} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          activeScreen={activeScreen}
          collapsed={sidebarCollapsed}
          onNavigate={setActiveScreen}
          onToggle={() => setSidebarCollapsed((c) => !c)}
          alertCount={newAlertCount}
        />

        <main className="flex-1 overflow-hidden flex flex-col">
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-border bg-card/30">
            <h1 className="text-slate-300 text-[13px] font-semibold tracking-wide">{screenTitles[activeScreen]}</h1>
            <span className="text-[10px] text-slate-600 font-mono">
              [{systemStatus}]
            </span>
          </div>

          <div className="flex-1 overflow-auto">
            {activeScreen === "command-center" && (
              <CommandCenter
                events={railwayEvents}
                onViewIncident={handleViewIncident}
                onNavigate={setActiveScreen}
              />
            )}
            {activeScreen === "cameras" && (
              <CameraGrid onViewIncident={handleViewIncident} />
            )}
            {activeScreen === "alerts" && (
              <AlertInbox events={railwayEvents} onViewIncident={handleViewIncident} />
            )}
            {activeScreen === "incidents" && (
              <IncidentDetail
                events={railwayEvents}
                selectedId={selectedIncidentId}
                onSelect={setSelectedIncidentId}
                onVerify={handleVerify}
                onDismiss={handleDismiss}
                onAssign={handleAssign}
                onResolve={handleResolve}
              />
            )}
            {activeScreen === "crowd" && <CrowdIntelligence />}
            {activeScreen === "analytics" && <Analytics />}
            {activeScreen === "system" && <SystemStatus wsStatus={wsStatus} />}
          </div>
        </main>
      </div>
    </div>
  );
}
