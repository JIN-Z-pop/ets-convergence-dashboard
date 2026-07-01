import type { ReactNode } from 'react';

export interface AxisItemProps {
  /** 'convergence' = green left bar, 'divergence' = red left bar */
  variant: 'convergence' | 'divergence';
  /** Bold axis title (e.g. 'Carbon price levels') */
  title: string;
  /** Muted description text */
  children?: ReactNode;
}

/**
 * Tinted list row with a colored left bar marking a convergence (green) or
 * divergence (red) axis between ETS systems.
 */
export function AxisItem({ variant, title, children }: AxisItemProps) {
  return (
    <div className={`axis-item ${variant === 'convergence' ? 'axis-conv' : 'axis-div'}`}>
      <div className="axis-title">{title}</div>
      {children}
    </div>
  );
}
