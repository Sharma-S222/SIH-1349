import { useEffect, useState } from 'react';
import { Bell, ChevronDown, AlertTriangle, RefreshCw, Wifi, WifiOff, User } from 'lucide-react';
import type { WsStatus } from '../../types/ui';

interface HeaderProps {
  wsStatus: WsStatus;
  newAlertCount: number;
  onToggleWs?: () => void;
}

export function Header({ wsStatus, newAlertCount }: HeaderProps) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const dateStr = now.toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

  return (
    <header className="flex-shrink-0 h-12 flex items-center justify-between px-4 bg-[#090e18] border-b border-white/10 z-10">
      <div className="flex items-center gap-4">
        <div>
          <span className="text-slate-200 text-sm font-semibold tracking-wide">Railway AI Command Center</span>
          <span className="mx-2 text-slate-600">·</span>
          <span className="text-slate-400 text-sm">Station:</span>
          <span className="text-slate-200 text-sm font-medium ml-1">Demo Junction</span>
        </div>

        <span className="bg-blue-600/20 text-blue-300 text-[10px] font-mono px-2 py-0.5 rounded border border-blue-600/30 tracking-wider">
          DEMO DATA
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <div className="text-slate-200 font-mono text-sm leading-none">{timeStr}</div>
          <div className="text-slate-500 text-[11px] mt-0.5">{dateStr}</div>
        </div>

        <div className="flex items-center gap-2">
          {wsStatus === 'CONNECTED' && (
            <div className="flex items-center gap-1.5 bg-green-700/20 border border-green-700/40 px-2 py-1 rounded text-green-400 text-[11px] font-mono tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              SYSTEM ONLINE
            </div>
          )}
          {wsStatus === 'CONNECTING' && (
            <div className="flex items-center gap-1.5 bg-amber-700/20 border border-amber-700/40 px-2 py-1 rounded text-amber-400 text-[11px] font-mono tracking-wide">
              <RefreshCw size={11} className="animate-spin" />
              CONNECTING
            </div>
          )}
          {wsStatus === 'DISCONNECTED' && (
            <div className="flex items-center gap-1.5 bg-red-700/20 border border-red-700/40 px-2 py-1 rounded text-red-400 text-[11px] font-mono tracking-wide">
              <AlertTriangle size={11} />
              BACKEND OFFLINE
            </div>
          )}
          {wsStatus === 'RECONNECTING' && (
            <div className="flex items-center gap-1.5 bg-amber-700/20 border border-amber-700/40 px-2 py-1 rounded text-amber-400 text-[11px] font-mono tracking-wide">
              <RefreshCw size={11} className="animate-spin" />
              RECONNECTING
            </div>
          )}
        </div>

        {wsStatus === 'CONNECTED' && (
          <div className="flex items-center gap-1 bg-green-700/15 px-2 py-1 rounded text-green-400 text-[11px] font-mono">
            <Wifi size={12} />
            LIVE DATA
          </div>
        )}
        {(wsStatus === 'DISCONNECTED' || wsStatus === 'RECONNECTING') && (
          <div className="flex items-center gap-1 bg-slate-700/30 px-2 py-1 rounded text-slate-400 text-[11px] font-mono">
            <WifiOff size={12} />
            LAST KNOWN
          </div>
        )}

        <button className="relative text-slate-400 hover:text-slate-200 p-1.5 rounded hover:bg-white/5 transition-colors">
          <Bell size={16} />
          {newAlertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-600 text-white text-[9px] font-mono flex items-center justify-center">
              {newAlertCount > 9 ? '9+' : newAlertCount}
            </span>
          )}
        </button>

        <div className="flex items-center gap-2 pl-2 border-l border-white/10 cursor-pointer hover:bg-white/5 px-2 py-1 rounded transition-colors">
          <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center">
            <User size={14} className="text-slate-300" />
          </div>
          <div className="hidden sm:block">
            <div className="text-[12px] text-slate-200 font-medium leading-none">operator_01</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Senior Operator</div>
          </div>
          <ChevronDown size={12} className="text-slate-500" />
        </div>
      </div>
    </header>
  );
}
