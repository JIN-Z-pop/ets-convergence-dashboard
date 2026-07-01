/**
 * The dashboard's THEME palette (shared.js) for use with any charting
 * library — colors here mirror the CSS custom properties in styles.css.
 */
export const chartTheme = {
  bg: '#0c1117',
  card: '#151d28',
  border: '#232e3c',
  text: '#dce4ec',
  muted: '#8a9bb0',
  dimmed: '#5a6b7f',
  accent: '#5BA4D9',
  gold: '#E8C468',
  hover: '#1c2736',
  countries: { EU: '#4A90D9', Korea: '#56B870', China: '#E8943A', Japan: '#D64545' },
} as const;

/**
 * Verbatim port of the dashboard's darkLayout() — a Plotly layout preset
 * (dark card plot area, DM Sans body font, DM Serif Display title). Merge
 * `extra` over the defaults, exactly like the original.
 */
export function plotlyDarkLayout(title: string, extra?: Record<string, unknown>): Record<string, unknown> {
  return Object.assign(
    {
      height: 420,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: chartTheme.card,
      font: { color: chartTheme.text, family: "'DM Sans', system-ui, sans-serif", size: 12 },
      title: {
        text: title,
        font: { color: chartTheme.text, size: 15, family: "'DM Serif Display', Georgia, serif" },
        x: 0.02,
        xanchor: 'left',
        y: 1,
        yanchor: 'top',
        pad: { t: 4 },
      },
      xaxis: {
        gridcolor: chartTheme.border,
        zerolinecolor: chartTheme.border,
        tickfont: { color: chartTheme.muted, size: 11 },
        linecolor: chartTheme.border,
      },
      yaxis: {
        gridcolor: chartTheme.border,
        zerolinecolor: chartTheme.border,
        tickfont: { color: chartTheme.muted, size: 11 },
        linecolor: chartTheme.border,
      },
      margin: { l: 60, r: 30, t: 52, b: 50 },
      legend: { font: { color: chartTheme.muted, size: 11 }, bgcolor: 'rgba(0,0,0,0)' },
      hoverlabel: {
        bgcolor: chartTheme.card,
        bordercolor: chartTheme.border,
        font: { color: chartTheme.text, family: "'DM Sans', system-ui, sans-serif", size: 12 },
      },
    },
    extra || {}
  );
}
