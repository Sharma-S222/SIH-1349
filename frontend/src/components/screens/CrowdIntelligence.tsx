import { useState } from 'react';
import { ArrowUp, ArrowDown, Minus, TrendingUp, Users } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { Zone } from '../../types/ui';
import { ZONES, CROWD_TREND_DATA } from '../../data/mockData';
import { SeverityBadge } from '../shared/SeverityBadge';

const TIME_RANGES = ['15 min', '1 hour', '6 hours', 'Today'] as const;
type TimeRange = typeof TIME_RANGES[number];

const riskBg: Record<string, string> = {
  CRITICAL: 'bg-red-900/30',
  HIGH: 'bg-orange-900/20',
  MEDIUM: 'bg-amber-900/15',
  LOW: 'bg-green-900/10',
};

function TrendIcon({ trend }: { trend: Zone['trend'] }) {
  if (trend === 'up') return <ArrowUp size={12} className="text-orange-400" />;
  if (trend === 'down') return <ArrowDown size={12} className="text-green-400" />;
  return <Minus size={12} className="text-slate-500" />;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#1a2236] border border-white/10 rounded p-2 text-[11px]">
      <div className="text-slate-400 font-mono mb-1">{label}</div>
      <div className="text-slate-200 font-mono">{payload[0]?.value} people</div>
    </div>
  );
};

