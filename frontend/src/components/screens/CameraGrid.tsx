import { useState, useEffect } from 'react';
import { Search, X, Users, Clock, Radio, Grid2X2, Grid3X3 } from 'lucide-react';
import type { Camera, CameraStatus, RiskLevel } from '../../types/ui';
import { CAMERAS } from '../../data/mockData';
import { SeverityBadge } from '../shared/SeverityBadge';
import { CCTVPlaceholder } from '../shared/CCTVPlaceholder';

const STATUS_OPTIONS: { value: CameraStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All Status' },
  { value: 'ONLINE', label: 'Online' },
  { value: 'OFFLINE', label: 'Offline' },
  { value: 'DEGRADED', label: 'Degraded' },
  { value: 'STALE', label: 'Stale' },
];

const RISK_OPTIONS: { value: RiskLevel | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All Risk' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
];

const statusDot: Record<CameraStatus, string> = {
  ONLINE: 'bg-green-500',
  OFFLINE: 'bg-red-500',
  DEGRADED: 'bg-amber-500',
  STALE: 'bg-slate-500',
};

const statusText: Record<CameraStatus, string> = {
  ONLINE: 'text-green-400',
  OFFLINE: 'text-red-400',
  DEGRADED: 'text-amber-400',
  STALE: 'text-slate-400',
};

interface CameraGridProps {
  onViewIncident?: (id: string) => void;
}

