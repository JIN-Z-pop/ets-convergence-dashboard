import type { ReactNode } from 'react';

export interface SectionTitleProps {
  children: ReactNode;
}

/**
 * Serif section heading with a short gold bar on the left. Use to introduce
 * a new block of charts or analysis within a page.
 */
export function SectionTitle({ children }: SectionTitleProps) {
  return <h3 className="section-title">{children}</h3>;
}
