import type { ReactNode } from 'react';

export interface AnalysisBoxProps {
  /** Optional serif heading rendered above the body */
  title?: string;
  /** Body content — <p> paragraphs render muted; inline <code> gets the accent chip style */
  children: ReactNode;
}

/**
 * Editorial commentary card with a gold left border — the dashboard's
 * standard container for written analysis and methodology notes.
 */
export function AnalysisBox({ title, children }: AnalysisBoxProps) {
  return (
    <div className="analysis-box">
      {title && <h3>{title}</h3>}
      {children}
    </div>
  );
}
