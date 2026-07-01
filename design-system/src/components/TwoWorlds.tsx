import type { ReactNode } from 'react';

export interface WorldSide {
  /** Side heading (e.g. 'EU World 🇪🇺') */
  title: string;
  /** Heading color (e.g. '#3182ce' for EU, '#ed8936' for Asia) */
  color?: string;
  /** Bullet items — each renders with a '▸' marker */
  items: ReactNode[];
}

export interface TwoWorldsProps {
  /** Centered heading above the two boxes */
  title?: string;
  /** Left box — styled with the blue 'EU world' tint */
  left: WorldSide;
  /** Right box — styled with the orange 'Asia world' tint */
  right: WorldSide;
  /** Symbol between the boxes (default '↔') */
  arrow?: string;
  /** Small centered footnote under the grid */
  note?: string;
}

/**
 * Side-by-side comparison panel ("two worlds"): a blue-tinted box and an
 * orange-tinted box of bullet points joined by a convergence arrow — used to
 * contrast regulatory regimes.
 */
export function TwoWorlds({ title, left, right, arrow = '↔', note }: TwoWorldsProps) {
  return (
    <div className="two-worlds">
      {title && <h3>{title}</h3>}
      <div className="worlds-grid">
        <div className="world-box world-eu">
          <h4 style={left.color ? { color: left.color } : undefined}>{left.title}</h4>
          <ul>
            {left.items.map((li, i) => (
              <li key={i}>{li}</li>
            ))}
          </ul>
        </div>
        <div className="convergence-arrow">{arrow}</div>
        <div className="world-box world-asia">
          <h4 style={right.color ? { color: right.color } : undefined}>{right.title}</h4>
          <ul>
            {right.items.map((li, i) => (
              <li key={i}>{li}</li>
            ))}
          </ul>
        </div>
      </div>
      {note && (
        <p style={{ textAlign: 'center', marginTop: 16, color: '#718096', fontSize: '0.82em' }}>{note}</p>
      )}
    </div>
  );
}
