import type { CSSProperties, ReactNode } from 'react';

export interface ChartFrameProps {
  /** Chart or any content to frame (e.g. a Plotly/Recharts chart, a simulator form) */
  children: ReactNode;
  /** Extra style for the inner chart box (e.g. padding for form content, minHeight override) */
  boxStyle?: CSSProperties;
}

/**
 * Width-capped chart container: a dark card box (min-height 420px) inside the
 * page's content column. Every chart on the dashboard lives in one of these.
 */
export function ChartFrame({ children, boxStyle }: ChartFrameProps) {
  return (
    <div className="chart-wrap">
      <div className="chart-box" style={boxStyle}>
        {children}
      </div>
    </div>
  );
}
