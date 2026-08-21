import { useState } from 'react';
import { CheckCircle, XCircle, UserPlus, CheckCheck, Clock, ChevronRight, X } from 'lucide-react';
import type { RailwayEvent, AssignPayload } from '../../types/ui';
import { SeverityBadge, severityBorderColor } from '../shared/SeverityBadge';
import { CCTVPlaceholder } from '../shared/CCTVPlaceholder';
import { CAMERAS } from '../../data/mockData';

interface IncidentDetailProps {
  events: RailwayEvent[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onVerify: (id: string) => void;
  onDismiss: (id: string) => void;
  onAssign: (id: string, payload: AssignPayload) => void;
  onResolve: (id: string) => void;
}

const RESPONSE_UNITS = ['RPF Team 1', 'RPF Team 2', 'Security Team A', 'Security Team B', 'Medical Team', 'Fire Safety Unit'];
const OPERATORS = ['operator_01', 'operator_02', 'operator_03', 'supervisor_01'];

export function IncidentDetail({ events, selectedId, onSelect, onVerify, onDismiss, onAssign, onResolve }: IncidentDetailProps) {
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showDismissConfirm, setShowDismissConfirm] = useState(false);
  const [showResolveConfirm, setShowResolveConfirm] = useState(false);
  const [assignUnit, setAssignUnit] = useState(RESPONSE_UNITS[0]);
  const [assignOperator, setAssignOperator] = useState(OPERATORS[0]);
  const [assignNote, setAssignNote] = useState('');

  const incident = events.find(e => e.event_id === selectedId);
  const camera = incident ? CAMERAS.find(c => c.camera_id === incident.camera_id) : null;

  const activeIncidents = events.filter(e => e.status !== 'DISMISSED');

