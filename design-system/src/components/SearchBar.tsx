import type { ReactNode } from 'react';

export interface SearchBarProps {
  placeholder?: string;
  /** Initial input value (uncontrolled) */
  defaultValue?: string;
  onChange?: (value: string) => void;
  /** Filter pills rendered to the right of the input (CatButton elements) */
  children?: ReactNode;
}

/**
 * Width-capped search row: dark rounded text input plus an optional row of
 * category filter pills — the terminology page's search chrome.
 */
export function SearchBar({ placeholder, defaultValue, onChange, children }: SearchBarProps) {
  return (
    <div className="search-bar">
      <input
        type="text"
        className="search-input"
        placeholder={placeholder}
        defaultValue={defaultValue}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
      />
      {children && <div className="cat-filters">{children}</div>}
    </div>
  );
}
