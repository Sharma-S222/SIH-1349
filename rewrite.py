import os
content = '''import { useState, useEffect } from 'react';
import { Video, VideoOff, AlertTriangle, Loader2 } from 'lucide-react';
import type { CameraStatus, RiskLevel } from '../../types/ui';

interface CCTVPlaceholderProps {
  cameraId: string;
  status: CameraStatus;
  sourceType?: string;
  peopleCount?: number;
  risk?: RiskLevel;
  className?: string;
  compact?: boolean;
}

export function CCTVPlaceholder({ cameraId, status, sourceType = 'VIDEO', peopleCount, risk, className = '', compact = false }: CCTVPlaceholderProps) {
  const isOffline = status === 'OFFLINE' || status === 'STALE';
  const isDegraded = status === 'DEGRADED';
  const isOnline = status === 'ONLINE';
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

  const [imgStatus, setImgStatus] = useState<'loading' | 'loaded' | 'error'>('loading');

  useEffect(() => {
    if (isOnline) {
      setImgStatus('loading');
    }
  }, [isOnline, cameraId]);

  let offlineMessage = "NOT CONNECTED";
  if (sourceType === 'VIDEO') {
    offlineMessage = "AWAITING VIDEO";
  }

  return (
    <div className={elative bg-[#060a10] overflow-hidden }>
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255,255,255,0.8) 3px, rgba(255,255,255,0.8) 4px)',
        }}
      />

      <div className="absolute inset-0 flex flex-col items-center justify-center z-10 pointer-events-none">
        {isOffline ? (
          <>
            <VideoOff className="text-slate-700" size={compact ? 20 : 28} />
            <span className="text-slate-600 font-mono text-[10px] mt-1.5 tracking-widest">{offlineMessage}</span>
          </>
        ) : isDegraded ? (
          <>
            <AlertTriangle className="text-amber-700/60" size={compact ? 20 : 28} />
            <span className="text-amber-700/60 font-mono text-[10px] mt-1.5 tracking-widest">SIGNAL DEGRADED</span>
          </>
        ) : (
          imgStatus === 'loading' ? (
            <>
              <Loader2 className="text-slate-600 animate-spin" size={compact ? 20 : 28} />
              <span className="text-slate-500 font-mono text-[10px] mt-1.5 tracking-widest">CONNECTING TO CAMERA...</span>
            </>
          ) : imgStatus === 'error' ? (
            <>
              <VideoOff className="text-red-900/60" size={compact ? 20 : 28} />
              <span className="text-red-800/60 font-mono text-[10px] mt-1.5 tracking-widest">CAMERA STREAM UNAVAILABLE</span>
            </>
          ) : null
        )}
      </div>

      {isOnline && (
        <img 
          src={${API_BASE_URL}/api/cameras//stream} 
          className={w-full h-full object-cover relative z-0 transition-opacity duration-300 } 
          alt={Camera  stream} 
          onLoad={() => setImgStatus('loaded')}
          onError={() => setImgStatus('error')}
        />
      )}

      {status === 'ONLINE' && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-green-700/80 px-1.5 py-0.5 rounded text-green-100 text-[10px] font-mono tracking-wide z-20">
          <span className="w-1.5 h-1.5 rounded-full bg-green-300 animate-pulse" />
          LIVE
        </div>
      )}
      {isDegraded && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-amber-700/80 px-1.5 py-0.5 rounded text-amber-100 text-[10px] font-mono tracking-wide z-20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-300" />
          DEGRADED
        </div>
      )}

      <div className="absolute top-2 right-2 text-[9px] font-mono text-slate-600/70 bg-black/50 px-1.5 py-0.5 rounded z-20">
        {cameraId}
      </div>

      {!isOffline && peopleCount !== undefined && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-2 py-1.5 z-20">
          <div className="flex items-center justify-between">
            <span className="text-white/90 text-[11px] font-mono">{peopleCount} PEOPLE</span>
            {risk && risk !== 'LOW' && (
              <span className={	ext-[9px] font-mono font-medium px-1.5 py-0.5 rounded }>{risk}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
'''
with open('frontend/src/components/shared/CCTVPlaceholder.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