export function CameraGrid(_props: CameraGridProps) {
  const [search, setSearch] = useState('');
  const [zoneFilter, setZoneFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState<CameraStatus | 'ALL'>('ALL');
  const [riskFilter, setRiskFilter] = useState<RiskLevel | 'ALL'>('ALL');
  const [columns, setColumns] = useState<2 | 3 | 4>(3);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [camerasData, setCamerasData] = useState<Camera[]>(CAMERAS);

  useEffect(() => {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
    let active = true;
    const fetchCameras = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/cameras`);
        const json = await res.json();
        if (active && json.ok) {
          const liveData = json.data as any[];
          setCamerasData(prev => prev.map(cam => {
            const live = liveData.find((l: any) => l.camera_id === cam.camera_id);
            if (live) {
              return {
                ...cam,
                status: live.status,
                people_count: live.people_count,
                last_update: "Just now",
                latest_event: live.telemetry.status === "PROCESSING" 
                  ? `Fps: ${live.telemetry.pipeline_fps} | Tracks: ${live.telemetry.active_tracks}` 
                  : cam.latest_event,
                telemetry: live.telemetry,
              };
            }
            return cam;
          }));
          
          setSelectedCamera(prev => {
            if (!prev) return null;
            const live = liveData.find((l: any) => l.camera_id === prev.camera_id);
            if (live) {
              return {
                ...prev,
                status: live.status,
                people_count: live.people_count,
                last_update: "Just now",
                latest_event: live.telemetry.status === "PROCESSING" 
                  ? `Fps: ${live.telemetry.pipeline_fps} | Tracks: ${live.telemetry.active_tracks}` 
                  : prev.latest_event,
                telemetry: live.telemetry,
              };
            }
            return prev;
          });
        }
      } catch (e) {
        console.error("Failed to fetch camera telemetry", e);
      }
    };
    
    fetchCameras();
    const interval = setInterval(fetchCameras, 2000);
    return () => { active = false; clearInterval(interval); };
  }, []);

  const zones = ['ALL', ...Array.from(new Set(camerasData.map(c => c.zone_name)))];

  const filtered = camerasData.filter(cam => {
    if (search && !cam.name.toLowerCase().includes(search.toLowerCase()) && !cam.camera_id.toLowerCase().includes(search.toLowerCase())) return false;
    if (zoneFilter !== 'ALL' && cam.zone_name !== zoneFilter) return false;
    if (statusFilter !== 'ALL' && cam.status !== statusFilter) return false;
    if (riskFilter !== 'ALL' && cam.risk !== riskFilter) return false;
    return true;
  });

  const gridCols = columns === 2 ? 'grid-cols-2' : columns === 3 ? 'grid-cols-3' : 'grid-cols-4';

  return (
    <div className="flex flex-col h-full">
      {/* Filter bar */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border bg-card/50 flex items-center gap-3 flex-wrap">
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search cameras..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-muted border border-border rounded pl-8 pr-3 py-1.5 text-[12px] text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-ring w-44"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
              <X size={12} />
            </button>
          )}
        </div>

        <select
          value={zoneFilter}
          onChange={e => setZoneFilter(e.target.value)}
          className="bg-muted border border-border rounded px-2 py-1.5 text-[12px] text-slate-300 focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {zones.map(z => <option key={z} value={z}>{z === 'ALL' ? 'All Zones' : z}</option>)}
        </select>

        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as CameraStatus | 'ALL')}
          className="bg-muted border border-border rounded px-2 py-1.5 text-[12px] text-slate-300 focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <select
          value={riskFilter}
          onChange={e => setRiskFilter(e.target.value as RiskLevel | 'ALL')}
          className="bg-muted border border-border rounded px-2 py-1.5 text-[12px] text-slate-300 focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {RISK_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <span className="text-slate-500 text-[11px] font-mono ml-2">{filtered.length} cameras</span>

        <div className="ml-auto flex items-center gap-1">
          {([2, 3, 4] as const).map(n => (
            <button
              key={n}
              onClick={() => setColumns(n)}
              className={`p-1.5 rounded transition-colors ${columns === n ? 'bg-blue-600/20 text-blue-400' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'}`}
            >
              {n === 2 ? <Grid2X2 size={15} /> : n === 3 ? <Grid3X3 size={15} /> : <Grid3X3 size={15} />}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto flex">
        {/* Camera grid */}
        <div className="flex-1 p-4 overflow-auto">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-slate-500">
              <Radio size={24} className="mb-2 opacity-40" />
              <p className="text-sm">No camera sources match filters.</p>
            </div>
          ) : (
            <div className={`grid ${gridCols} gap-3`}>
              {filtered.map(cam => (
                <button
                  key={cam.camera_id}
                  onClick={() => setSelectedCamera(cam)}
                  className={`text-left border rounded overflow-hidden transition-all hover:border-slate-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring ${
                    selectedCamera?.camera_id === cam.camera_id ? 'border-blue-500 ring-1 ring-blue-500/30' : 'border-border'
                  }`}
                >
                  <CCTVPlaceholder
                    cameraId={cam.camera_id}
                    status={cam.status}
                    sourceType={cam.source_type}
                    peopleCount={cam.people_count}
                    risk={cam.risk}
                    className="h-32"
                  />
                  <div className="p-2 bg-card">
                    <div className="flex items-start justify-between gap-1">
                      <div className="min-w-0">
                        <div className="text-slate-200 text-[12px] font-medium truncate">{cam.name}</div>
                        <div className="text-slate-500 text-[10px] font-mono mt-0.5 truncate">{cam.zone_name}</div>
                      </div>
                      <SeverityBadge severity={cam.risk} size="sm" />
                    </div>
                    <div className="flex items-center justify-between mt-1.5">
                      <div className="flex items-center gap-1">
                        <span className={`w-1.5 h-1.5 rounded-full ${statusDot[cam.status]}`} />
                        <span className={`text-[10px] font-mono ${statusText[cam.status]}`}>
                          {cam.status === 'ONLINE' ? (cam.source_type === 'VIDEO' ? 'PROCESSING' : 'LIVE') : cam.status}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-600">{cam.last_update}</span>
                    </div>
                    {cam.latest_event && cam.latest_event !== 'Normal activity' && (
                      <div className="text-[10px] text-slate-400 mt-1 truncate">{cam.latest_event}</div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Camera detail drawer */}
        {selectedCamera && (
          <div className="w-72 flex-shrink-0 border-l border-border bg-card flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-3 py-2.5 border-b border-border">
              <div>
                <div className="text-slate-200 text-[13px] font-semibold">{selectedCamera.camera_id}</div>
                <div className="text-slate-500 text-[11px] font-mono">{selectedCamera.name}</div>
              </div>
              <button onClick={() => setSelectedCamera(null)} className="text-slate-500 hover:text-slate-300 p-1 rounded hover:bg-white/5">
                <X size={14} />
              </button>
            </div>

            <CCTVPlaceholder
              cameraId={selectedCamera.camera_id}
              status={selectedCamera.status}
              sourceType={selectedCamera.source_type}
              peopleCount={selectedCamera.people_count}
              risk={selectedCamera.risk}
              className="h-40 flex-shrink-0"
            />

            <div className="p-3 space-y-3 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-2">
                <Stat label="Status">
                  <div className="flex items-center gap-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${statusDot[selectedCamera.status]}`} />
                    <span className={`text-[12px] font-mono ${statusText[selectedCamera.status]}`}>
                      {selectedCamera.status === 'ONLINE' ? (selectedCamera.source_type === 'VIDEO' ? 'PROCESSING' : 'LIVE') : selectedCamera.status}
                    </span>
                  </div>
                </Stat>
                <Stat label="Risk Level">
                  <SeverityBadge severity={selectedCamera.risk} size="sm" />
                </Stat>
                <Stat label="People Count">
                  <div className="flex items-center gap-1 text-slate-200 text-[12px]">
                    <Users size={11} className="text-slate-500" />
                    <span className="font-mono">{selectedCamera.people_count}</span>
                  </div>
                </Stat>
                <Stat label="Last Update">
                  <div className="flex items-center gap-1 text-slate-400 text-[11px]">
                    <Clock size={11} />
                    <span className="font-mono">{selectedCamera.last_update}</span>
                  </div>
                </Stat>
              </div>

              {selectedCamera.telemetry && selectedCamera.telemetry.status === "PROCESSING" && (
                <div className="space-y-3 pt-3 border-t border-border">
                  <div className="flex items-center justify-between">
                     <span className="text-slate-200 text-[12px] font-medium flex items-center gap-1"><Radio size={13} className="text-blue-400" /> AI DETECTIONS</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="flex justify-between bg-black/20 p-1.5 rounded">
                      <span className="text-slate-400">People</span>
                      <span className="text-slate-200 font-mono">{selectedCamera.telemetry.people_count}</span>
                    </div>
                    {Object.entries(selectedCamera.telemetry.objects || {}).map(([objName, count]: [string, any]) => (
                      <div key={objName} className="flex justify-between bg-black/20 p-1.5 rounded">
                        <span className="text-slate-400 capitalize">{objName}</span>
                        <span className="text-slate-200 font-mono">{count}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between bg-black/20 p-1.5 rounded text-[11px]">
                    <span className="text-slate-400">Active Tracks</span>
                    <span className="text-slate-200 font-mono">{selectedCamera.telemetry.active_tracks}</span>
                  </div>

                  <div className="flex justify-between bg-black/20 p-1.5 rounded text-[11px]">
                    <span className="text-slate-400">Inference</span>
                    <span className="text-slate-200 font-mono">{selectedCamera.telemetry.inference_ms} ms</span>
                  </div>

                  <div className="flex justify-between bg-black/20 p-1.5 rounded text-[11px]">
                    <span className="text-slate-400">Pipeline FPS</span>
                    <span className="text-slate-200 font-mono">{selectedCamera.telemetry.pipeline_fps}</span>
                  </div>
                </div>
              )}

              <div>
                <div className="text-slate-500 text-[10px] uppercase tracking-wider mb-1">Zone</div>
                <div className="text-slate-200 text-[12px]">{selectedCamera.zone_name}</div>
              </div>

              <div>
                <div className="text-slate-500 text-[10px] uppercase tracking-wider mb-1">Latest Event</div>
                <div className={`text-[12px] ${
                  selectedCamera.latest_event?.includes('Normal') ? 'text-slate-500' : 'text-slate-300'
                }`}>{selectedCamera.latest_event ?? 'None'}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">{label}</div>
      {children}
    </div>
  );
}
