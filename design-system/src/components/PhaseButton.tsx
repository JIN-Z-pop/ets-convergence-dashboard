import type { CSSProperties } from 'react';

export interface PhaseButtonProps {
  label: string;
  /** Per-button accent color (sets --btn-c; defaults to the muted/accent scheme) */
  color?: string;
  active?: boolean;
  onClick?: () => void;
}

/**
 * Rectangular filter chip used for the per-country phase selector above
 * charts. The active state fills with a translucent tint of its color.
 */
export function PhaseButton({ label, color, active, onClick }: PhaseButtonProps) {
  return (
    <button
      className={`phase-btn${active ? ' phase-btn-active' : ''}`}
      style={color ? ({ '--btn-c': color } as CSSProperties) : undefined}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
