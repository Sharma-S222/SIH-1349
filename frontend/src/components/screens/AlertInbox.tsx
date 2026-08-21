import { useState } from 'react';
import { Search, X, ArrowUpDown, Bell } from 'lucide-react';
import type { RailwayEvent, EventSeverity, EventStatus } from '../../types/ui';
import { SeverityBadge, severityBorderColor } from '../shared/SeverityBadge';

const SEVERITY_FILTERS: (EventSeverity | 'ALL')[] = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const STATUS_FILTERS: (EventStatus | 'ALL')[] = ['ALL', 'NEW', 'VERIFIED', 'ASSIGNED', 'RESOLVED', 'DISMISSED'];

interface AlertInboxProps {
  events: RailwayEvent[];
  onViewIncident: (id: string) => void;
}

export function AlertInbox({ events, onViewIncident }: AlertInboxProps) {
  const [severityFilter, setSeverityFilter] = useState<EventSeverity | 'ALL'>('ALL');
  const [statusFilter, setStatusFilter] = useState<EventStatus | 'ALL'>('ALL');
  const [cameraFilter, setCameraFilter] = useState('ALL');
  const [zoneFilter, setZoneFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'newest' | 'severity'>('newest');

  const cameras = ['ALL', ...Array.from(new Set(events.map(e => e.camera_id)))];
  const zones = ['ALL', ...Array.from(new Set(events.map(e => e.zone_name)))];

  const severityOrder: Record<EventSeverity, number> = { CRITICAL: 3, HIGH: 2, MEDIUM: 1, LOW: 0 };

  const filtered = events
    .filter(e => {
      if (severityFilter !== 'ALL' && e.severity !== severityFilter) return false;
      if (statusFilter !== 'ALL' && e.status !== statusFilter) return false;
      if (cameraFilter !== 'ALL' && e.camera_id !== cameraFilter) return false;
      if (zoneFilter !== 'ALL' && e.zone_name !== zoneFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return e.event_label.toLowerCase().includes(q) ||
          e.camera_id.toLowerCase().includes(q) ||
          e.zone_name.toLowerCase().includes(q) ||
          e.event_id.toLowerCase().includes(q);
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'severity') return severityOrder[b.severity] - severityOrder[a.severity];
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });

  function formatTime(isoStr: string) {
    return new Date(isoStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }

  function formatDate(isoStr: string) {
    const d = new Date(isoStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    return formatTime(isoStr);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border bg-card/50">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search alerts..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-muted border border-border rounded pl-8 pr-3 py-1.5 text-[12px] text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-ring w-44"
            />
            {search && <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"><X size={12} /></button>}
          </div>

          <select value={cameraFilter} onChange={e => setCameraFilter(e.target.value)} className="bg-muted border border-border rounded px-2 py-1.5 text-[12px] text-slate-300 focus:outline-none focus:ring-1 focus:ring-ring">
            {cameras.map(c => <option key={c} value={c}>{c === 'ALL' ? 'All Cameras' : c}</option>)}
          </select>

          <select value={zoneFilter} onChange={e => setZoneFilter(e.target.value)} className="bg-muted border border-border rounded px-2 py-1.5 text-[12px] text-slate-300 focus:outline-none focus:ring-1 focus:ring-ring">
            {zones.map(z => <option key={z} value={z}>{z === 'ALL' ? 'All Zones' : z}</option>)}
          </select>

          <div className="ml-auto flex items-center gap-2">
            <span className="text-slate-500 text-[11px] font-mono">{filtered.length} alerts</span>
            <button
              onClick={() => setSortBy(s => s === 'newest' ? 'severity' : 'newest')}
              className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-slate-200 bg-muted border border-border rounded px-2 py-1.5 transition-colors"
            >
              <ArrowUpDown size={12} />
              {sortBy === 'newest' ? 'Newest first' : 'Highest severity'}
            </button>
          </div>
        </div>

        {/* Severity filter chips */}
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <span className="text-slate-600 text-[11px]">Severity:</span>
          {SEVERITY_FILTERS.map(s => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
                severityFilter === s
                  ? s === 'CRITICAL' ? 'bg-red-600/30 text-red-300 border-red-600/50' :
                    s === 'HIGH' ? 'bg-orange-600/30 text-orange-300 border-orange-600/50' :
                    s === 'MEDIUM' ? 'bg-amber-600/30 text-amber-300 border-amber-600/50' :
                    s === 'LOW' ? 'bg-green-700/30 text-green-300 border-green-700/50' :
                    'bg-blue-600/30 text-blue-300 border-blue-600/50'
                  : 'border-border text-slate-500 hover:text-slate-300 hover:border-slate-600'
              }`}
            >
              {s}
            </button>
          ))}

          <span className="text-slate-600 text-[11px] ml-2">Status:</span>
          {STATUS_FILTERS.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
                statusFilter === s
                  ? 'bg-blue-600/30 text-blue-300 border-blue-600/50'
                  : 'border-border text-slate-500 hover:text-slate-300 hover:border-slate-600'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40">
            <Bell size={24} className="text-slate-600 mb-2" />
            <p className="text-slate-500 text-sm">No active safety alerts</p>
            <p className="text-slate-600 text-xs mt-1">Railway operations are currently clear.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filtered.map(alert => (
              <div
                key={alert.event_id}
                className={`flex items-start gap-3 px-4 py-3 border-l-2 hover:bg-white/3 transition-colors ${severityBorderColor(alert.severity)}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <SeverityBadge severity={alert.severity} />
                    <span className="text-slate-200 text-[13px] font-medium">{alert.event_label}</span>
                    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                      alert.status === 'NEW' ? 'bg-blue-600/20 text-blue-400 border-blue-600/30' :
                      alert.status === 'VERIFIED' ? 'bg-green-700/20 text-green-400 border-green-700/30' :
                      alert.status === 'ASSIGNED' ? 'bg-purple-700/20 text-purple-400 border-purple-700/30' :
                      alert.status === 'RESOLVED' ? 'bg-slate-700/30 text-slate-400 border-slate-600/30' :
                      'bg-slate-700/20 text-slate-500 border-slate-700/30'
                    }`}>{alert.status}</span>
                  </div>

                  <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                    <span className="text-[11px] text-slate-500 font-mono">{alert.camera_id}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-[11px] text-slate-500">{alert.zone_name}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-[11px] text-slate-500 font-mono">{formatTime(alert.timestamp)}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-[11px] text-slate-600">Confidence {Math.round(alert.confidence * 100)}%</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-[11px] text-slate-600 font-mono">{alert.people_count} people</span>
                  </div>

                  {alert.status === 'ASSIGNED' && alert.assigned_unit && (
                    <div className="mt-1 text-[11px] text-purple-400 font-mono">Assigned → {alert.assigned_unit}</div>
                  )}
                  {alert.status === 'RESOLVED' && alert.resolved_at && (
                    <div className="mt-1 text-[11px] text-slate-500">Resolved at {formatTime(alert.resolved_at)}</div>
                  )}
                </div>

                <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
                  <span className="text-[10px] text-slate-600 font-mono">{formatDate(alert.timestamp)}</span>
                  <button
                    onClick={() => onViewIncident(alert.event_id)}
                    className="text-[11px] text-blue-400 hover:text-blue-300 font-medium transition-colors px-2 py-1 rounded hover:bg-blue-600/10 border border-transparent hover:border-blue-600/20"
                  >
                    View Incident →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
