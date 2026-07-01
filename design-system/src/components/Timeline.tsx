import type { ReactNode } from 'react';

export interface TimelineProps {
  /** TimelineItem elements */
  children: ReactNode;
}

/**
 * Vertical event timeline with a blue-to-red gradient spine; items alternate
 * left/right on wide screens and stack on mobile. Compose with TimelineItem.
 */
export function Timeline({ children }: TimelineProps) {
  return <div className="timeline">{children}</div>;
}

export interface TimelineItemProps {
  /** Event date label (e.g. '2026-01') */
  date: string;
  /** Bold event title */
  title: string;
  /** Muted description paragraph */
  description?: ReactNode;
  /** Dot severity: 'high' = orange ring, 'critical' = filled red */
  severity?: 'default' | 'high' | 'critical';
  /** ImpactBadge elements shown under the description */
  impacts?: ReactNode;
}

/**
 * One event on the Timeline: severity dot on the spine, date, title,
 * description and optional country-impact badges.
 */
export function TimelineItem({ date, title, description, severity = 'default', impacts }: TimelineItemProps) {
  const dotClass = severity === 'default' ? '' : ` ${severity}`;
  return (
    <div className="tl-item">
      <div className={`tl-dot${dotClass}`}></div>
      <div className="tl-content">
        <div className="tl-date">{date}</div>
        <div className="tl-type">{title}</div>
        {description && <div className="tl-desc">{description}</div>}
        {impacts && <div className="tl-impact">{impacts}</div>}
      </div>
    </div>
  );
}
