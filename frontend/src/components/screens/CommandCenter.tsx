import { ArrowUp, ArrowDown, Minus, AlertTriangle, Camera, FileWarning, Users, Bell } from 'lucide-react';
import type { RailwayEvent, Zone, ScreenName } from '../../types/ui';
import { SeverityBadge, severityBorderColor } from '../shared/SeverityBadge';
import { CCTVPlaceholder } from '../shared/CCTVPlaceholder';
import { CAMERAS, ZONES } from '../../data/mockData';

const riskBarColor: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-amber-500',
  LOW: 'bg-green-500',
};

const riskBg: Record<string, string> = {
  CRITICAL: 'text-red-400',
  HIGH: 'text-orange-400',
  MEDIUM: 'text-amber-400',
  LOW: 'text-green-400',
};

function TrendIcon({ trend }: { trend: Zone['trend'] }) {
  if (trend === 'up') return <ArrowUp size={12} className="text-orange-400" />;
  if (trend === 'down') return <ArrowDown size={12} className="text-green-400" />;
  return <Minus size={12} className="text-slate-500" />;
}

interface CommandCenterProps {
  events: RailwayEvent[];
  onViewIncident: (id: string) => void;
  onNavigate: (screen: ScreenName) => void;
}

export function CommandCenter({ events, onViewIncident, onNavigate }: CommandCenterProps) {
  const activeAlerts = events.filter(e => e.status !== 'RESOLVED' && e.status !== 'DISMISSED');
  const criticalCount = events.filter(e => e.severity === 'CRITICAL' && e.status !== 'RESOLVED' && e.status !== 'DISMISSED').length;
  const highestRiskZone = [...ZONES].sort((a, b) => {
    const order = { CRITICAL: 3, HIGH: 2, MEDIUM: 1, LOW: 0 };
    return order[b.risk] - order[a.risk];
  })[0];

  const onlineCameras = CAMERAS.filter(c => c.status === 'ONLINE').length;
  const openIncidents = events.filter(e => e.status !== 'RESOLVED' && e.status !== 'DISMISSED');
  const newCount = openIncidents.filter(e => e.status === 'NEW').length;
  const verifiedCount = openIncidents.filter(e => e.status === 'VERIFIED').length;
  const assignedCount = openIncidents.filter(e => e.status === 'ASSIGNED').length;

  const priorityAlerts = [...events]
    .filter(e => e.status !== 'RESOLVED' && e.status !== 'DISMISSED')
    .sort((a, b) => {
      const order = { CRITICAL: 3, HIGH: 2, MEDIUM: 1, LOW: 0 };
      return order[b.severity] - order[a.severity];
    })
    .slice(0, 4);

  const previewCameras = CAMERAS.filter(c => c.risk !== 'LOW').slice(0, 4);

  function formatTime(isoStr: string) {
    return new Date(isoStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }

  return (
    <div className="p-4 space-y-4 min-h-full">
      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-card border border-border rounded p-3 cursor-pointer hover:border-slate-600 transition-colors" onClick={() => onNavigate('alerts')}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-[12px] font-medium uppercase tracking-wider">Active Alerts</span>
            <Bell size={14} className="text-slate-500" />
          </div>
          <div className="text-3xl font-bold text-slate-100 font-mono">{String(activeAlerts.length).padStart(2, '0')}</div>
          <div className="text-[11px] mt-1 text-red-400">{criticalCount} critical</div>
        </div>

        <div className="bg-card border border-border rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-[12px] font-medium uppercase tracking-wider">Crowd Risk</span>
            <Users size={14} className="text-slate-500" />
          </div>
          <div className={`text-2xl font-bold font-mono ${riskBg[highestRiskZone.risk]}`}>{highestRiskZone.risk}</div>
          <div className="text-[11px] mt-1 text-slate-500">{highestRiskZone.name} approaching threshold</div>
        </div>

        <div className="bg-card border border-border rounded p-3 cursor-pointer hover:border-slate-600 transition-colors" onClick={() => onNavigate('cameras')}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-[12px] font-medium uppercase tracking-wider">Cameras Online</span>
            <Camera size={14} className="text-slate-500" />
          </div>
          <div className="text-3xl font-bold text-slate-100 font-mono">{onlineCameras} <span className="text-slate-500 text-xl">/ {CAMERAS.length}</span></div>
          <div className="text-[11px] mt-1 text-amber-400">{CAMERAS.length - onlineCameras} {CAMERAS.length - onlineCameras === 1 ? 'camera' : 'cameras'} offline/degraded</div>
        </div>

        <div className="bg-card border border-border rounded p-3 cursor-pointer hover:border-slate-600 transition-colors" onClick={() => onNavigate('incidents')}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-[12px] font-medium uppercase tracking-wider">Open Incidents</span>
            <FileWarning size={14} className="text-slate-500" />
          </div>
          <div className="text-3xl font-bold text-slate-100 font-mono">{String(openIncidents.length).padStart(2, '0')}</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] font-mono bg-blue-600/20 text-blue-400 px-1.5 py-0.5 rounded">{newCount} NEW</span>
            <span className="text-[10px] font-mono bg-green-700/20 text-green-400 px-1.5 py-0.5 rounded">{verifiedCount} VERIFIED</span>
            <span className="text-[10px] font-mono bg-purple-700/20 text-purple-400 px-1.5 py-0.5 rounded">{assignedCount} ASSIGNED</span>
          </div>
        </div>
      </div>

      {/* Middle row: Priority Alerts + Zone Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Priority Alerts */}
        <div className="lg:col-span-2 bg-card border border-border rounded">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-amber-400" />
              <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Priority Alerts</span>
            </div>
            <button onClick={() => onNavigate('alerts')} className="text-blue-400 hover:text-blue-300 text-[11px] font-medium transition-colors">
              View All →
            </button>
          </div>
          <div className="divide-y divide-border">
            {priorityAlerts.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <div className="text-slate-500 text-sm">No active safety alerts</div>
                <div className="text-slate-600 text-xs mt-1">Railway operations are currently clear.</div>
              </div>
            ) : (
              priorityAlerts.map((alert) => (
                <div
                  key={alert.event_id}
                  className={`px-4 py-3 border-l-2 hover:bg-white/3 transition-colors ${severityBorderColor(alert.severity)}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <SeverityBadge severity={alert.severity} size="sm" />
                        <span className="text-slate-200 text-[13px] font-medium">{alert.event_label}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500 flex-wrap">
                        <span className="font-mono">{alert.zone_name}</span>
                        <span>·</span>
                        <span className="font-mono">{alert.camera_id}</span>
                        <span>·</span>
                        <span>Detected {formatTime(alert.timestamp)}</span>
                        <span>·</span>
                        <span>Confidence {Math.round(alert.confidence * 100)}%</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                        alert.status === 'NEW' ? 'bg-blue-600/20 text-blue-400 border-blue-600/30' :
                        alert.status === 'VERIFIED' ? 'bg-green-700/20 text-green-400 border-green-700/30' :
                        alert.status === 'ASSIGNED' ? 'bg-purple-700/20 text-purple-400 border-purple-700/30' :
                        'bg-slate-700/30 text-slate-400 border-slate-700/30'
                      }`}>{alert.status}</span>
                      <button
                        onClick={() => onViewIncident(alert.event_id)}
                        className="text-[11px] text-blue-400 hover:text-blue-300 font-medium transition-colors px-2 py-1 rounded hover:bg-blue-600/10"
                      >
                        View
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Station Zone Risk */}
        <div className="bg-card border border-border rounded">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Station / Zone Risk</span>
            <button onClick={() => onNavigate('crowd')} className="text-blue-400 hover:text-blue-300 text-[11px] font-medium transition-colors">
              Details →
            </button>
          </div>
          <div className="p-3 space-y-2">
            {ZONES.map(zone => (
              <div key={zone.zone_id} className="flex items-center gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-slate-300 text-[12px] font-medium truncate">{zone.name}</span>
                    <div className="flex items-center gap-1">
                      <TrendIcon trend={zone.trend} />
                      <span className={`text-[11px] font-mono font-medium ${riskBg[zone.risk]}`}>{zone.risk}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${riskBarColor[zone.risk]}`}
                        style={{ width: `${Math.min(100, (zone.people_count / zone.capacity) * 100)}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-slate-500 flex-shrink-0 w-10 text-right">{zone.people_count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Simple schematic */}
          <div className="mx-3 mb-3 border border-border rounded overflow-hidden">
            <div className="grid grid-cols-3 text-center">
              {(['Platform 1', 'Platform 2', 'Platform 3'] as const).map((name) => {
                const z = ZONES.find(z => z.name === name);
                return (
                  <div key={name} className={`py-2 border-r border-border last:border-r-0 ${
                    z?.risk === 'CRITICAL' ? 'bg-red-900/30' :
                    z?.risk === 'HIGH' ? 'bg-orange-900/20' :
                    z?.risk === 'MEDIUM' ? 'bg-amber-900/15' : 'bg-green-900/10'
                  }`}>
                    <div className="text-[9px] text-slate-500 font-mono">{name.replace('Platform ', 'PLT')}</div>
                    <div className={`text-[10px] font-mono font-medium mt-0.5 ${z ? riskBg[z.risk] : 'text-slate-500'}`}>{z?.risk ?? '—'}</div>
                  </div>
                );
              })}
            </div>
            <div className={`py-2 text-center border-t border-border ${
              ZONES.find(z => z.name === 'Main Concourse')?.risk === 'CRITICAL' ? 'bg-red-900/30' :
              ZONES.find(z => z.name === 'Main Concourse')?.risk === 'HIGH' ? 'bg-orange-900/20' :
              'bg-amber-900/10'
            }`}>
              <div className="text-[9px] text-slate-500 font-mono">CONCOURSE</div>
              <div className={`text-[10px] font-mono font-medium mt-0.5 ${riskBg[ZONES.find(z => z.name === 'Main Concourse')?.risk ?? 'LOW']}`}>
                {ZONES.find(z => z.name === 'Main Concourse')?.risk}
              </div>
            </div>
            <div className="grid grid-cols-2 border-t border-border">
              {([{ name: 'Main Entrance', risk: 'LOW' as const }, { name: 'Staircase A', risk: null }]).map((item, i) => {
                const z = ZONES.find(z => z.name === item.name);
                const risk = z?.risk ?? item.risk ?? 'LOW';
                return (
                  <div key={item.name} className={`py-2 text-center ${i === 0 ? 'border-r border-border' : ''} ${
                    risk === 'CRITICAL' ? 'bg-red-900/30' :
                    risk === 'HIGH' ? 'bg-orange-900/20' :
                    risk === 'MEDIUM' ? 'bg-amber-900/10' : 'bg-transparent'
                  }`}>
                    <div className="text-[9px] text-slate-500 font-mono">{item.name.toUpperCase()}</div>
                    <div className={`text-[10px] font-mono font-medium mt-0.5 ${riskBg[risk]}`}>{risk}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Live Camera Preview */}
      <div className="bg-card border border-border rounded">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Live Camera Preview</span>
          </div>
          <button onClick={() => onNavigate('cameras')} className="text-blue-400 hover:text-blue-300 text-[11px] font-medium transition-colors">
            Camera Grid →
          </button>
        </div>
        <div className="p-3 grid grid-cols-2 lg:grid-cols-4 gap-3">
          {previewCameras.map(cam => (
            <div key={cam.camera_id} className="border border-border rounded overflow-hidden">
              <CCTVPlaceholder
                cameraId={cam.camera_id}
                status={cam.status}
                peopleCount={cam.people_count}
                risk={cam.risk}
                className="h-28"
              />
              <div className="px-2 py-1.5 bg-card">
                <div className="text-slate-200 text-[11px] font-medium truncate">{cam.name}</div>
                <div className="flex items-center justify-between mt-0.5">
                  <span className="text-slate-500 text-[10px] font-mono">{cam.zone_name}</span>
                  <span className="text-[10px] font-mono text-slate-500">{cam.last_update}</span>
                </div>
                {cam.latest_event && cam.latest_event !== 'Normal activity' && (
                  <div className="text-[10px] text-slate-400 mt-0.5 truncate">{cam.latest_event}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

