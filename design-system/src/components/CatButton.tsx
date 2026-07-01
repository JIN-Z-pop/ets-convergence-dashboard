export interface CatButtonProps {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

/**
 * Rounded category filter pill (accent tint when active) — used alongside
 * SearchBar to filter the terminology table by category.
 */
export function CatButton({ label, active, onClick }: CatButtonProps) {
  return (
    <button className={`cat-btn${active ? ' active' : ''}`} onClick={onClick}>
      {label}
    </button>
  );
}
