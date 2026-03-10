# ETS Convergence Dashboard

**4-Country ETS Convergence & Divergence toward 2030**

> Interactive dashboard visualizing how Emission Trading Systems in EU, Korea, China, and Japan are converging and diverging as they approach 2030.

**Live:** [https://jin-z-pop.github.io/ets-convergence-dashboard/](https://jin-z-pop.github.io/ets-convergence-dashboard/)

## Pages

| Page | Content |
|------|---------|
| **Overview** | KPI cards (price, coverage, entities) + carbon price trend chart (USD-converted) |
| **Compare** | 5-dimension radar chart + detailed comparison table (14 metrics) |
| **Allocation** | Phase timeline (Gantt) + allocation method evolution (GF → BM → Auction) |
| **CBAM** | EU CBAM timeline (11 events, 2005-2050) with Korea/China impact badges |
| **Convergence** | Scatter plot (system age vs price) with 2030 predictions + 5 convergence/divergence axes |
| **Rosetta** | 47-term ETS terminology in 4 languages (EN/JA/KO/ZH) with search & category filter |

## Data Sources

- SQLite database with ETS tables: `raw_cea_daily`, `raw_kets_daily_price`, `ets_system_comparison`, `ets_allocation_typology`, `eu_ets_phases`, `japan_gx_ets_timeline`, `eu_ets_cbam_timeline`, `ets_terminology`

## Tech Stack

- HTML5 + vanilla JS (no build step)
- [Plotly.js 2.27.0](https://plotly.com/javascript/) (CDN)
- Shared theme/nav/i18n via `shared.js`
- 4-language support: English, Japanese, Korean, Chinese

## Update Data

```bash
python scripts/export_data.py
# Exports JSON files to data/ from the ETS database
```

## Related Projects

- [korea-ets-mcp](https://github.com/JIN-Z-pop/korea-ets-mcp) — Korea ETS MCP server + dashboard
- [china-ets-mcp](https://github.com/JIN-Z-pop/china-ets-mcp) — China ETS MCP server + dashboard
- [estat-api-client](https://github.com/JIN-Z-pop/estat-api-client) — Japanese government statistics API client

## Author

**JIN-Z-pop and his merry AI brothers**

## License

MIT
