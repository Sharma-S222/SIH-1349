export type WebSocketStatus =
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED"
  | "RECONNECTING";

export type WebSocketMessageType =
  | "connection-established"
  | "event.created"
  | "crowd.updated"
  | "incident.updated";

export type WebSocketMessage = {
  type: string;
  data?: Record<string, unknown>;
};

const WS_URL =
  import.meta.env.VITE_WS_URL || "ws://127.0.0.1:8000/ws/events";

export function createEventWebSocket(
  onMessage: (message: { type: string; data: Record<string, unknown> }) => void,
  onStatusChange?: (status: "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "RECONNECTING") => void
) {
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let manuallyClosed = false;
  let reconnectAttempt = 0;

  const connect = () => {
    if (manuallyClosed) {
      return;
    }

    onStatusChange?.(
      reconnectAttempt > 0 ? "RECONNECTING" : "CONNECTING"
    );

    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      reconnectAttempt = 0;
      onStatusChange?.("CONNECTED");
      console.log("WebSocket connected:", WS_URL);
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as {
          type: string;
          data?: Record<string, unknown>;
        };

        if (!message || typeof message.type !== "string") {
          console.warn("Ignoring invalid WebSocket message:", message);
          return;
        }

        console.log("WebSocket message:", message);

        // Normalize message types
        const normalizedType = normalizeMessageType(message.type);
        const data = message.data || {};

        onMessage({ type: normalizedType, data });
      } catch (error) {
        console.error("Invalid WebSocket JSON message:", error);
      }
    };

    socket.onerror = (error) => {
      console.warn("WebSocket error:", error);
    };

    socket.onclose = () => {
      socket = null;

      if (manuallyClosed) {
        onStatusChange?.("DISCONNECTED");
        return;
      }

      onStatusChange?.("DISCONNECTED");

      reconnectAttempt += 1;

      const delay = Math.min(
        1000 * 2 ** Math.min(reconnectAttempt - 1, 4),
        10000
      );

      console.log(
        `WebSocket disconnected. Reconnecting in ${delay}ms...`
      );

      reconnectTimer = setTimeout(connect, delay);
    };
  };

  connect();

  return {
    close() {
      manuallyClosed = true;

      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      if (socket) {
        socket.close();
        socket = null;
      }

      onStatusChange?.("DISCONNECTED");
    },
  };
}

/**
 * Normalize backend WebSocket message types to frontend types.
 * Backend sends: "connection-established", "event.created", "crowd.updated", "incident.updated"
 * Frontend expects: "connection-established", "event.created", "crowd.updated", "incident.updated"
 */
function normalizeMessageType(type: string): string {
  const mapping: Record<string, string> = {
    "connection-established": "connection-established",
    "event.created": "event.created",
    "crowd.updated": "crowd.updated",
    "incident.updated": "incident.updated",
  };

  return mapping[type] || type;
}