export interface PageHeaderProps {
  /** Page title, set in the DM Serif Display editorial face */
  title: string;
  /** Muted one-line subtitle under the title */
  subtitle?: string;
}

/**
 * Centered editorial page header: serif display title, muted subtitle and a
 * short accent-to-gold gradient rule underneath.
 */
export function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div className="page-header">
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </div>
  );
}