export function CrowdIntelligence() {
  const [timeRange, setTimeRange] = useState<TimeRange>('1 hour');

  const totalCrowd = ZONES.reduce((s, z) => s + z.people_count, 0);
  const highestRisk = [...ZONES].sort((a, b) => {
    const o = { CRITICAL: 3, HIGH: 2, MEDIUM: 1, LOW: 0 };
    return o[b.risk] - o[a.risk];
  })[0];

  const rangePoints = {
    '15 min': 15,
    '1 hour': 60,
    '6 hours': Math.min(60, CROWD_TREND_DATA.length),
    'Today': CROWD_TREND_DATA.length,
  };
  const chartData = CROWD_TREND_DATA.slice(-rangePoints[timeRange]);

  const tickInterval = Math.floor(chartData.length / 6);

  return (
    <div className="p-4 space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard
          label="Current Station Crowd"
          value={String(totalCrowd)}
          sub="+8.4% over last 15 min"
          subColor="text-orange-400"
          icon={<Users size={14} className="text-slate-500" />}
        />
        <KPICard
          label="Highest-Risk Zone"
          value={highestRisk.name}
          sub={`${highestRisk.risk} risk · ${highestRisk.people_count} people`}
          subColor="text-red-400"
          valueClass="text-xl"
          icon={<TrendingUp size={14} className="text-slate-500" />}
        />
        <KPICard
          label="Peak Crowd Today"
          value="512"
          sub="18:47 — Peak hour"
          subColor="text-slate-500"
          icon={<TrendingUp size={14} className="text-slate-500" />}
        />
        <KPICard
          label="Crowd Trend"
          value="↑ Rising"
          valueClass="text-orange-400 text-xl"
          sub="Last 15 minutes"
          subColor="text-slate-500"
          icon={<ArrowUp size={14} className="text-orange-400" />}
        />
      </div>

      {/* Trend chart */}
      <div className="bg-card border border-border rounded">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
          <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Crowd Trend</span>
          <div className="flex items-center gap-1">
            {TIME_RANGES.map(r => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`text-[11px] px-2.5 py-1 rounded transition-colors font-mono ${
                  timeRange === r
                    ? 'bg-blue-600/20 text-blue-300 border border-blue-600/30'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <div className="p-3 h-52">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="crowdGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(148,163,184,0.07)" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
                tickLine={false}
                axisLine={false}
                interval={tickInterval}
              />
              <YAxis
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
                tickLine={false}
                axisLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={1.5}
                fill="url(#crowdGrad)"
                dot={false}
                activeDot={{ r: 3, fill: '#3b82f6', stroke: '#111827', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Zone table + Heat view */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Zone table */}
        <div className="bg-card border border-border rounded">
          <div className="px-4 py-2.5 border-b border-border">
            <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Crowd by Zone</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-2 text-left text-[10px] text-slate-500 uppercase tracking-wider">Zone</th>
                  <th className="px-4 py-2 text-right text-[10px] text-slate-500 uppercase tracking-wider">People</th>
                  <th className="px-4 py-2 text-right text-[10px] text-slate-500 uppercase tracking-wider">Capacity</th>
                  <th className="px-4 py-2 text-center text-[10px] text-slate-500 uppercase tracking-wider">Trend</th>
                  <th className="px-4 py-2 text-center text-[10px] text-slate-500 uppercase tracking-wider">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {ZONES.map(zone => (
                  <tr key={zone.zone_id} className="hover:bg-white/3 transition-colors">
                    <td className="px-4 py-2.5 text-slate-200 text-[12px] font-medium">{zone.name}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px] text-slate-300">{zone.people_count}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[12px] text-slate-500">{zone.capacity}</td>
                    <td className="px-4 py-2.5 text-center">
                      <div className="flex items-center justify-center">
                        <TrendIcon trend={zone.trend} />
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      <div className="flex justify-center">
                        <SeverityBadge severity={zone.risk} size="sm" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Station Heat View */}
        <div className="bg-card border border-border rounded">
          <div className="px-4 py-2.5 border-b border-border">
            <span className="text-slate-200 text-[13px] font-semibold tracking-wide">Station Heat View</span>
            <span className="ml-2 text-slate-600 text-[11px]">Schematic — Demo Junction</span>
          </div>
          <div className="p-3">
            <div className="border border-white/8 rounded overflow-hidden text-center text-[11px]">
              {/* Platform row */}
              <div className="grid grid-cols-3 border-b border-white/8">
                {(['Platform 1', 'Platform 2', 'Platform 3'] as const).map((name, i) => {
                  const z = ZONES.find(z => z.name === name);
                  return (
                    <div key={name} className={`py-3 px-2 ${i < 2 ? 'border-r border-white/8' : ''} ${z ? riskBg[z.risk] : ''}`}>
                      <div className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">{name}</div>
                      <div className="text-slate-300 text-[14px] font-mono font-semibold mt-1">{z?.people_count ?? '—'}</div>
                      {z && <SeverityBadge severity={z.risk} size="sm" showDot={false} />}
                    </div>
                  );
                })}
              </div>

              {/* Track row */}
              <div className={`py-2 border-b border-white/8 ${riskBg[ZONES.find(z => z.zone_id === 'TRKZ')?.risk ?? 'LOW']}`}>
                <div className="text-[9px] text-slate-600 font-mono tracking-widest">━━━━━━━━ TRACK ZONE ━━━━━━━━</div>
                <div className="text-slate-500 text-[10px] mt-0.5 font-mono">{ZONES.find(z => z.zone_id === 'TRKZ')?.people_count} people · <span className="text-red-400">HIGH RISK</span></div>
              </div>

              {/* Concourse */}
              <div className={`py-3 border-b border-white/8 ${riskBg[ZONES.find(z => z.zone_id === 'CONC')?.risk ?? 'LOW']}`}>
                <div className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">Main Concourse</div>
                <div className="text-slate-300 text-[14px] font-mono font-semibold mt-1">{ZONES.find(z => z.zone_id === 'CONC')?.people_count}</div>
                <div className="flex justify-center mt-1">
                  <SeverityBadge severity={ZONES.find(z => z.zone_id === 'CONC')?.risk ?? 'LOW'} size="sm" showDot={false} />
                </div>
              </div>

              {/* Entrance + Staircase */}
              <div className="grid grid-cols-2">
                <div className="py-3 px-2 border-r border-white/8">
                  <div className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">Main Entrance</div>
                  <div className="text-slate-500 text-[11px] font-mono mt-1">~97</div>
                  <div className="flex justify-center mt-1">
                    <SeverityBadge severity="LOW" size="sm" showDot={false} />
                  </div>
                </div>
                <div className={`py-3 px-2 ${riskBg[ZONES.find(z => z.zone_id === 'STCA')?.risk ?? 'LOW']}`}>
                  <div className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">Staircase A</div>
                  <div className="text-slate-300 text-[14px] font-mono font-semibold mt-1">{ZONES.find(z => z.zone_id === 'STCA')?.people_count}</div>
                  <div className="flex justify-center mt-1">
                    <SeverityBadge severity={ZONES.find(z => z.zone_id === 'STCA')?.risk ?? 'LOW'} size="sm" showDot={false} />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-3 flex-wrap">
              <span className="text-slate-600 text-[10px]">Risk legend:</span>
              {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(r => (
                <SeverityBadge key={r} severity={r} size="sm" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({ label, value, sub, subColor, icon, valueClass = 'text-3xl' }: {
  label: string; value: string; sub: string; subColor: string; icon: React.ReactNode; valueClass?: string;
}) {
  return (
    <div className="bg-card border border-border rounded p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-[12px] font-medium uppercase tracking-wider">{label}</span>
        {icon}
      </div>
      <div className={`font-bold text-slate-100 font-mono ${valueClass}`}>{value}</div>
      <div className={`text-[11px] mt-1 ${subColor}`}>{sub}</div>
    </div>
  );
}
