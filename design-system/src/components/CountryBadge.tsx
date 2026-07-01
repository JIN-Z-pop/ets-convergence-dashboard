export interface CountryBadgeProps {
  /** Text label (e.g. 'EU', 'Korea') */
  label: string;
  /** Solid background color — use the country tokens */
  color: string;
  /** Optional emoji flag prefix */
  flag?: string;
}

/**
 * Solid-color country chip with white text — used in table headers to label
 * per-country columns.
 */
export function CountryBadge({ label, color, flag }: CountryBadgeProps) {
  return (
    <span className="country-badge" style={{ background: color }}>
      {flag ? `${flag} ${label}` : label}
    </span>
  );
}
