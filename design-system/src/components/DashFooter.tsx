export interface DashFooterProps {
  /** Credit line (e.g. 'JIN-Z-pop and his merry AI brothers | Plotly.js') */
  credit: string;
  /** Small faded disclaimer paragraph above the credit */
  disclaimer?: string;
  /** 'Data as of' label, rendered muted after the credit (e.g. 'Data as of: 2026-04-21') */
  lastUpdated?: string;
}

/**
 * Centered page footer: a hairline gradient rule, optional disclaimer, and
 * the credit line with an optional data-freshness note.
 */
export function DashFooter({ credit, disclaimer, lastUpdated }: DashFooterProps) {
  return (
    <footer className="dash-footer">
      <div className="footer-rule"></div>
      {disclaimer && <p className="footer-disclaimer">{disclaimer}</p>}
      <span>{credit}</span>
      {lastUpdated && (
        <span className="footer-updated" style={{ marginLeft: 12, color: 'var(--muted)', fontSize: '0.85em' }}>
          {lastUpdated}
        </span>
      )}
    </footer>
  );
}
