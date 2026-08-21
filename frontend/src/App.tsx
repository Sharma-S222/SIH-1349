import { useEffect, useState, useRef, useCallback } from "react";
import "./App.css";

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
import camerasData from "./mocks/cameras.json";

import type {
  EventResponse,
} from "./types/api";




function App() {
  const [severityFilter, setSeverityFilter] = useState<"ALL" | "CRITICAL" | "HIGH" | "MEDIUM" | "LOW">("ALL");
  const [systemStatus, setSystemStatus] = useState("CONNECTING");

  const [cameras] = useState(camerasData);

  const [events, setEvents] = useState<EventResponse[]>([]);
  const [crowdData, setCrowdData] = useState({
    risk: "UNKNOWN",
    current_count: 0,
    trend: "UNKNOWN",
    zones: [],
  });

  const [selectedEvent, setSelectedEvent] = useState<EventResponse | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const wsRef = useRef<ReturnType<typeof createEventWebSocket> | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await fetchHealth();
        if (health.ok && health.data.status === "ready") {
          setSystemStatus("ONLINE");
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

  const loadEvents = useCallback(async () => {
    try {
      const result = await fetchEvents();
      if (result.ok && Array.isArray(result.data) && result.data.length > 0) {
        const sorted = [...result.data].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        setEvents(sorted);
      } else {
        console.log("Events API returned no data. Events list empty.");
        setEvents([]);
      }
    } catch (error) {
      console.error("Failed to load events:", error);
      setEvents([]);
    }
  }, []);

  // oxlint-disable-next-line react/set-state-in-effect
  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const loadCrowd = useCallback(async () => {
    try {
      const result = await fetchCrowdSummary();
      if (result.ok) {
        setCrowdData(result.data);
      }
    } catch (error) {
      console.error("Failed to load crowd summary:", error);
    }
  }, []);

  // oxlint-disable-next-line react/set-state-in-effect
  useEffect(() => {
    loadCrowd();
  }, [loadCrowd]);

  useEffect(() => {
    const handleMessage = (message: { type: string; data: Record<string, unknown> }) => {
      switch (message.type) {
        case "connection-established": {
          console.log("WebSocket connection established");
          break;
        }
        case "event.created": {
          const event = message.data as { event_id: string; camera_id: string; event_type: string; severity: string; confidence: number; timestamp: string; track_ids?: string[] };
          console.log("Live event received:", event);
          setEvents((prev) => {
            if (prev.some((e) => e.event_id === event.event_id)) {
              return prev;
            }
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
        case "crowd.updated": {
          const crowd = message.data as { camera_id: string; zone_id: string; people_count: number; timestamp: string };
          console.log("Crowd update:", crowd);
          loadCrowd();
          break;
        }
        case "incident.updated": {
          const incident = message.data as { incident_id: number; event_id: string; status: string; assigned_to: string | null };
          console.log("Incident updated:", incident);
          if (selectedEvent && selectedEvent.event_id === incident.event_id) {
            setSelectedStatus(incident.status);
          }
          break;
        }
        default:
          console.log("Unknown WS message type:", message.type);
      }
    };

    const handleStatusChange = (status: "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "RECONNECTING") => {
      if (status === "CONNECTED") {
        setSystemStatus("ONLINE");
      } else if (status === "DISCONNECTED") {
        setSystemStatus("OFFLINE");
      } else if (status === "RECONNECTING") {
        setSystemStatus("DEGRADED");
      }
    };

    const ws = createEventWebSocket(handleMessage, handleStatusChange);
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [loadCrowd]);

  const filteredEvents =
    severityFilter === "ALL"
      ? events
      : events.filter(
          (event) =>
            String(event.severity).toUpperCase() === severityFilter
        );

  const handleSelectEvent = (event: EventResponse) => {
    setSelectedEvent(event);
    setSelectedStatus(null);
  };

  const handleEventAction = async (action: "VERIFY" | "DISMISS" | "ASSIGN" | "RESOLVE") => {
    if (!selectedEvent) return;

    try {
      setLoadingAction(action);

      let result;
      if (action === "VERIFY") {
        result = await verifyIncident(
          selectedEvent.event_id,
          "operator_01",
          "Operator action: VERIFY"
        );
      } else if (action === "DISMISS") {
        result = await dismissIncident(
          selectedEvent.event_id,
          "operator_01",
          "Operator action: DISMISS"
        );
      } else if (action === "ASSIGN") {
        result = await assignIncident(
          selectedEvent.event_id,
          "operator_01",
          "operator_01",
          "Incident assigned by operator"
        );
      } else if (action === "RESOLVE") {
        result = await resolveIncident(
          selectedEvent.event_id,
          "operator_01",
          "Operator action: RESOLVE"
        );
      }

      console.log("INCIDENT ACTION SUCCESS:", action, result);

      if (result?.data?.status) {
        setSelectedStatus(result.data.status);
      }
    } catch (error) {
      console.error("INCIDENT ACTION FAILED:", error);
      alert(
        error instanceof Error
          ? error.message
          : "Failed to perform incident action"
      );
    } finally {
      setLoadingAction(null);
    }
  };

  const closeIncident = () => {
    setSelectedEvent(null);
    setSelectedStatus(null);
  };

  const getZoneRiskClass = (risk: string) => {
    const normalized = String(risk ?? "").toUpperCase();
    if (normalized === "HIGH") return "high";
    if (normalized === "CRITICAL") return "critical";
    if (normalized === "MEDIUM") return "moderate";
    if (normalized === "LOW") return "low";
    return "unknown";
  }

  const crowdRisk = crowdData?.risk ?? "UNKNOWN";
  const crowdCurrentCount = crowdData?.current_count ?? 0;
  const crowdTrend = crowdData?.trend ?? "UNKNOWN";
  const crowdZones = Array.isArray(crowdData?.zones) ? crowdData.zones : [];

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="header">
        <div>
          <h1>
            SIH1349 Railway AI Command Center
          </h1>

          <p>
            Station: Demo Junction
          </p>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          LIVE Ã¢â‚¬Â¢ SYSTEM {systemStatus}
        </div>
      </header>

      <main className="dashboard">

        {/* ===================================================
            SUMMARY CARDS
        =================================================== */}

        <section className="summary-grid">

          <div className="summary-card">
            <span>
              Active Alerts
            </span>

            <strong>
              {events.length}
            </strong>
          </div>

          <div className="summary-card">
            <span>
              Crowd Risk
            </span>

            <strong>
              {crowdRisk}
            </strong>
          </div>

          <div className="summary-card">
            <span>
              Cameras Online
            </span>

            <strong>
              {
                cameras.filter(
                  (camera) =>
                    String(
                      camera.status ?? ""
                    ).toUpperCase() ===
                    "ONLINE"
                ).length
              }{" "}
              / {cameras.length}
            </strong>
          </div>

        </section>

        {/* ===================================================
            PRIORITY ALERTS + ZONE RISK
        =================================================== */}

        <section className="content-grid">

          {/* PRIORITY ALERTS */}

          <div className="panel">

            <h2>
              Priority Alerts
            </h2>

            <div className="alert-filters">

              <button
                onClick={() =>
                  setSeverityFilter("ALL")
                }
                className={
                  severityFilter === "ALL"
                    ? "active"
                    : ""
                }
              >
                ALL
              </button>

              <button
                onClick={() =>
                  setSeverityFilter("CRITICAL")
                }
                className={
                  severityFilter === "CRITICAL"
                    ? "active"
                    : ""
                }
              >
                CRITICAL
              </button>

              <button
                onClick={() =>
                  setSeverityFilter("HIGH")
                }
                className={
                  severityFilter === "HIGH"
                    ? "active"
                    : ""
                }
              >
                HIGH
              </button>

              <button
                onClick={() =>
                  setSeverityFilter("MEDIUM")
                }
                className={
                  severityFilter === "MEDIUM"
                    ? "active"
                    : ""
                }
              >
                MODERATE
              </button>

            </div>

            {filteredEvents.length === 0 ? (
              <div className="empty-state">
                No alerts available.
              </div>
            ) : (
              filteredEvents.map((event) => (
                <div
                  className={`alert ${
                    String(
                      event.severity ?? "UNKNOWN"
                    ).toLowerCase()
                  }`}
                  key={event.event_id}
                  onClick={() =>
                    handleSelectEvent(event)
                  }
                  role="button"
                  tabIndex={0}
                  style={{
                    cursor: "pointer",
                  }}
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" ||
                      e.key === " "
                    ) {
                      handleSelectEvent(event);
                    }
                  }}
                >
                  <strong>
                    {event.severity}
                  </strong>

                  <span>
                    {String(
                      event.event_type ??
                        "UNKNOWN EVENT"
                    ).replaceAll("_", " ")}
                  </span>

                  <small>
                    {event.zone_id} Ã¢â‚¬Â¢{" "}
                    {Math.round(
                      Number(
                        event.confidence ?? 0
                      ) * 100
                    )}
                    % confidence
                  </small>
                </div>
              ))
            )}

          </div>

          {/* STATION / ZONE RISK */}

          <div className="panel">

            <h2>
              Station / Zone Risk
            </h2>

            <div className="zone">
              <span>
                Platform 1
              </span>

              <strong className="low">
                LOW
              </strong>
            </div>

            <div className="zone">
              <span>
                Stair A
              </span>

              <strong className="high-text">
                HIGH
              </strong>
            </div>

            <div className="zone">
              <span>
                Concourse
              </span>

              <strong className="moderate-text">
                MODERATE
              </strong>
            </div>

          </div>

        </section>

        {/* ===================================================
            INCIDENT DETAIL
        =================================================== */}

        {selectedEvent && (
          <section className="incident-panel">

            <div className="incident-header">

              <div>
                <p className="section-label">
                  INCIDENT DETAIL
                </p>

                <h2>
                  Event Information
                </h2>
              </div>

              <button
                className="close-button"
                onClick={closeIncident}
              >
                CLOSE
              </button>

            </div>

            <div className="incident-details">

              <div>
                <span>
                  Event ID
                </span>

                <strong>
                  {selectedEvent.event_id}
                </strong>
              </div>

              <div>
                <span>
                  Event Type
                </span>

                <strong>
                  {String(
                    selectedEvent.event_type
                  ).replaceAll("_", " ")}
                </strong>
              </div>

              <div>
                <span>
                  Severity
                </span>

                <strong>
                  {selectedEvent.severity}
                </strong>
              </div>

              <div>
                <span>
                  Zone
                </span>

                <strong>
                  {selectedEvent.zone_id}
                </strong>
              </div>

              <div>
                <span>
                  {(!selectedEvent.track_ids || selectedEvent.track_ids.length <= 1) ? "Track" : "Tracks"}
                </span>

                <strong>
                  {(!selectedEvent.track_ids || selectedEvent.track_ids.length === 0) 
                    ? "â€”" 
                    : selectedEvent.track_ids.join(", ")}
                </strong>
              </div>

              <div>
                <span>
                  Confidence
                </span>

                <strong>
                  {Math.round(
                    Number(
                      selectedEvent.confidence ?? 0
                    ) * 100
                  )}
                  %
                </strong>
              </div>

              <div>
                <span>
                  Status
                </span>

                <strong>
                  {selectedStatus ||
                    "NEW"}
                </strong>
              </div>

            </div>

            {/* OPERATOR ACTIONS */}

            <div className="incident-actions">

              <h3>
                Operator Actions
              </h3>

              <div className="action-buttons">

                <button
                  disabled={
                    loadingAction !== null
                  }
                  onClick={() =>
                    handleEventAction("VERIFY")
                  }
                >
                  {loadingAction === "VERIFY"
                    ? "VERIFYING..."
                    : "VERIFY"}
                </button>

                <button
                  disabled={
                    loadingAction !== null
                  }
                  onClick={() =>
                    handleEventAction("DISMISS")
                  }
                >
                  {loadingAction === "DISMISS"
                    ? "DISMISSING..."
                    : "DISMISS"}
                </button>

                <button
                  disabled={
                    loadingAction !== null
                  }
                  onClick={() =>
                    handleEventAction("ASSIGN")
                  }
                >
                  {loadingAction === "ASSIGN"
                    ? "ASSIGNING..."
                    : "ASSIGN"}
                </button>

                <button
                  disabled={
                    loadingAction !== null
                  }
                  onClick={() =>
                    handleEventAction("RESOLVE")
                  }
                >
                  {loadingAction === "RESOLVE"
                    ? "RESOLVING..."
                    : "RESOLVE"}
                </button>

              </div>

            </div>

            <div className="incident-footer">

              <button
                className="close-button"
                onClick={closeIncident}
              >
                CLOSE
              </button>

            </div>

          </section>
        )}

        {/* ===================================================
            LIVE CAMERAS
        =================================================== */}

        <section className="panel cameras">

          <h2>
            Live Cameras / Recent Events
          </h2>

          <div className="camera-grid">

            {cameras.map((camera) => (
              <div
                className="camera-card"
                key={camera.camera_id}
              >

                <div className="camera-placeholder">
                  {camera.camera_id}
                </div>

                <div className="camera-info">

                  <div>
                    <p>
                      {camera.name}
                    </p>

                    <span>
                      {camera.location}
                    </span>
                  </div>

                  <span
                    className={`camera-status ${String(
                      camera.status ?? "UNKNOWN"
                    ).toLowerCase()}`}
                  >
                    {camera.status}
                  </span>

                </div>

                <div className="camera-details">

                  <span>
                    People:{" "}
                    {camera.people_count}
                  </span>

                  <span
                    className={`camera-risk ${String(
                      camera.risk ?? "UNKNOWN"
                    ).toLowerCase()}`}
                  >
                    {camera.risk}
                  </span>

                </div>

              </div>
            ))}

          </div>

        </section>

        {/* ===================================================
            CROWD INTELLIGENCE
        =================================================== */}

        <section className="crowd-section">

          <div className="section-header">

            <div>
              <p className="section-label">
                CROWD INTELLIGENCE
              </p>

              <h2>
                Station Crowd Status
              </h2>
            </div>

            <span
              className={`risk-badge ${String(
                crowdRisk
              ).toLowerCase()}`}
            >
              {crowdRisk}
            </span>

          </div>

          {/* CROWD SUMMARY */}

          <div className="crowd-summary">

            <div className="crowd-card">

              <span>
                Current Count
              </span>

              <strong>
                {crowdCurrentCount}
              </strong>

              <small>
                People detected
              </small>

            </div>

            <div className="crowd-card">

              <span>
                Trend
              </span>

              <strong
                className={`trend-${String(
                  crowdTrend
                ).toLowerCase()}`}
              >
                {crowdTrend}
              </strong>

              <small>
                Current movement
              </small>

            </div>

            <div className="crowd-card">

              <span>
                Station Risk
              </span>

              <strong
                className={`crowd-risk-${String(
                  crowdRisk
                ).toLowerCase()}`}
              >
                {crowdRisk}
              </strong>

              <small>
                Overall crowd risk
              </small>

            </div>

          </div>

          {/* ZONE STATUS */}

          <div className="zone-list">

            <h3>
              Zone Status
            </h3>

            {crowdZones.length === 0 ? (
              <div className="empty-state">
                No crowd zone data available.
              </div>
            ) : (
              crowdZones.map((zone: any) => {

                const zonePeople =
                  Number(
                    zone.people_count ?? 0
                  );

                const percentage =
                  crowdCurrentCount > 0
                    ? Math.min(
                        (zonePeople /
                          crowdCurrentCount) *
                          100,
                        100
                      )
                    : 0;

                return (
                  <div
                    className="zone-row"
                    key={zone.zone_id}
                  >

                    <div className="zone-information">

                      <div className="zone-title-row">

                        <strong>
                          {zone.zone_id}
                        </strong>

                        <span
                          className={`zone-risk ${getZoneRiskClass(
                            zone.risk
                          )}`}
                        >
                          {zone.risk}
                        </span>

                      </div>

                      <span>
                        {zonePeople} people
                      </span>

                      <div className="crowd-bar">

                        <div
                          className={`crowd-bar-fill ${getZoneRiskClass(
                            zone.risk
                          )}`}
                          style={{
                            width: `${percentage}%`,
                          }}
                        />

                      </div>

                    </div>

                  </div>
                );
              })
            )}

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;


