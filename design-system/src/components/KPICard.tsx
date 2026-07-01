export interface KPIStat {
  value: string;
  label: string;
}

export interface KPICardProps {
  /** Emoji flag or symbol shown on top (e.g. '🇪🇺') */
  flag?: string;
  /** Uppercased entity name under the flag (e.g. 'EU', 'Korea') */
  name: string;
  /** Headline value in the serif display face (e.g. '€72/t') */
  value: string;
  /** Dimmed sub-line under the value (e.g. '~$79/t (2026 avg)') */
  sub?: string;
  /** Accent color: top border, name and value (use the country tokens) */
  color?: string;
  /** Small stats row at the bottom (e.g. coverage / entities / since) */
  stats?: KPIStat[];
}

/**
 * Country/entity KPI card: colored top border, flag, uppercase name, big
 * serif value, muted sub-line and an optional three-stat footer row.
 * Compose inside CardsGrid.
 */
export function KPICard({ flag, name, value, sub, color, stats }: KPICardProps) {
  return (
    <div className="card" style={color ? { borderTop: `3px solid ${color}` } : undefined}>
      {flag && <div className="country-flag">{flag}</div>}
      <div className="country-name" style={color ? { color } : undefined}>
        {name}
      </div>
      <div className="value" style={color ? { color } : undefined}>
        {value}
      </div>
      {sub && <div className="sub">{sub}</div>}
      {stats && stats.length > 0 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            marginTop: 14,
            fontSize: '0.82em',
            color: 'var(--muted)',
            gap: 8,
          }}
        >
          {stats.map((s) => (
            <div key={s.label}>
              <div style={{ fontWeight: 600, color: 'var(--text)', fontSize: '1.1em' }}>{s.value}</div>
              {s.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
