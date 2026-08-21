import { Video, VideoOff, AlertTriangle } from 'lucide-react';
import type { CameraStatus, RiskLevel } from '../../types/ui';

interface CCTVPlaceholderProps {
  cameraId: string;
  status: CameraStatus;
  peopleCount?: number;
  risk?: RiskLevel;
  className?: string;
  compact?: boolean;
}

export function CCTVPlaceholder({ cameraId, status, peopleCount, risk, className = '', compact = false }: CCTVPlaceholderProps) {
  const isOffline = status === 'OFFLINE';
  const isDegraded = status === 'DEGRADED';
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

  return (
    <div className={`relative bg-[#060a10] overflow-hidden ${className}`}>
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255,255,255,0.8) 3px, rgba(255,255,255,0.8) 4px)',
        }}
      />

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {isOffline ? (
          <>
            <VideoOff className="text-slate-700" size={compact ? 20 : 28} />
            <span className="text-slate-600 font-mono text-[10px] mt-1.5 tracking-widest">NO SIGNAL</span>
          </>
        ) : isDegraded ? (
          <>
            <AlertTriangle className="text-amber-700/60" size={compact ? 20 : 28} />
            <span className="text-amber-700/60 font-mono text-[10px] mt-1.5 tracking-widest">SIGNAL DEGRADED</span>
          </>
        ) : (
          <>
            <img src={`${API_BASE_URL}/api/cameras/${cameraId}/stream`} className="w-full h-full object-cover" alt={`Camera ${cameraId} stream`} onError={(e) => { e.currentTarget.style.display = 'none'; }} />
            <Video className="text-slate-800 absolute -z-10" size={compact ? 20 : 28} />
          </>
        )}
      </div>

      {status === 'ONLINE' && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-green-700/80 px-1.5 py-0.5 rounded text-green-100 text-[10px] font-mono tracking-wide">
          <span className="w-1.5 h-1.5 rounded-full bg-green-300 animate-pulse" />
          LIVE
        </div>
      )}
      {isDegraded && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-amber-700/80 px-1.5 py-0.5 rounded text-amber-100 text-[10px] font-mono tracking-wide">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-300" />
          DEGRADED
        </div>
      )}
      {status === 'STALE' && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-slate-600/80 px-1.5 py-0.5 rounded text-slate-100 text-[10px] font-mono tracking-wide">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
          STALE
        </div>
      )}

      <div className="absolute top-2 right-2 text-[9px] font-mono text-slate-600/70 bg-black/50 px-1.5 py-0.5 rounded">
        {cameraId}
      </div>

      {!isOffline && peopleCount !== undefined && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-2 py-1.5">
          <div className="flex items-center justify-between">
            <span className="text-white/90 text-[11px] font-mono">{peopleCount} PEOPLE</span>
            {risk && risk !== 'LOW' && (
              <span className={`text-[9px] font-mono font-medium px-1.5 py-0.5 rounded ${
                risk === 'CRITICAL' ? 'bg-red-700/80 text-red-100' :
                risk === 'HIGH' ? 'bg-orange-700/80 text-orange-100' :
                'bg-amber-700/80 text-amber-100'
              }`}>{risk}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
