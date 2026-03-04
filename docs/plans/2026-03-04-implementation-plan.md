# ETS Convergence Dashboard — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 6-page interactive dashboard visualizing 4-country ETS convergence/divergence toward 2030, deployed on GitHub Pages.

**Architecture:** Multi-page static site. Each HTML page loads Plotly.js via CDN and shared.js for common theme/nav/i18n. Data is embedded as JSON within each page. A Python script exports data from gods-eye-db (SQLite) to update the embedded JSON.

**Tech Stack:** HTML5, Plotly.js 2.27.0 (CDN), vanilla JS, Python 3 (sqlite3), GitHub Pages.

**Project Root:** `C:\Users\jin_z\Desktop\ets-convergence-dashboard\`

**Style Reference:** `C:\Users\jin_z\Desktop\korea-ets-mcp\dashboard\template.html` — match dark theme, card layout, Plotly config.

**DB Path:** gods-eye-db is accessed via MCP `mcp__gods-eye-database-py__read_query`. For export_data.py, the SQLite file location needs to be discovered at runtime (check `C:\Users\jin_z\Desktop\gods-eye-database-py\` or MCP config).

---

## Task 1: Create shared.js — Theme, Navigation, i18n

**Files:**
- Create: `shared.js`

**Step 1: Write shared.js with all common functionality**

```javascript
// === THEME ===
const THEME = {
  bg: '#0f1923', card: '#1a2332', border: '#2d3748',
  text: '#e0e0e0', muted: '#a0aec0', dimmed: '#718096',
  accent: '#63b3ed', hover: '#4a5568',
  countries: { EU: '#3182ce', Korea: '#48bb78', China: '#ed8936', Japan: '#e53e3e' }
};

// === NAVIGATION ===
const NAV_PAGES = [
  { id: 'index', href: 'index.html', en: 'Overview', ja: '概要', ko: '개요', zh: '概览' },
  { id: 'compare', href: 'compare.html', en: 'Compare', ja: '比較', ko: '비교', zh: '比较' },
  { id: 'allocation', href: 'allocation.html', en: 'Allocation', ja: '割当', ko: '할당', zh: '分配' },
  { id: 'cbam', href: 'cbam.html', en: 'CBAM', ja: 'CBAM', ko: 'CBAM', zh: 'CBAM' },
  { id: 'convergence', href: 'convergence.html', en: 'Convergence', ja: '収斂', ko: '수렴', zh: '趋同' },
  { id: 'rosetta', href: 'rosetta.html', en: 'Rosetta', ja: 'ロゼッタ', ko: '로제타', zh: '罗塞塔' }
];

function createNav(currentPageId) { ... }  // Build nav bar, highlight current
function createLangSwitcher() { ... }       // EN/JA/KO/ZH select dropdown
function switchLang(lang) { ... }           // Update all [data-i18n] elements
function getLang() { ... }                  // Get from localStorage or default 'en'

// === i18n COMMON STRINGS ===
const LANG = {
  en: { dashTitle: 'ETS Convergence Dashboard', dashSub: '4-Country ETS Convergence & Divergence toward 2030', ... },
  ja: { dashTitle: 'ETS収斂ダッシュボード', dashSub: '4カ国ETS制度の2030年に向けた収斂と分岐', ... },
  ko: { dashTitle: 'ETS 수렴 대시보드', dashSub: '4개국 ETS 제도의 2030년 수렴과 분기', ... },
  zh: { dashTitle: 'ETS趋同仪表板', dashSub: '四国ETS制度2030年趋同与分歧', ... }
};

// === PLOTLY DARK LAYOUT ===
function darkLayout(title, extra) {
  return Object.assign({
    paper_bgcolor: THEME.bg, plot_bgcolor: THEME.card,
    font: { color: THEME.text, family: 'Segoe UI, sans-serif' },
    title: { text: title, font: { color: THEME.accent, size: 16 } },
    xaxis: { gridcolor: THEME.border, zerolinecolor: THEME.border },
    yaxis: { gridcolor: THEME.border, zerolinecolor: THEME.border },
    margin: { l: 60, r: 30, t: 50, b: 50 }, legend: { font: { color: THEME.muted } }
  }, extra || {});
}

// === COMMON CSS (injected) ===
function injectCommonCSS() { ... }  // Inject base styles matching korea-ets-mcp theme

