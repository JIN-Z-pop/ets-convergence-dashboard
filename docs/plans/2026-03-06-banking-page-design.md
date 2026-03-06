# Banking Page Design — ETS Convergence Dashboard

**Date**: 2026-03-06
**Author**: ClaudeCode

## Overview

Add `banking.html` as the 7th page to the ETS Convergence Dashboard. Explains banking (carryover) rules across 4 ETS systems with interactive Plotly charts and 4-language i18n support.

## Architecture

Same pattern as existing pages:
- `initPage('banking')` via shared.js
- Data loaded from `data/banking.json` via fetch
- Charts via Plotly.js + `darkLayout()`
- 4-language i18n (EN/JA/KO/ZH)
- `langchange` event for dynamic switching

## Changes

### 1. shared.js
- Add `banking` to `NAV_PAGES` (between Allocation and CBAM)
- Add i18n keys to all 4 LANG objects

### 2. data/banking.json
Static data file with:
- `phases`: K-ETS phase evolution (restrictions, free allocation %, trading volume, price)
- `rules`: 4-country banking rule comparison (limit type, formula, borrowing, offset)
- `simulator`: parameters for interactive carryover calculator
- `trading`: K-ETS annual trading data (2015-2022)

### 3. banking.html
Four sections:

| Section | Chart Type | Description |
|---------|-----------|-------------|
| **Phase Evolution** | Grouped bar | Banking restriction + free allocation % + price across K-ETS phases |
| **Carryover Simulator** | Interactive (HTML slider + Plotly bar) | User adjusts net sales volume → see carryover limit per country |
| **4-Country Comparison** | Horizontal bar | Side-by-side banking/borrowing/offset rules |
| **K-ETS Market Impact** | Dual-axis line | Trading volume vs price (2015-2022), with Phase 2 restriction annotation |

Plus analysis-box with multilingual insights.

## Data Sources
- gods-eye-db: `ets_system_comparison`, `raw_kets_daily_price`
- Knowledge Brain RAG: #1623 (K-ETS Sub Map), #949 (ETS Master Index)

## Success Criteria
- Page renders with dark theme matching existing pages
- All 4 languages switch correctly
- Simulator responds to slider input in real-time
- Charts display correctly on mobile (responsive)
