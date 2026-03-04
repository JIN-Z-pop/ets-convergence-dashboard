# ETS Convergence Dashboard - Design Document

**Date**: 2026-03-04
**Author**: JIN-Z-pop and his merry AI brothers
**Status**: Approved

## Overview

Interactive web dashboard visualizing the convergence and divergence of Emission Trading Systems (ETS) across 4 countries: EU, Korea, China, and Japan toward 2030.

Data source: gods-eye-db (48 tables, ~26,300 rows) + Knowledge Brain RAG (1600+ items).

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repository | New standalone repo | 4-country scope exceeds korea/china-ets-mcp |
| Tech stack | Single HTML per page + Plotly.js CDN | Consistent with existing korea-ets-mcp, china-ets-mcp |
| Page structure | Multi-page + shared.js nav | 6 sections too heavy for single page; enables per-section URL sharing |
| Language | English default + 4-lang switcher (EN/JA/KO/ZH) | Matches 4-country scope; leverages ets_terminology table |
| Data embedding | JSON in `<script>` tags per page | No server needed; works on GitHub Pages and locally |
| Deployment | GitHub Pages | Free, instant, URL shareable |

## File Structure

```
ets-convergence-dashboard/
├── index.html            # Overview (KPI cards + price chart)
├── compare.html          # System Comparison (radar + table)
├── allocation.html       # Allocation Evolution (Gantt chart)
├── cbam.html             # CBAM Impact (timeline)
├── convergence.html      # Convergence Map (scatter + analysis)
├── rosetta.html          # Rosetta Stone (4-lang terminology)
├── shared.js             # Common: theme/nav/i18n/utilities
├── scripts/
│   └── export_data.py    # gods-eye-db → JSON data update
├── docs/
│   ├── plans/            # This design doc
│   └── analysis.md       # Convergence/divergence analysis text
├── README.md
└── LICENSE (MIT)
```

## Page Designs

### Page 1: Overview (index.html)
- **Header**: Dashboard title + language switcher + nav bar
- **KPI Cards**: 4 country cards showing current price, coverage %, entity count, start year
- **Main Chart**: 4-country price trend line chart (USD-converted, 2015-2026)
  - Data: raw_cea_daily (China), raw_kets_daily_price (Korea), EU reference values
  - USD conversion: KRW/1400, CNY/7.2, EUR*1.1
- **Footer**: Project description, data sources, GitHub link

### Page 2: System Comparison (compare.html)
- **Radar Chart**: 5 axes (Price level / Coverage % / Auction % / Penalty severity / System age) x 4 countries overlaid
- **Comparison Table**: Detailed metrics from ets_system_comparison (sortable)
- Data: ets_system_comparison table

### Page 3: Allocation Evolution (allocation.html)
- **Horizontal Gantt Chart**: X-axis 2005→2050, Y-axis 4 countries
- Color coding: GF(blue) → BM(green) → Auction(red)
- Phase details on hover
- Data: ets_allocation_typology + eu_ets_phases + japan_gx_ets_timeline

### Page 4: CBAM Impact (cbam.html)
- **Vertical Timeline**: 11 events (2005→2050)
- Impact cards showing Korea/China effects per event
- "Two Worlds" diagram section
- Data: eu_ets_cbam_timeline

### Page 5: Convergence Map (convergence.html)
- **Scatter Plot**: X=system age, Y=carbon price (USD/t), bubble=covered emissions
- Annotation arrows for 5 convergence + 5 divergence axes
- Ghost points for 2030 predictions
- Analysis text sections (5A-5D insights)
- Data: ets_system_comparison + analysis text

### Page 6: Rosetta Stone (rosetta.html)
- **Interactive Table**: 47 terms x 4 languages
- Category filter (7 categories)
- Cross-language search box
- Data: ets_terminology

## Shared Components (shared.js)

### Navigation Bar
- 6 page links with current-page highlight
- Responsive (hamburger on mobile)

### Language Switcher
- EN/JA/KO/ZH selector (top-right)
- All text stored in `LANG` object
- Chart labels, card text, tab names all switch

### Theme Constants
```javascript
const THEME = {
  bg: '#0f1923',
  card: '#1a2332',
  border: '#2d3748',
  text: '#e0e0e0',
  textMuted: '#a0aec0',
  accent: '#63b3ed',
  countries: {
    EU: '#3182ce',
    Korea: '#48bb78',
    China: '#ed8936',
    Japan: '#e53e3e'
  }
};
```

### Plotly Dark Layout
Common Plotly layout config for all charts (dark background, grid style, font).

## Data Strategy

Each HTML page contains its own JSON data in a `<script type="application/json" id="page-data">` tag.

`scripts/export_data.py`:
1. Connect to gods-eye-db via sqlite3
2. Execute page-specific SQL queries
3. Generate JSON
4. Replace data sections in each HTML file

## DB Tables Used

| Table | Page | Query |
|-------|------|-------|
| raw_cea_daily | Overview | Yearly avg/max/min price |
| raw_kets_daily_price | Overview | Yearly avg/max/min price |
| ets_system_comparison | Overview, Compare | 139 rows of metrics |
| ets_allocation_typology | Allocation | 8 rows, 4 countries |
| eu_ets_phases | Allocation | 5 phases |
| japan_gx_ets_timeline | Allocation | 5 events |
| eu_ets_cbam_timeline | CBAM | 11 events |
| ets_terminology | Rosetta | 47 terms x 4 langs |

## Non-Goals
- Real-time data updates (manual export_data.py)
- User authentication
- Server-side rendering
- Database direct connection from browser
