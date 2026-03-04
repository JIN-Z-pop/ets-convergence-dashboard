// === ETS Convergence Dashboard — shared.js ===
// Common theme, navigation, i18n, and Plotly utilities

const THEME = {
  bg: '#0f1923', card: '#1a2332', border: '#2d3748',
  text: '#e0e0e0', muted: '#a0aec0', dimmed: '#718096',
  accent: '#63b3ed', hover: '#4a5568',
  countries: { EU: '#3182ce', Korea: '#48bb78', China: '#ed8936', Japan: '#e53e3e' }
};

const COUNTRY_FLAGS = { EU: '\u{1F1EA}\u{1F1FA}', Korea: '\u{1F1F0}\u{1F1F7}', China: '\u{1F1E8}\u{1F1F3}', Japan: '\u{1F1EF}\u{1F1F5}' };

const NAV_PAGES = [
  { id: 'index', href: 'index.html', en: 'Overview', ja: '概要', ko: '개요', zh: '概览' },
  { id: 'compare', href: 'compare.html', en: 'Compare', ja: '比較', ko: '비교', zh: '比较' },
  { id: 'allocation', href: 'allocation.html', en: 'Allocation', ja: '割当', ko: '할당', zh: '分配' },
  { id: 'cbam', href: 'cbam.html', en: 'CBAM', ja: 'CBAM', ko: 'CBAM', zh: 'CBAM' },
  { id: 'convergence', href: 'convergence.html', en: 'Convergence', ja: '収斂・分岐', ko: '수렴·분기', zh: '趋同·分歧' },
  { id: 'rosetta', href: 'rosetta.html', en: 'Rosetta', ja: 'ロゼッタ', ko: '로제타', zh: '罗塞塔' }
];

const LANG = {
  en: {
    dashTitle: 'ETS Convergence Dashboard',
    dashSub: '4-Country ETS Convergence & Divergence toward 2030',
    footer: 'Data: gods-eye-db | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: 'Price', coverage: 'Coverage', entities: 'Entities', since: 'Since',
    eu: 'EU', korea: 'Korea', china: 'China', japan: 'Japan',
    usdPerTon: 'USD/t', approx: 'approx.',
    convergence: 'Convergence', divergence: 'Divergence',
    source: 'Source', noData: 'No market data yet'
  },
  ja: {
    dashTitle: 'ETS収斂ダッシュボード',
    dashSub: '4カ国ETS制度の2030年に向けた収斂と分岐',
    footer: 'データ: gods-eye-db | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '価格', coverage: 'カバー率', entities: '対象企業', since: '開始',
    eu: 'EU', korea: '韓国', china: '中国', japan: '日本',
    usdPerTon: 'USD/t', approx: '約',
    convergence: '収斂', divergence: '分岐',
    source: '出典', noData: '市場データ未形成'
  },
  ko: {
    dashTitle: 'ETS 수렴 대시보드',
    dashSub: '4개국 ETS 제도의 2030년 수렴과 분기',
    footer: '데이터: gods-eye-db | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '가격', coverage: '커버율', entities: '대상기업', since: '시작',
    eu: 'EU', korea: '한국', china: '중국', japan: '일본',
    usdPerTon: 'USD/t', approx: '약',
    convergence: '수렴', divergence: '분기',
    source: '출처', noData: '시장 데이터 미형성'
  },
  zh: {
    dashTitle: 'ETS趋同仪表板',
    dashSub: '四国ETS制度2030年趋同与分歧',
    footer: '数据: gods-eye-db | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '价格', coverage: '覆盖率', entities: '纳入企业', since: '启动',
    eu: 'EU', korea: '韩国', china: '中国', japan: '日本',
    usdPerTon: 'USD/t', approx: '约',
    convergence: '趋同', divergence: '分歧',
    source: '来源', noData: '尚无市场数据'
  }
};

// --- Language ---
function getLang() { return localStorage.getItem('ets-dash-lang') || 'en'; }
function setLang(lang) { localStorage.setItem('ets-dash-lang', lang); }
function t(key) { return (LANG[getLang()] || LANG.en)[key] || (LANG.en[key] || key); }

function switchLang(lang) {
  setLang(lang);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    el.innerHTML = t(el.dataset.i18nHtml);
  });
  // Update nav labels
  document.querySelectorAll('.nav-link').forEach(a => {
    const page = NAV_PAGES.find(p => p.id === a.dataset.pageId);
    if (page) a.textContent = page[lang] || page.en;
  });
  // Dispatch event for page-specific updates
  window.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
}

// --- Navigation ---
function createNavHTML(currentPageId) {
  const lang = getLang();
  const links = NAV_PAGES.map(p => {
    const active = p.id === currentPageId ? ' nav-active' : '';
    return `<a href="${p.href}" class="nav-link${active}" data-page-id="${p.id}">${p[lang] || p.en}</a>`;
  }).join('');

  return `<nav class="top-nav">
    <div class="nav-brand" data-i18n="dashTitle">${t('dashTitle')}</div>
    <div class="nav-links">${links}</div>
    <div class="lang-switcher">
      <select id="lang-select" onchange="switchLang(this.value)">
        <option value="en"${lang==='en'?' selected':''}>English</option>
        <option value="ja"${lang==='ja'?' selected':''}>日本語</option>
        <option value="ko"${lang==='ko'?' selected':''}>한국어</option>
        <option value="zh"${lang==='zh'?' selected':''}>中文</option>
      </select>
    </div>
    <button class="nav-hamburger" onclick="this.parentElement.classList.toggle('open')">&#9776;</button>
  </nav>`;
}

