import type { ReactNode } from 'react';

export interface ImpactBadgeProps {
  /** 'kr' = green (Korea), 'cn' = orange (China) */
  variant: 'kr' | 'cn';
  children: ReactNode;
}

/**
 * Small tinted pill describing a country-specific impact on a timeline
 * event (e.g. '🇰🇷 K-CBAM legislation').
 */
export function ImpactBadge({ variant, children }: ImpactBadgeProps) {
  return <span className={`impact-badge impact-${variant}`}>{children}</span>;
}
