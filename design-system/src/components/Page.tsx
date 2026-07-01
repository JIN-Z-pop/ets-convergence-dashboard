import type { CSSProperties, ReactNode } from 'react';

export interface PageProps {
  children: ReactNode;
  /** Extra style for the page canvas (e.g. minHeight, padding) */
  style?: CSSProperties;
}

/**
 * The dashboard's dark editorial canvas — deep navy background, DM Sans body
 * type, light text. Every component in this system is designed against this
 * surface: wrap your app (or any composition) in Page, or the components
 * render on white and the theme is lost.
 */
export function Page({ children, style }: PageProps) {
  return (
    <div className="dash-page" style={style}>
      {children}
    </div>
  );
}