function createFooterHTML() {
  return `<footer class="dash-footer">
    <span data-i18n="footer">${t('footer')}</span>
  </footer>`;
}

// --- Common CSS ---
function getCommonCSS() {
  return `
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: ${THEME.bg}; color: ${THEME.text}; }

.top-nav {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 24px; background: linear-gradient(135deg, ${THEME.card}, ${THEME.border});
  border-bottom: 1px solid ${THEME.border}; flex-wrap: wrap; position: relative;
}
.nav-brand { font-size: 1.1em; font-weight: 700; color: ${THEME.accent}; white-space: nowrap; }
.nav-links { display: flex; gap: 4px; flex: 1; justify-content: center; flex-wrap: wrap; }
.nav-link {
  padding: 6px 14px; border-radius: 6px; text-decoration: none;
  color: ${THEME.muted}; font-size: 0.85em; transition: all 0.15s;
}
.nav-link:hover { background: ${THEME.hover}; color: ${THEME.text}; }
.nav-link.nav-active { background: ${THEME.accent}22; color: ${THEME.accent}; font-weight: 600; }
.lang-switcher select {
  background: ${THEME.border}; color: ${THEME.text}; border: 1px solid ${THEME.hover};
  border-radius: 6px; padding: 5px 10px; font-size: 0.82em; cursor: pointer; outline: none;
}
.lang-switcher select:hover { border-color: ${THEME.accent}; }
.nav-hamburger {
  display: none; background: none; border: 1px solid ${THEME.hover};
  color: ${THEME.text}; font-size: 1.2em; padding: 4px 10px; border-radius: 6px; cursor: pointer;
}
@media (max-width: 768px) {
  .nav-links { display: none; order: 3; width: 100%; justify-content: flex-start; }
  .top-nav.open .nav-links { display: flex; }
  .nav-hamburger { display: block; }
  .nav-brand { flex: 1; }
}

.page-header {
  text-align: center; padding: 28px 20px 16px;
}
.page-header h1 { font-size: 1.6em; color: ${THEME.accent}; margin-bottom: 6px; }
.page-header p { color: ${THEME.muted}; font-size: 0.9em; }

.cards { display: flex; gap: 15px; padding: 0 20px 20px; flex-wrap: wrap; justify-content: center; max-width: 1400px; margin: 0 auto; }
.card {
  background: ${THEME.card}; border-radius: 10px; padding: 18px 22px; min-width: 200px;
  text-align: center; border: 1px solid ${THEME.border}; flex: 1; max-width: 300px;
}
.card .country-flag { font-size: 1.6em; }
.card .country-name { font-size: 0.82em; color: ${THEME.muted}; margin: 4px 0 8px; text-transform: uppercase; letter-spacing: 1px; }
.card .value { font-size: 1.7em; font-weight: bold; line-height: 1.3; }
.card .label { color: ${THEME.muted}; font-size: 0.82em; margin-top: 4px; }
.card .sub { color: ${THEME.dimmed}; font-size: 0.72em; margin-top: 2px; }

.chart-wrap {
  padding: 10px 20px; max-width: 1400px; margin: 0 auto;
}
.chart-box {
  background: ${THEME.card}; border-radius: 10px; margin-bottom: 20px;
  padding: 15px; border: 1px solid ${THEME.border}; min-height: 400px;
}

.section-title {
  color: ${THEME.accent}; font-size: 1.15em; font-weight: 600;
  margin: 24px 0 12px; padding-left: 20px;
}

.dash-footer {
  text-align: center; padding: 20px; color: ${THEME.dimmed};
  font-size: 0.82em; border-top: 1px solid ${THEME.border}; margin-top: 20px;
}

.analysis-box {
  background: ${THEME.card}; border-radius: 10px; padding: 20px 24px;
  border: 1px solid ${THEME.border}; margin: 12px 20px; max-width: 1400px;
  margin-left: auto; margin-right: auto; color: ${THEME.text}; line-height: 1.65;
}
.analysis-box h3 { color: ${THEME.accent}; margin-bottom: 10px; font-size: 1.05em; }
.analysis-box p { margin-bottom: 10px; font-size: 0.9em; }
.analysis-box code { background: ${THEME.border}; padding: 1px 6px; border-radius: 3px; font-size: 0.88em; }
`;
}

// --- Plotly ---
function darkLayout(title, extra) {
  return Object.assign({
    paper_bgcolor: THEME.bg, plot_bgcolor: THEME.card,
    font: { color: THEME.text, family: 'Segoe UI, system-ui, sans-serif', size: 12 },
    title: { text: title, font: { color: THEME.accent, size: 15 }, x: 0.02, xanchor: 'left' },
    xaxis: { gridcolor: THEME.border, zerolinecolor: THEME.border, tickfont: { color: THEME.muted } },
    yaxis: { gridcolor: THEME.border, zerolinecolor: THEME.border, tickfont: { color: THEME.muted } },
    margin: { l: 60, r: 30, t: 50, b: 50 },
    legend: { font: { color: THEME.muted }, bgcolor: 'rgba(0,0,0,0)' },
    hoverlabel: { bgcolor: THEME.card, bordercolor: THEME.border, font: { color: THEME.text } }
  }, extra || {});
}

var plotlyConfig = { responsive: true, displayModeBar: false };

// --- Page init ---
function initPage(pageId) {
  // Inject CSS
  const style = document.createElement('style');
  style.textContent = getCommonCSS();
  document.head.appendChild(style);
  // Inject nav
  document.body.insertAdjacentHTML('afterbegin', createNavHTML(pageId));
  // Inject footer
  document.body.insertAdjacentHTML('beforeend', createFooterHTML());
}
