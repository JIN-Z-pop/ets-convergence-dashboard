export interface TopNavLink {
  label: string;
  href?: string;
  /** Marks the current page — renders with the accent underline */
  active?: boolean;
}

export interface TopNavProps {
  /** Brand text shown next to the gradient brand mark */
  brand: string;
  /** Optional brand link target */
  brandHref?: string;
  links?: TopNavLink[];
  /** Language switcher labels, e.g. ['EN', 'JA', 'KO', 'ZH'] */
  langs?: string[];
  /** Currently active language label (gold highlight) */
  activeLang?: string;
  onLangChange?: (lang: string) => void;
}

/**
 * Sticky editorial top navigation with a gradient brand mark, centered page
 * links (accent underline on the active page) and an optional language
 * switcher. Mirrors the dashboard's createNavHTML() chrome.
 */
export function TopNav({ brand, brandHref = '#', links = [], langs, activeLang, onLangChange }: TopNavProps) {
  return (
    <nav className="top-nav">
      <a href={brandHref} className="nav-brand">
        <span className="brand-mark"></span>
        <span className="brand-text">{brand}</span>
      </a>
      <div className="nav-links">
        {links.map((l) => (
          <a key={l.label} href={l.href ?? '#'} className={`nav-link${l.active ? ' nav-active' : ''}`}>
            {l.label}
          </a>
        ))}
      </div>
      {langs && langs.length > 0 && (
        <div className="lang-switcher">
          {langs.map((code) => (
            <button
              key={code}
              className={`lang-btn${code === activeLang ? ' lang-active' : ''}`}
              onClick={onLangChange ? () => onLangChange(code) : undefined}
            >
              {code}
            </button>
          ))}
        </div>
      )}
      <button className="nav-hamburger" aria-label="Menu">
        {'≡'}
      </button>
    </nav>
  );
}
