import { AlertTriangle, Wifi, WifiOff, Activity, Cpu } from 'lucide-react';
import type { WsStatus } from '../../types/ui';
import { CAMERAS } from '../../data/mockData';

interface SystemStatusProps {
  wsStatus: WsStatus;
}

const cameraStatusDot: Record<string, string> = {
  ONLINE: 'bg-green-500',
  OFFLINE: 'bg-red-500',
  DEGRADED: 'bg-amber-500',
  STALE: 'bg-slate-500',
};
const cameraStatusText: Record<string, string> = {
  ONLINE: 'text-green-400',
  OFFLINE: 'text-red-400',
  DEGRADED: 'text-amber-400',
  STALE: 'text-slate-400',
};

export function SystemStatus({ wsStatus }: SystemStatusProps) {
  const online = CAMERAS.filter(c => c.status === 'ONLINE').length;
  const offline = CAMERAS.filter(c => c.status === 'OFFLINE').length;
  const degraded = CAMERAS.filter(c => c.status === 'DEGRADED').length;

  return (
    <div className="p-4 space-y-4">
      {/* Service Health Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Backend API */}
        <ServiceCard
          title="Backend API"
          icon={<Activity size={16} className="text-blue-400" />}
          status={wsStatus === 'CONNECTED' || wsStatus === 'CONNECTING' ? 'online' : 'offline'}
          statusLabel={wsStatus === 'CONNECTED' ? 'ONLINE' : wsStatus === 'CONNECTING' ? 'CONNECTING' : 'OFFLINE'}
          details={[
            { label: 'Latency', value: wsStatus === 'CONNECTED' ? '24 ms' : '—' },
            { label: 'Endpoint', value: '/api/v1' },
          ]}
        />

        {/* WebSocket */}
        <ServiceCard
          title="Real-Time WebSocket"
          icon={<Wifi size={16} className="text-blue-400" />}
          status={wsStatus === 'CONNECTED' ? 'online' : wsStatus === 'RECONNECTING' ? 'warning' : wsStatus === 'CONNECTING' ? 'warning' : 'offline'}
          statusLabel={wsStatus}
          details={[
            { label: 'Last Event', value: wsStatus === 'CONNECTED' ? '4 sec ago' : '—' },
            { label: 'Channel', value: 'ws://events' },
          ]}
        />

        {/* Cameras */}
        <ServiceCard
          title="Cameras"
          icon={<Activity size={16} className="text-blue-400" />}
          status={offline > 0 || degraded > 0 ? 'warning' : 'online'}
          statusLabel={`${online} / ${CAMERAS.length} ONLINE`}
          details={[
            { label: 'Offline', value: String(offline), valueClass: offline > 0 ? 'text-red-400' : undefined },
            { label: 'Degraded', value: String(degraded), valueClass: degraded > 0 ? 'text-amber-400' : undefined },
          ]}
        />

        {/* AI Pipeline */}
        <ServiceCard
          title="AI Pipeline"
          icon={<Cpu size={16} className="text-slate-500" />}
          status="pending"
          statusLabel="AWAITING INTEGRATION"
          details={[
            { label: 'Note', value: 'Managed by backend team' },
          ]}
        />
      </div>

      {/* Live connection states */}
      <div className="bg-card border border-border rounded p-4">
        <div className="text-slate-400 text-[12px] font-semibold uppercase tracking-wider mb-3">Connection State</div>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-2">
          {(['CONNECTED', 'CONNECTING', 'DISCONNECTED', 'RECONNECTING', 'STALE DATA'] as const).map(state => {
            const isActive =
              (state === 'CONNECTED' && wsStatus === 'CONNECTED') ||
              (state === 'CONNECTING' && wsStatus === 'CONNECTING') ||
              (state === 'DISCONNECTED' && wsStatus === 'DISCONNECTED') ||
              (state === 'RECONNECTING' && wsStatus === 'RECONNECTING');
            return (
              <div key={state} className={`rounded border p-2 text-center transition-all ${
                isActive
                  ? state === 'CONNECTED' ? 'bg-green-700/20 border-green-600/40' :
                    state === 'CONNECTING' || state === 'RECONNECTING' ? 'bg-amber-700/20 border-amber-600/40' :
                    'bg-red-700/20 border-red-600/40'
                  : 'bg-transparent border-border opacity-40'
              }`}>
                <div className={`text-[11px] font-mono font-medium ${
                  isActive
                    ? state === 'CONNECTED' ? 'text-green-400' :
                      state === 'CONNECTING' || state === 'RECONNECTING' ? 'text-amber-400' :
                      'text-red-400'
                    : 'text-slate-600'
                }`}>{state}</div>
              </div>
            );
          })}
        </div>

        {(wsStatus === 'DISCONNECTED' || wsStatus === 'RECONNECTING') && (
          <div className="mt-3 flex items-start gap-2 bg-amber-900/20 border border-amber-700/30 rounded p-3">
            <AlertTriangle size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-amber-300 text-[12px] font-medium">Live connection interrupted</div>
              <div className="text-amber-500/70 text-[11px] mt-0.5">Displaying last known data. Attempting to reconnect...</div>
              <div className="text-amber-600/60 text-[11px] font-mono mt-0.5">Last successful update: 42 seconds ago</div>
            </div>
          </div>
        )}
      </div>

      {/* Camera status table */}
      <div className="bg-card border border-border rounded">
        <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
          <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Camera Status</span>
          <div className="flex items-center gap-3 text-[11px]">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> {online} Online</span>
            {degraded > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> {degraded} Degraded</span>}
            {offline > 0 && <span className="flex items-center gap-1 text-red-400"><span className="w-2 h-2 rounded-full bg-red-500" /> {offline} Offline</span>}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-2 text-left text-[10px] text-slate-500 uppercase tracking-wider">Camera</th>
                <th className="px-4 py-2 text-left text-[10px] text-slate-500 uppercase tracking-wider">Location</th>
                <th className="px-4 py-2 text-left text-[10px] text-slate-500 uppercase tracking-wider">Zone</th>
                <th className="px-4 py-2 text-center text-[10px] text-slate-500 uppercase tracking-wider">Connection</th>
                <th className="px-4 py-2 text-right text-[10px] text-slate-500 uppercase tracking-wider">Last Update</th>
                <th className="px-4 py-2 text-center text-[10px] text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {CAMERAS.map(cam => (
                <tr key={cam.camera_id} className={`hover:bg-white/3 transition-colors ${cam.status === 'OFFLINE' ? 'opacity-60' : ''}`}>
                  <td className="px-4 py-2 font-mono text-[11px] text-slate-300">{cam.camera_id}</td>
                  <td className="px-4 py-2 text-[12px] text-slate-300">{cam.name}</td>
                  <td className="px-4 py-2 text-[11px] text-slate-500">{cam.zone_name}</td>
                  <td className="px-4 py-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {cam.status === 'ONLINE' ? (
                        <Wifi size={12} className="text-green-400" />
                      ) : cam.status === 'OFFLINE' ? (
                        <WifiOff size={12} className="text-red-400" />
                      ) : (
                        <Wifi size={12} className="text-amber-400" />
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-[11px] text-slate-500">{cam.last_update}</td>
                  <td className="px-4 py-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <span className={`w-1.5 h-1.5 rounded-full ${cameraStatusDot[cam.status]}`} />
                      <span className={`text-[10px] font-mono ${cameraStatusText[cam.status]}`}>{cam.status}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ServiceCard({
  title, icon, status, statusLabel, details,
}: {
  title: string;
  icon: React.ReactNode;
  status: 'online' | 'offline' | 'warning' | 'pending';
  statusLabel: string;
  details: { label: string; value: string; valueClass?: string }[];
}) {
  const statusConfig = {
    online: { dot: 'bg-green-500 animate-pulse', text: 'text-green-400', bg: 'bg-green-700/10 border-green-700/30' },
    offline: { dot: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-900/10 border-red-700/20' },
    warning: { dot: 'bg-amber-500 animate-pulse', text: 'text-amber-400', bg: 'bg-amber-900/10 border-amber-700/20' },
    pending: { dot: 'bg-slate-600', text: 'text-slate-500', bg: 'bg-transparent border-border' },
  };
  const cfg = statusConfig[status];

  return (
    <div className={`rounded border p-3 ${cfg.bg}`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-slate-300 text-[12px] font-medium">{title}</span>
      </div>
      <div className="flex items-center gap-1.5 mb-2">
        <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
        <span className={`text-[11px] font-mono font-medium tracking-wide ${cfg.text}`}>{statusLabel}</span>
      </div>
      <div className="space-y-0.5">
        {details.map(d => (
          <div key={d.label} className="flex items-center justify-between">
            <span className="text-slate-600 text-[10px]">{d.label}</span>
            <span className={`text-[10px] font-mono ${d.valueClass ?? 'text-slate-400'}`}>{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
