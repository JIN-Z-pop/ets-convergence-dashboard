export interface StatCardProps {
  /** Small uppercase label above the value (e.g. '🇰🇷 Korea 2026') */
  label: string;
  /** Large serif value (e.g. '13,679' or '∞') */
  value: string;
  /** Tiny explanatory note under the value (e.g. 'NS × 5 = 13,679') */
  note?: string;
  /** Accent color: label text and border tint (use the country tokens) */
  color?: string;
}

/**
 * Compact simulator/result stat card on the page background — used by the
 * banking simulator for per-country computed results. Place in a CSS grid
 * (e.g. gridTemplateColumns: '1fr 1fr', gap 16).
 */
export function StatCard({ label, value, note, color }: StatCardProps) {
  return (
    <div className="sim-card" style={color ? { borderColor: `${color}33` } : undefined}>
      <div className="sim-label" style={color ? { color } : undefined}>
        {label}
      </div>
      <div className="sim-value">{value}</div>
      {note && <div className="sim-note">{note}</div>}
    </div>
  );
}
