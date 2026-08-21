import {
  LayoutDashboard, Camera, Bell, FileText, Users, BarChart3, Activity,
  ChevronLeft, ChevronRight, Train,
} from 'lucide-react';
import type { ScreenName } from '../../types/ui';

const NAV_ITEMS: { id: ScreenName; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }[] = [
  { id: 'command-center', label: 'Command Center', icon: LayoutDashboard },
  { id: 'cameras', label: 'Cameras', icon: Camera },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'incidents', label: 'Incidents', icon: FileText },
  { id: 'crowd', label: 'Crowd Intelligence', icon: Users },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'system', label: 'System Status', icon: Activity },
];

interface SidebarProps {
  activeScreen: ScreenName;
  collapsed: boolean;
  onNavigate: (screen: ScreenName) => void;
  onToggle: () => void;
  alertCount?: number;
}

export function Sidebar({ activeScreen, collapsed, onNavigate, onToggle, alertCount = 0 }: SidebarProps) {
  return (
    <aside
      className={`flex flex-col flex-shrink-0 bg-sidebar border-r border-sidebar-border transition-all duration-200 ${collapsed ? 'w-14' : 'w-56'}`}
    >
      <div className={`flex items-center gap-2 px-3 py-3 border-b border-sidebar-border ${collapsed ? 'justify-center' : ''}`}>
        <div className="flex-shrink-0 w-7 h-7 rounded bg-blue-600/20 flex items-center justify-center">
          <Train size={14} className="text-blue-400" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="text-[11px] font-semibold text-slate-200 tracking-wide truncate">SIH1349</div>
            <div className="text-[10px] text-slate-500 font-mono tracking-wider">RAILWAY AI</div>
          </div>
        )}
      </div>

      <nav className="flex-1 py-2 overflow-y-auto overflow-x-hidden">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeScreen === item.id;
          const showBadge = item.id === 'alerts' && alertCount > 0;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2 text-left transition-colors
                focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring
                ${collapsed ? 'justify-center' : ''}
                ${isActive
                  ? 'bg-blue-600/15 text-blue-300 border-r-2 border-blue-500'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}
              `}
              title={collapsed ? item.label : undefined}
            >
              <div className="relative flex-shrink-0">
                <Icon size={16} className={isActive ? 'text-blue-400' : ''} />
                {showBadge && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500" />
                )}
              </div>
              {!collapsed && (
                <span className="text-[13px] font-medium truncate">{item.label}</span>
              )}
              {!collapsed && showBadge && (
                <span className="ml-auto flex-shrink-0 bg-red-600/80 text-red-100 text-[10px] font-mono px-1.5 py-0.5 rounded">
                  {alertCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-sidebar-border p-2">
        <button
          onClick={onToggle}
          className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-colors ${collapsed ? 'justify-center' : ''}`}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={15} /> : (
            <>
              <ChevronLeft size={15} />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