  function formatTime(isoStr?: string) {
    if (!isoStr) return '—';
    return new Date(isoStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }

  function calcElapsed(start: string, end?: string) {
    const s = new Date(start);
    const e = end ? new Date(end) : new Date();
    const diff = Math.floor((e.getTime() - s.getTime()) / 1000);
    const m = Math.floor(diff / 60);
    const s2 = diff % 60;
    return `${String(m).padStart(2, '0')}:${String(s2).padStart(2, '0')}`;
  }

  function getTimeline(e: RailwayEvent) {
    const entries = [
      { time: formatTime(e.timestamp), label: 'AI event detected', actor: 'AI System' },
      { time: formatTime(e.timestamp), label: 'Incident created', actor: 'System' },
    ];
    if (e.verified_at) entries.push({ time: formatTime(e.verified_at), label: `Operator verified`, actor: e.verified_by ?? 'operator' });
    if (e.assigned_at) entries.push({ time: formatTime(e.assigned_at), label: `Assigned to ${e.assigned_unit}`, actor: e.assigned_to ?? 'operator' });
    if (e.resolved_at) entries.push({ time: formatTime(e.resolved_at), label: 'Incident resolved', actor: 'operator' });
    if (e.dismissed_at) entries.push({ time: formatTime(e.dismissed_at), label: 'Dismissed', actor: 'operator' });
    return entries;
  }

  return (
    <div className="flex h-full">
      {/* Left: incident list */}
      <div className="w-64 flex-shrink-0 border-r border-border flex flex-col">
        <div className="px-3 py-2.5 border-b border-border">
          <span className="text-slate-400 text-[11px] uppercase tracking-wider font-medium">All Incidents</span>
          <span className="ml-2 text-[10px] font-mono text-slate-600">{activeIncidents.length} total</span>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-border">
          {activeIncidents.map(e => (
            <button
              key={e.event_id}
              onClick={() => onSelect(e.event_id)}
              className={`w-full text-left px-3 py-2.5 border-l-2 transition-colors hover:bg-white/3 ${
                selectedId === e.event_id ? 'bg-blue-600/10 border-l-blue-500' : severityBorderColor(e.severity)
              }`}
            >
              <div className="flex items-center justify-between gap-1">
                <SeverityBadge severity={e.severity} size="sm" />
                <span className={`text-[10px] font-mono ${
                  e.status === 'NEW' ? 'text-blue-400' :
                  e.status === 'VERIFIED' ? 'text-green-400' :
                  e.status === 'ASSIGNED' ? 'text-purple-400' :
                  e.status === 'RESOLVED' ? 'text-slate-500' : 'text-slate-600'
                }`}>{e.status}</span>
              </div>
              <div className="text-slate-300 text-[12px] mt-0.5 line-clamp-1">{e.event_label}</div>
              <div className="text-slate-600 text-[10px] font-mono mt-0.5">{e.camera_id} · {formatTime(e.timestamp)}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Right: detail panel */}
      <div className="flex-1 overflow-auto">
        {!incident ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <ChevronRight size={24} className="mb-2 opacity-40 rotate-180" />
            <p className="text-sm">Select an incident to view details</p>
          </div>
        ) : (
          <div className="p-4 max-w-3xl space-y-4">
            {/* Header */}
            <div className={`bg-card border border-border rounded p-4 border-l-4 ${severityBorderColor(incident.severity).replace('border-l-', 'border-l-')}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <SeverityBadge severity={incident.severity} size="lg" />
                    <span className={`text-[11px] font-mono px-1.5 py-0.5 rounded border ${
                      incident.status === 'NEW' ? 'bg-blue-600/20 text-blue-400 border-blue-600/30' :
                      incident.status === 'VERIFIED' ? 'bg-green-700/20 text-green-400 border-green-700/30' :
                      incident.status === 'ASSIGNED' ? 'bg-purple-700/20 text-purple-400 border-purple-700/30' :
                      incident.status === 'RESOLVED' ? 'bg-slate-700/30 text-slate-300 border-slate-600/30' :
                      'bg-slate-700/20 text-slate-500 border-slate-700/30'
                    }`}>{incident.status}</span>
                  </div>
                  <h2 className="text-slate-100 mt-2 leading-tight">{incident.event_label}</h2>
                  <div className="flex items-center gap-2 mt-1 text-slate-500 text-[12px]">
                    <span className="font-mono">{incident.camera_id}</span>
                    <span>·</span>
                    <span>{incident.zone_name}</span>
                    <span>·</span>
                    <span className="font-mono">{formatTime(incident.timestamp)}</span>
                  </div>
                </div>
                <div className="text-right text-[11px] text-slate-500">
                  <div className="font-mono">{incident.event_id}</div>
                  <div className="mt-0.5">Confidence {Math.round(incident.confidence * 100)}%</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Evidence */}
              <div className="bg-card border border-border rounded overflow-hidden">
                <div className="px-3 py-2 border-b border-border">
                  <span className="text-slate-400 text-[12px] font-semibold uppercase tracking-wider">Evidence</span>
                </div>
                <CCTVPlaceholder
                  cameraId={incident.camera_id}
                  status={camera?.status ?? 'ONLINE'}
                  peopleCount={incident.people_count}
                  risk={incident.severity}
                  className="h-44"
                />
                <div className="p-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[11px]">
                  <MetaRow label="Event ID" value={incident.event_id} mono />
                  <MetaRow label="Camera" value={incident.camera_id} mono />
                  <MetaRow label="Zone" value={incident.zone_name} />
                  <MetaRow label="Confidence" value={`${Math.round(incident.confidence * 100)}%`} mono />
                  <MetaRow label="Detected" value={formatTime(incident.timestamp)} mono />
                  <MetaRow label="People" value={String(incident.people_count)} mono />
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-card border border-border rounded">
                <div className="px-3 py-2 border-b border-border">
                  <span className="text-slate-400 text-[12px] font-semibold uppercase tracking-wider">Timeline</span>
                </div>
                <div className="p-3 space-y-1">
                  {getTimeline(incident).map((entry, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-14 text-[11px] font-mono text-slate-500 mt-0.5">{entry.time}</div>
                      <div className="flex flex-col items-center mr-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                        {i < getTimeline(incident).length - 1 && <div className="w-px flex-1 bg-border min-h-4 mt-1" />}
                      </div>
                      <div className="flex-1 pb-2">
                        <div className="text-slate-200 text-[12px]">{entry.label}</div>
                        {entry.actor && <div className="text-slate-600 text-[10px] font-mono mt-0.5">{entry.actor}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Operator Actions */}
            <div className="bg-card border border-border rounded p-4">
              <div className="text-slate-400 text-[12px] font-semibold uppercase tracking-wider mb-3">Operator Actions</div>

              {incident.status === 'NEW' && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => onVerify(incident.event_id)}
                    className="flex items-center gap-2 bg-green-700/20 hover:bg-green-700/30 border border-green-700/40 text-green-300 px-4 py-2 rounded text-[12px] font-medium transition-colors"
                  >
                    <CheckCircle size={14} />
                    VERIFY
                  </button>
                  <button
                    onClick={() => setShowDismissConfirm(true)}
                    className="flex items-center gap-2 bg-slate-700/20 hover:bg-slate-700/40 border border-slate-600/40 text-slate-400 px-4 py-2 rounded text-[12px] font-medium transition-colors"
                  >
                    <XCircle size={14} />
                    DISMISS
                  </button>
                </div>
              )}

              {incident.status === 'VERIFIED' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCheck size={14} className="text-green-400" />
                    <span className="text-green-400 text-[12px] font-medium">VERIFIED</span>
                    {incident.verified_by && <span className="text-slate-500 text-[11px]">by {incident.verified_by}</span>}
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setShowAssignModal(true)}
                      className="flex items-center gap-2 bg-purple-700/20 hover:bg-purple-700/30 border border-purple-700/40 text-purple-300 px-4 py-2 rounded text-[12px] font-medium transition-colors"
                    >
                      <UserPlus size={14} />
                      ASSIGN RESPONSE TEAM
                    </button>
                    <button
                      onClick={() => setShowDismissConfirm(true)}
                      className="flex items-center gap-2 bg-slate-700/20 hover:bg-slate-700/40 border border-slate-600/40 text-slate-400 px-4 py-2 rounded text-[12px] font-medium transition-colors"
                    >
                      <XCircle size={14} />
                      DISMISS
                    </button>
                  </div>
                </div>
              )}

              {incident.status === 'ASSIGNED' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-purple-500" />
                      <span className="text-purple-300 text-[12px] font-medium">ASSIGNED</span>
                    </div>
                    <span className="text-slate-300 text-[12px]">{incident.assigned_unit}</span>
                    <div className="flex items-center gap-1 text-slate-500 text-[11px]">
                      <Clock size={11} />
                      <span className="font-mono">Elapsed: {calcElapsed(incident.assigned_at!)}</span>
                    </div>
                  </div>
                  {incident.assigned_note && (
                    <div className="text-[11px] text-slate-500 bg-muted rounded px-3 py-2 border border-border font-mono">
                      Note: {incident.assigned_note}
                    </div>
                  )}
                  <button
                    onClick={() => setShowResolveConfirm(true)}
                    className="flex items-center gap-2 bg-green-700/20 hover:bg-green-700/30 border border-green-700/40 text-green-300 px-4 py-2 rounded text-[12px] font-medium transition-colors"
                  >
                    <CheckCheck size={14} />
                    RESOLVE INCIDENT
                  </button>
                </div>
              )}

              {incident.status === 'RESOLVED' && (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <CheckCheck size={14} className="text-green-400" />
                    <span className="text-green-400 text-[13px] font-medium">INCIDENT RESOLVED</span>
                  </div>
                  <div className="text-slate-500 text-[11px] font-mono">
                    Resolved: {formatTime(incident.resolved_at)}
                  </div>
                  {incident.assigned_at && incident.resolved_at && (
                    <div className="text-slate-500 text-[11px] font-mono">
                      Response Time: {calcElapsed(incident.assigned_at, incident.resolved_at)}
                    </div>
                  )}
                </div>
              )}

              {incident.status === 'DISMISSED' && (
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <XCircle size={14} className="text-slate-500" />
                    <span className="text-slate-400 text-[12px]">DISMISSED</span>
                  </div>
                  <div className="text-slate-600 text-[11px]">Removed from active priority queue.</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Assign Modal */}
      {showAssignModal && incident && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-card border border-border rounded w-full max-w-sm mx-4 shadow-xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="text-slate-200 text-[14px] font-semibold">Assign Response Team</span>
              <button onClick={() => setShowAssignModal(false)} className="text-slate-500 hover:text-slate-300 p-1 rounded hover:bg-white/5">
                <X size={14} />
              </button>
            </div>
            <div className="p-4 space-y-3">
              <div>
                <label className="text-slate-400 text-[11px] uppercase tracking-wider block mb-1">Response Unit</label>
                <select
                  value={assignUnit}
                  onChange={e => setAssignUnit(e.target.value)}
                  className="w-full bg-muted border border-border rounded px-3 py-2 text-[13px] text-slate-200 focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {RESPONSE_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-[11px] uppercase tracking-wider block mb-1">Operator</label>
                <select
                  value={assignOperator}
                  onChange={e => setAssignOperator(e.target.value)}
                  className="w-full bg-muted border border-border rounded px-3 py-2 text-[13px] text-slate-200 focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {OPERATORS.map(o => <option key={o} value={o}>{o}</option>)}
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-[11px] uppercase tracking-wider block mb-1">Note (optional)</label>
                <textarea
                  value={assignNote}
                  onChange={e => setAssignNote(e.target.value)}
                  placeholder="e.g. Investigate Track Zone immediately"
                  rows={2}
                  className="w-full bg-muted border border-border rounded px-3 py-2 text-[13px] text-slate-200 placeholder:text-slate-600 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 px-4 pb-4">
              <button onClick={() => setShowAssignModal(false)} className="px-4 py-2 text-[12px] text-slate-400 hover:text-slate-200 border border-border rounded hover:bg-white/5 transition-colors">
                CANCEL
              </button>
              <button
                onClick={() => {
                  onAssign(incident.event_id, { unit: assignUnit, operator: assignOperator, note: assignNote });
                  setShowAssignModal(false);
                  setAssignNote('');
                }}
                className="px-4 py-2 text-[12px] bg-purple-700/30 hover:bg-purple-700/50 border border-purple-600/40 text-purple-200 rounded font-medium transition-colors"
              >
                ASSIGN
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dismiss Confirm */}
      {showDismissConfirm && incident && (
        <ConfirmDialog
          title="Dismiss Incident"
          message={`Dismiss "${incident.event_label}"? It will be removed from the active priority queue.`}
          confirmLabel="DISMISS"
          confirmClass="bg-slate-700/30 hover:bg-slate-700/50 border border-slate-600/40 text-slate-300"
          onConfirm={() => { onDismiss(incident.event_id); setShowDismissConfirm(false); }}
          onCancel={() => setShowDismissConfirm(false)}
        />
      )}

      {/* Resolve Confirm */}
      {showResolveConfirm && incident && (
        <ConfirmDialog
          title="Resolve Incident"
          message={`Mark "${incident.event_label}" as resolved? This will close the incident.`}
          confirmLabel="RESOLVE"
          confirmClass="bg-green-700/30 hover:bg-green-700/50 border border-green-700/40 text-green-200"
          onConfirm={() => { onResolve(incident.event_id); setShowResolveConfirm(false); }}
          onCancel={() => setShowResolveConfirm(false)}
        />
      )}
    </div>
  );
}

function MetaRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</div>
      <div className={`text-slate-300 mt-0.5 ${mono ? 'font-mono text-[11px]' : 'text-[12px]'}`}>{value}</div>
    </div>
  );
}

function ConfirmDialog({
  title, message, confirmLabel, confirmClass, onConfirm, onCancel,
}: {
  title: string; message: string; confirmLabel: string; confirmClass: string;
  onConfirm: () => void; onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-card border border-border rounded w-full max-w-sm mx-4 shadow-xl p-5">
        <h3 className="text-slate-200 text-[14px] font-semibold mb-2">{title}</h3>
        <p className="text-slate-400 text-[13px] mb-4">{message}</p>
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="px-4 py-2 text-[12px] text-slate-400 hover:text-slate-200 border border-border rounded hover:bg-white/5 transition-colors">
            CANCEL
          </button>
          <button onClick={onConfirm} className={`px-4 py-2 text-[12px] rounded font-medium transition-colors ${confirmClass}`}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
