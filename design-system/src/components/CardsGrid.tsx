import type { ReactNode } from 'react';

export interface CardsGridProps {
  /** KPICard elements (or any .card content) */
  children: ReactNode;
}

/**
 * Centered, wrapping flex row for KPI cards — the dashboard's standard
 * card rack under the page header.
 */
export function CardsGrid({ children }: CardsGridProps) {
  return <div className="cards">{children}</div>;
}
