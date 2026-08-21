import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell,
} from 'recharts';
import { INCIDENT_TREND, INCIDENT_CATEGORIES, SEVERITY_DISTRIBUTION, BUSIEST_ZONES, RESPONSE_STATS } from '../../data/mockData';
import { Clock, TrendingUp, CheckCircle } from 'lucide-react';

const BAR_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#22c55e', '#3b82f6', '#a78bfa'];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#1a2236] border border-white/10 rounded p-2 text-[11px]">
      <div className="text-slate-400 font-mono mb-1">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} className="text-slate-200 font-mono">{p.name}: {p.value}</div>
      ))}
    </div>
  );
};

export function Analytics() {
  const totalIncidents = INCIDENT_CATEGORIES.reduce((s, c) => s + c.count, 0);
  const maxBusy = Math.max(...BUSIEST_ZONES.map(z => z.incidents));

  return (
    <div className="p-4 space-y-4">
      {/* Response Performance */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Total Incidents Today" value={String(RESPONSE_STATS.totalToday)} icon={<TrendingUp size={14} className="text-slate-500" />} />
        <StatCard label="Avg Verification Time" value={RESPONSE_STATS.avgVerification} mono icon={<Clock size={14} className="text-slate-500" />} />
        <StatCard label="Avg Assignment Time" value={RESPONSE_STATS.avgAssignment} mono icon={<Clock size={14} className="text-slate-500" />} />
        <StatCard label="Avg Resolution Time" value={RESPONSE_STATS.avgResolution} mono icon={<CheckCircle size={14} className="text-slate-500" />} />
      </div>

      {/* Incident Trend chart */}
      <div className="bg-card border border-border rounded">
        <div className="px-4 py-2.5 border-b border-border">
          <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Incident Trend — Today (per hour)</span>
        </div>
        <div className="p-3 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={INCIDENT_TREND} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="rgba(148,163,184,0.07)" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="hour"
                tick={{ fill: '#475569', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fill: '#475569', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Incidents" radius={[2, 2, 0, 0]}>
                {INCIDENT_TREND.map((entry, i) => (
                  <Cell key={i} fill={entry.count >= 10 ? '#ef4444' : entry.count >= 7 ? '#f97316' : entry.count >= 4 ? '#f59e0b' : '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category breakdown + Severity dist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Category breakdown */}
        <div className="bg-card border border-border rounded">
          <div className="px-4 py-2.5 border-b border-border">
            <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Incident Breakdown</span>
            <span className="text-slate-500 text-[11px] ml-2">{totalIncidents} total</span>
          </div>
          <div className="p-3 space-y-2">
            {INCIDENT_CATEGORIES.map((cat, i) => (
              <div key={cat.name}>
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-slate-300 text-[12px]">{cat.name}</span>
                  <span className="text-slate-400 text-[11px] font-mono">{cat.count}</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(cat.count / totalIncidents) * 100}%`,
                      backgroundColor: BAR_COLORS[i % BAR_COLORS.length],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Severity distribution */}
        <div className="bg-card border border-border rounded">
          <div className="px-4 py-2.5 border-b border-border">
            <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Severity Distribution</span>
          </div>
          <div className="p-3 space-y-2">
            {SEVERITY_DISTRIBUTION.map(sev => {
              const total = SEVERITY_DISTRIBUTION.reduce((s, x) => s + x.count, 0);
              return (
                <div key={sev.name}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-[11px] font-mono font-medium" style={{ color: sev.color }}>{sev.name}</span>
                    <span className="text-slate-400 text-[11px] font-mono">{sev.count} ({Math.round((sev.count / total) * 100)}%)</span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${(sev.count / total) * 100}%`, backgroundColor: sev.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="px-4 pb-3 mt-2">
            <div className="px-4 py-2.5 border border-border rounded bg-muted/50">
              <div className="text-slate-400 text-[11px] font-medium">Resolution Rate</div>
              <div className="flex items-end gap-2 mt-1">
                <span className="text-green-400 text-[22px] font-mono font-bold">{Math.round((RESPONSE_STATS.resolvedToday / RESPONSE_STATS.totalToday) * 100)}%</span>
                <span className="text-slate-500 text-[11px] pb-0.5">{RESPONSE_STATS.resolvedToday} / {RESPONSE_STATS.totalToday} resolved today</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Busiest zones */}
      <div className="bg-card border border-border rounded">
        <div className="px-4 py-2.5 border-b border-border">
          <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Busiest Zones by Incident Count</span>
        </div>
        <div className="p-4 space-y-2">
          {BUSIEST_ZONES.map((zone, i) => (
            <div key={zone.name} className="flex items-center gap-3">
              <span className="text-slate-500 text-[11px] font-mono w-4 text-right">{i + 1}</span>
              <span className="text-slate-300 text-[12px] w-32 flex-shrink-0">{zone.name}</span>
              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${(zone.incidents / maxBusy) * 100}%`,
                    backgroundColor: i === 0 ? '#ef4444' : i === 1 ? '#f97316' : i === 2 ? '#f59e0b' : '#3b82f6',
                  }}
                />
              </div>
              <span className="text-slate-400 text-[11px] font-mono w-8 text-right">{zone.incidents}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, mono, icon }: { label: string; value: string; mono?: boolean; icon: React.ReactNode }) {
  return (
    <div className="bg-card border border-border rounded p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-[12px] font-medium uppercase tracking-wider leading-tight">{label}</span>
        {icon}
      </div>
      <div className={`text-slate-100 ${mono ? 'font-mono text-2xl' : 'text-2xl'} font-bold`}>{value}</div>
    </div>
  );
}
