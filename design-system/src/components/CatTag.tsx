export interface CatTagProps {
  /** Category text (e.g. 'MRV', '市場取引') */
  label: string;
  /** Category color — background at 13% alpha, border at 27% alpha, text solid */
  color: string;
}

/**
 * Tinted category pill (rounded, translucent background derived from its
 * color) — used to tag terminology rows by category.
 */
export function CatTag({ label, color }: CatTagProps) {
  return (
    <span
      className="cat-tag"
      style={{ background: `${color}22`, color, border: `1px solid ${color}44` }}
    >
      {label}
    </span>
  );
}
