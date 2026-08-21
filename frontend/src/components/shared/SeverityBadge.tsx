import type { EventSeverity, RiskLevel } from '../../types/ui';

const severityConfig: Record<string, { className: string; dot: string }> = {
  CRITICAL: { className: 'bg-red-600/20 text-red-400 border border-red-600/40', dot: 'bg-red-500' },
  HIGH: { className: 'bg-orange-600/20 text-orange-400 border border-orange-600/40', dot: 'bg-orange-500' },
  MEDIUM: { className: 'bg-amber-600/20 text-amber-400 border border-amber-600/40', dot: 'bg-amber-500' },
  LOW: { className: 'bg-green-700/20 text-green-400 border border-green-700/40', dot: 'bg-green-500' },
};

interface SeverityBadgeProps {
  severity: EventSeverity | RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export function SeverityBadge({ severity, size = 'md', showDot = true }: SeverityBadgeProps) {
  const config = severityConfig[severity] ?? severityConfig.LOW;
  const sizeClass =
    size === 'sm' ? 'text-[10px] px-1.5 py-0.5' :
    size === 'lg' ? 'text-sm px-3 py-1' :
    'text-[11px] px-2 py-0.5';

  return (
    <span className={`inline-flex items-center gap-1 rounded font-mono font-medium tracking-wider ${sizeClass} ${config.className}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${config.dot}`} />}
      {severity}
    </span>
  );
}

export function severityBorderColor(severity: EventSeverity | RiskLevel): string {
  const map: Record<string, string> = {
    CRITICAL: 'border-l-red-500',
    HIGH: 'border-l-orange-500',
    MEDIUM: 'border-l-amber-500',
    LOW: 'border-l-green-500',
  };
  return map[severity] ?? map.LOW;
}

export function severityTextColor(severity: EventSeverity | RiskLevel): string {
  const map: Record<string, string> = {
    CRITICAL: 'text-red-400',
    HIGH: 'text-orange-400',
    MEDIUM: 'text-amber-400',
    LOW: 'text-green-400',
  };
  return map[severity] ?? map.LOW;
}