// === PAGE INIT ===
function initPage(pageId) {
  injectCommonCSS();
  document.body.insertAdjacentHTML('afterbegin', createNav(pageId));
  // ... lang switcher, footer
}
```

**Step 2: Verify** — Will be verified when first HTML page is created.

**Step 3: Commit**
```bash
git add shared.js && git commit -m "feat: add shared.js with theme, nav, i18n, Plotly layout"
```

---

## Task 2: Create export_data.py — DB to JSON extraction

**Files:**
- Create: `scripts/export_data.py`

**Step 1: Write export script**

Connects to gods-eye-db SQLite, runs queries for each page, outputs JSON files to `data/`.

Key queries:
- **prices.json**: `SELECT strftime('%Y', date), AVG/MAX/MIN(closing_price) FROM raw_cea_daily GROUP BY year` + same for `raw_kets_daily_price`
- **systems.json**: `SELECT * FROM ets_system_comparison WHERE reference_year >= 2024`
- **allocation.json**: `SELECT * FROM ets_allocation_typology` + `eu_ets_phases` + `japan_gx_ets_timeline`
- **cbam.json**: `SELECT * FROM eu_ets_cbam_timeline`
- **terminology.json**: `SELECT * FROM ets_terminology`

Also embeds EU reference price data (no DB table — hardcoded from known values: ~€80/t in 2024).

**Step 2: Run and verify JSON output**
```bash
cd ~/Desktop/ets-convergence-dashboard
python scripts/export_data.py
# Verify: ls data/*.json
```

**Step 3: Commit**
```bash
git add scripts/export_data.py data/ && git commit -m "feat: add data export script and initial JSON data"
```

---

## Task 3: Create index.html — Overview Page

**Files:**
- Create: `index.html`

**Key elements:**
1. Header with nav (via `initPage('index')`)
2. 4 KPI cards: EU (€80, 40%, 11000, 2005) / Korea (₩11,823, 68%, 680, 2015) / China (¥79, 60%, 3500, 2021) / Japan (GX-ETS, 60%, 400, 2023)
3. 4-country price trend Plotly line chart (yearly averages, USD-converted)
   - Korea: raw_kets_daily_price yearly avg / 1400
   - China: raw_cea_daily yearly avg / 7.2
   - EU: reference line ~$88
   - Japan: no market price yet — omit or show as annotation
4. Country color-coded: EU blue, Korea green, China orange, Japan red
5. Footer with data sources

**Embedded data:** prices.json content in `<script id="page-data">`

**Step 1: Create full index.html** with embedded data, cards, chart.

**Step 2: Open in browser, verify visually**
```bash
start ~/Desktop/ets-convergence-dashboard/index.html
```

**Step 3: Commit**
```bash
git add index.html && git commit -m "feat: add Overview page with KPI cards and price chart"
```

---

## Task 4: Create compare.html — System Comparison

**Files:**
- Create: `compare.html`

**Key elements:**
1. Radar chart (Plotly scatterpolar): 5 axes normalized 0-100
   - Price level: EU=100, China=12.5, Korea=9, Japan=0
   - Coverage %: EU=40, Korea=68, China=60, Japan=60
   - Auction %: EU=43, Korea=10, China=0, Japan=0
   - Penalty severity: EU=90(€100/t), Korea=80(3x price), China=50(improving), Japan=20(TBD)
   - System age (years): EU=21, Korea=11, China=5, Japan=3 → normalized to 0-100
2. Comparison table below with sortable columns
3. Key metrics from ets_system_comparison

**Embedded data:** systems.json filtered for radar + table

**Step 1: Create compare.html** with radar chart and table.

**Step 2: Verify in browser.**

**Step 3: Commit**
```bash
git add compare.html && git commit -m "feat: add System Comparison page with radar chart"
```

---

## Task 5: Create allocation.html — Allocation Evolution

**Files:**
- Create: `allocation.html`

**Key elements:**
1. Horizontal Gantt-style chart using Plotly bar chart (horizontal)
   - Y-axis: EU, Korea, China, Japan
   - X-axis: 2005 → 2050 (years)
   - Stacked/segmented bars per phase
   - Colors: GF=#3182ce(blue), BM=#48bb78(green), Auction=#ed8936(orange)
2. Phase labels on hover (name, period, free/auction %)
3. Data from ets_allocation_typology + eu_ets_phases + japan_gx_ets_timeline

**Embedded data:** allocation.json

**Step 1: Create allocation.html** with Gantt chart.

**Step 2: Verify in browser.**

**Step 3: Commit**
```bash
git add allocation.html && git commit -m "feat: add Allocation Evolution page with Gantt chart"
```

---

## Task 6: Create cbam.html — CBAM Impact

**Files:**
- Create: `cbam.html`

**Key elements:**
1. Vertical timeline using CSS (not Plotly) — better for event display
   - 11 events from eu_ets_cbam_timeline
   - Left side: event date + type
   - Right side: description + impact cards
2. Korea/China impact badges (colored if data exists)
3. "Two Worlds" section at bottom — styled text/diagram showing EU vs Asia divide

**Embedded data:** cbam.json

**Step 1: Create cbam.html** with CSS timeline and impact cards.

**Step 2: Verify in browser.**

**Step 3: Commit**
```bash
git add cbam.html && git commit -m "feat: add CBAM Impact page with timeline"
```

---

## Task 7: Create convergence.html — Convergence Map

**Files:**
- Create: `convergence.html`

**Key elements:**
1. Scatter plot (Plotly):
   - X: system age (years since start)
   - Y: current carbon price (USD/t)
   - Bubble size: covered emissions (relative)
   - Color: country color
   - 4 current-state points + 4 ghost 2030-prediction points
2. Annotation arrows/text for convergence (5) and divergence (5) axes
3. Analysis text sections (5A–5D insights from the analysis)
4. "Two Worlds" diagram

**Embedded data:** Curated from ets_system_comparison + analysis text

**Step 1: Create convergence.html** with scatter chart and analysis sections.

**Step 2: Verify in browser.**

**Step 3: Commit**
```bash
git add convergence.html && git commit -m "feat: add Convergence Map page with scatter chart and analysis"
```

---

## Task 8: Create rosetta.html — Rosetta Stone

**Files:**
- Create: `rosetta.html`

**Key elements:**
1. Search box at top (searches all 4 language columns)
2. Category filter buttons (7 categories from ets_terminology)
3. Interactive table: columns = English, Japanese, Korean, Chinese, Category
4. 47 rows from ets_terminology
5. Highlight matching text on search

**Embedded data:** terminology.json (47 rows)

**Step 1: Create rosetta.html** with search, filter, and table.

**Step 2: Verify in browser.**

**Step 3: Commit**
```bash
git add rosetta.html && git commit -m "feat: add Rosetta Stone page with 4-language terminology"
```

---

## Task 9: Create README.md + LICENSE

**Files:**
- Create: `README.md`
- Create: `LICENSE`

**README structure:**
- Title + badge (GitHub Pages link)
- Screenshot/preview
- What is this? (1 paragraph)
- 6 pages overview
- Data sources (gods-eye-db tables listed)
- How to update data (export_data.py)
- Related projects (korea-ets-mcp, china-ets-mcp, estat-api-client)
- Author: JIN-Z-pop and his merry AI brothers

**LICENSE:** MIT

**Step 1: Write README.md and LICENSE**

**Step 2: Commit**
```bash
git add README.md LICENSE && git commit -m "docs: add README and MIT license"
```

---

## Task 10: GitHub Repository + Pages Deployment

**Step 1: Create GitHub repo**
```bash
cd ~/Desktop/ets-convergence-dashboard
gh repo create JIN-Z-pop/ets-convergence-dashboard --public --source=. --push --description "4-Country ETS Convergence & Divergence Dashboard — EU, Korea, China, Japan toward 2030"
```

**Step 2: Enable GitHub Pages**
```bash
gh api repos/JIN-Z-pop/ets-convergence-dashboard/pages -X POST -f source.branch=master -f source.path=/
```

**Step 3: Verify deployment**
```bash
gh api repos/JIN-Z-pop/ets-convergence-dashboard/pages --jq '.html_url'
# Expected: https://jin-z-pop.github.io/ets-convergence-dashboard/
```

**Step 4: Update README with live URL, commit and push**

---

## Execution Dependencies

```
Task 1 (shared.js) ──┐
Task 2 (export_data) ─┤
                      ├→ Task 3 (index.html)
                      ├→ Task 4 (compare.html)    ← can run in parallel
                      ├→ Task 5 (allocation.html)  ← can run in parallel
                      ├→ Task 6 (cbam.html)        ← can run in parallel
                      ├→ Task 7 (convergence.html)  ← can run in parallel
                      ├→ Task 8 (rosetta.html)      ← can run in parallel
                      └→ Task 9 (README + LICENSE)
                              │
                              └→ Task 10 (GitHub + Pages)
```

**Parallelizable:** Tasks 3-8 are independent once Tasks 1-2 are complete. Can dispatch up to 3 subagents simultaneously (per reflexes.md limit).

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `~/Desktop/korea-ets-mcp/dashboard/template.html` | Style reference (CSS, card layout, Plotly config) |
| `~/Desktop/china-ets-mcp/dashboard/template.html` | Style reference (same pattern) |
| Design doc: `docs/plans/2026-03-04-ets-convergence-dashboard-design.md` | Approved design |
| gods-eye-db tables | See design doc "DB Tables Used" section |
