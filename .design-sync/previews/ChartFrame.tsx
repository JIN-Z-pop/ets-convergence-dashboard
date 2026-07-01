import { ChartFrame, chartTheme } from 'ets-editorial';

const demoSeries = [
  { name: 'EU', color: chartTheme.countries.EU, points: '0,150 60,120 120,130 180,90 240,60 300,40' },
  { name: 'Korea', color: chartTheme.countries.Korea, points: '0,180 60,185 120,190 180,200 240,205 300,195' },
  { name: 'China', color: chartTheme.countries.China, points: '0,210 60,205 120,208 180,200 240,198 300,192' },
];

/** A ChartFrame holding a simple inline SVG price-trend sketch themed with chartTheme. */
export const PriceTrend = () => (
  <ChartFrame>
    <div style={{ padding: '12px 4px 4px' }}>
      <div style={{ fontFamily: "'DM Serif Display', Georgia, serif", color: chartTheme.text, fontSize: 15, marginBottom: 8 }}>
        Carbon Price Trends (USD/t)
      </div>
      <svg viewBox="0 0 320 240" style={{ width: '100%', height: 360, background: chartTheme.card }}>
        {[40, 90, 140, 190].map((y) => (
          <line key={y} x1="0" y1={y} x2="320" y2={y} stroke={chartTheme.border} strokeWidth="1" />
        ))}
        {demoSeries.map((s) => (
          <polyline key={s.name} points={s.points} fill="none" stroke={s.color} strokeWidth="2.5" />
        ))}
        <text x="8" y="30" fill={chartTheme.muted} fontSize="11" fontFamily="'DM Sans', sans-serif">
          EU · Korea · China (2021–2026)
        </text>
      </svg>
    </div>
  </ChartFrame>
);

export const AsFormContainer = () => (
  <ChartFrame boxStyle={{ padding: '24px 28px', minHeight: 0 }}>
    <p style={{ color: 'var(--muted)', fontSize: '0.88em', marginBottom: 12 }}>
      Enter net sales (NS) to simulate bankable allowances under each system's carryover rule.
    </p>
    <p style={{ color: 'var(--text)', fontSize: '0.95em' }}>
      NS = <span style={{ color: 'var(--accent)' }}>2,736 tCO₂</span>
    </p>
  </ChartFrame>
);
