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
    footer: 'Data: ETS database | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: 'Price', coverage: 'Coverage', entities: 'Entities', since: 'Since',
    eu: 'EU', korea: 'Korea', china: 'China', japan: 'Japan',
    usdPerTon: 'USD/t', approx: 'approx.',
    convergence: 'Convergence', divergence: 'Divergence',
    source: 'Source', noData: 'No market data yet',
    // Page headers
    pageCompareTitle: 'System Comparison',
    pageCompareSub: 'Radar chart \u2014 5 key dimensions across 4 ETS systems',
    pageAllocTitle: 'Allocation Evolution',
    pageAllocSub: 'From Grandfathering to Benchmark to Auctioning',
    pageCbamTitle: 'CBAM Impact Timeline',
    pageCbamSub: 'EU Carbon Border Adjustment Mechanism \u2014 Timeline & Asian ETS Impact',
    pageConvTitle: 'Convergence & Divergence Map',
    pageConvSub: 'Where 4 ETS systems stand today and where they\'re heading by 2030',
    pageRosettaTitle: 'Rosetta Stone',
    pageRosettaSub: '4-Language ETS Terminology \u2014 EN / JA / KO / ZH',
    // Chart titles
    chartPrice: 'Carbon Price Trends (USD/t)',
    chartRadar: '5-Dimension ETS Comparison',
    chartGantt: 'Allocation Phase Timeline (2005 \u2192 2040)',
    chartMethod: 'Allocation Method Mix (%)',
    chartScatter: 'ETS Position Map: System Age vs Carbon Price',
    // Section titles
    aboutTitle: 'About This Dashboard',
    detailCompare: 'Detailed Comparison',
    allocPath: 'Allocation Method Migration Path',
    twoWorlds: '"Two Worlds" \u2014 EU vs Asia ETS Paradigm',
    keyInsights: 'Key Insights',
    convAxes: '\u2192 5 Convergence Axes',
    divAxes: '\u2190 5 Divergence Axes',
    // Rosetta UI
    searchPlaceholder: 'Search across all 4 languages...',
    showingTerms: 'Showing',
    ofTerms: 'of',
    terms: 'terms',
    allCats: 'All',
    category: 'Category',
    // Labels
    metric: 'Metric',
    year: 'Year',
    bubbleNote: 'Bubble size = Covered emissions (relative)',
    solidFaded: 'Solid = Current (2026) | Faded = Predicted (2030)',
    jpNoPrice: 'Japan GX-ETS: no market price yet',
    cbamNote: 'CBAM is the bridge forcing convergence \u2014 Asia must either raise carbon prices or pay the EU difference',
    euWorld: 'EU World',
    asiaWorld: 'Asia World'
  },
  ja: {
    dashTitle: 'ETS\u53CE\u6582\u30C0\u30C3\u30B7\u30E5\u30DC\u30FC\u30C9',
    dashSub: '4\u30AB\u56FDETS\u5236\u5EA6\u306E2030\u5E74\u306B\u5411\u3051\u305F\u53CE\u6582\u3068\u5206\u5C90',
    footer: '\u30C7\u30FC\u30BF: ETS database | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '\u4FA1\u683C', coverage: '\u30AB\u30D0\u30FC\u7387', entities: '\u5BFE\u8C61\u4F01\u696D', since: '\u958B\u59CB',
    eu: 'EU', korea: '\u97D3\u56FD', china: '\u4E2D\u56FD', japan: '\u65E5\u672C',
    usdPerTon: 'USD/t', approx: '\u7D04',
    convergence: '\u53CE\u6582', divergence: '\u5206\u5C90',
    source: '\u51FA\u5178', noData: '\u5E02\u5834\u30C7\u30FC\u30BF\u672A\u5F62\u6210',
    pageCompareTitle: '\u5236\u5EA6\u6BD4\u8F03',
    pageCompareSub: '\u30EC\u30FC\u30C0\u30FC\u30C1\u30E3\u30FC\u30C8 \u2014 4\u30AB\u56FDETS\u306E5\u3064\u306E\u4E3B\u8981\u6B21\u5143\u3092\u6BD4\u8F03',
    pageAllocTitle: '\u5272\u5F53\u65B9\u5F0F\u306E\u9032\u5316',
    pageAllocSub: '\u904E\u53BB\u6392\u51FA\u91CF\u57FA\u6E96\u304B\u3089\u30D9\u30F3\u30C1\u30DE\u30FC\u30AF\u3001\u30AA\u30FC\u30AF\u30B7\u30E7\u30F3\u3078',
    pageCbamTitle: 'CBAM\u30A4\u30F3\u30D1\u30AF\u30C8\u5E74\u8868',
    pageCbamSub: 'EU\u70AD\u7D20\u56FD\u5883\u8ABF\u6574\u30E1\u30AB\u30CB\u30BA\u30E0 \u2014 \u5E74\u8868\u3068\u30A2\u30B8\u30A2ETS\u3078\u306E\u5F71\u97FF',
    pageConvTitle: '\u53CE\u6582\u30FB\u5206\u5C90\u30DE\u30C3\u30D7',
    pageConvSub: '4\u3064\u306EETS\u5236\u5EA6\u306E\u73FE\u5728\u5730\u3001\u305D\u3057\u30662030\u5E74\u306B\u5411\u304B\u3046\u5148',
    pageRosettaTitle: '\u30ED\u30BC\u30C3\u30BF\u30B9\u30C8\u30FC\u30F3',
    pageRosettaSub: '4\u8A00\u8A9EETS\u7528\u8A9E\u96C6 \u2014 \u82F1\u8A9E\u30FB\u65E5\u672C\u8A9E\u30FB\u97D3\u56FD\u8A9E\u30FB\u4E2D\u56FD\u8A9E',
    chartPrice: '\u70AD\u7D20\u4FA1\u683C\u63A8\u79FB (USD/t)',
    chartRadar: '5\u6B21\u5143ETS\u6BD4\u8F03',
    chartGantt: '\u5272\u5F53\u30D5\u30A7\u30FC\u30BA\u5E74\u8868 (2005 \u2192 2040)',
    chartMethod: '\u5272\u5F53\u65B9\u5F0F\u306E\u69CB\u6210 (%)',
    chartScatter: 'ETS\u30DD\u30B8\u30B7\u30E7\u30F3\u30DE\u30C3\u30D7\uFF1A\u5236\u5EA6\u5E74\u9F62 \u00D7 \u70AD\u7D20\u4FA1\u683C',
    aboutTitle: '\u30C0\u30C3\u30B7\u30E5\u30DC\u30FC\u30C9\u306B\u3064\u3044\u3066',
    detailCompare: '\u8A73\u7D30\u6BD4\u8F03',
    allocPath: '\u5272\u5F53\u65B9\u5F0F\u306E\u79FB\u884C\u30D1\u30B9',
    twoWorlds: '\u300C\u4E8C\u3064\u306E\u4E16\u754C\u300D\u2014 EU vs \u30A2\u30B8\u30A2ETS\u30D1\u30E9\u30C0\u30A4\u30E0',
    keyInsights: '\u4E3B\u8981\u306A\u77E5\u898B',
    convAxes: '\u2192 5\u3064\u306E\u53CE\u6582\u8EF8',
    divAxes: '\u2190 5\u3064\u306E\u5206\u5C90\u8EF8',
    searchPlaceholder: '4\u8A00\u8A9E\u3067\u691C\u7D22...',
    showingTerms: '\u8868\u793A\u4E2D',
    ofTerms: '/',
    terms: '\u4EF6',
    allCats: '\u5168\u3066',
    category: '\u30AB\u30C6\u30B4\u30EA',
    metric: '\u6307\u6A19',
    year: '\u5E74',
    bubbleNote: '\u30D0\u30D6\u30EB\u30B5\u30A4\u30BA = \u6392\u51FA\u30AB\u30D0\u30FC\u898F\u6A21\uFF08\u76F8\u5BFE\u5024\uFF09',
    solidFaded: '\u5B9F\u7DDA = \u73FE\u5728(2026) | \u8584\u8272 = \u4E88\u6E2C(2030)',
    jpNoPrice: '\u65E5\u672CGXETS\uFF1A\u5E02\u5834\u4FA1\u683C\u672A\u5F62\u6210',
    cbamNote: 'CBAM\u306F\u53CE\u6582\u3092\u5F37\u5236\u3059\u308B\u67B6\u3051\u6A4B \u2014 \u30A2\u30B8\u30A2\u306F\u70AD\u7D20\u4FA1\u683C\u3092\u5F15\u304D\u4E0A\u3052\u308B\u304B\u3001EU\u5DEE\u984D\u3092\u652F\u6255\u3046',
    euWorld: 'EU\u306E\u4E16\u754C',
    asiaWorld: '\u30A2\u30B8\u30A2\u306E\u4E16\u754C'
  },
  ko: {
    dashTitle: 'ETS \uC218\uB834 \uB300\uC2DC\uBCF4\uB4DC',
    dashSub: '4\uAC1C\uAD6D ETS \uC81C\uB3C4\uC758 2030\uB144 \uC218\uB834\uACFC \uBD84\uAE30',
    footer: '\uB370\uC774\uD130: ETS database | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '\uAC00\uACA9', coverage: '\uCEE4\uBC84\uC728', entities: '\uB300\uC0C1\uAE30\uC5C5', since: '\uC2DC\uC791',
    eu: 'EU', korea: '\uD55C\uAD6D', china: '\uC911\uAD6D', japan: '\uC77C\uBCF8',
    usdPerTon: 'USD/t', approx: '\uC57D',
    convergence: '\uC218\uB834', divergence: '\uBD84\uAE30',
    source: '\uCD9C\uCC98', noData: '\uC2DC\uC7A5 \uB370\uC774\uD130 \uBBF8\uD615\uC131',
    pageCompareTitle: '\uC81C\uB3C4 \uBE44\uAD50',
    pageCompareSub: '\uB808\uC774\uB354 \uCC28\uD2B8 \u2014 4\uAC1C\uAD6D ETS\uC758 5\uB300 \uD575\uC2EC \uCC28\uC6D0 \uBE44\uAD50',
    pageAllocTitle: '\uD560\uB2F9 \uBC29\uC2DD\uC758 \uC9C4\uD654',
    pageAllocSub: '\uACFC\uAC70\uBC30\uCD9C\uB7C9 \uAE30\uC900\uC5D0\uC11C \uBCA4\uCE58\uB9C8\uD06C, \uACBD\uB9E4\uAE4C\uC9C0',
    pageCbamTitle: 'CBAM \uC601\uD5A5 \uD0C0\uC784\uB77C\uC778',
    pageCbamSub: 'EU \uD0C4\uC18C\uAD6D\uACBD\uC870\uC815\uBA54\uCEE4\uB2C8\uC998 \u2014 \uD0C0\uC784\uB77C\uC778\uACFC \uC544\uC2DC\uC544 ETS \uC601\uD5A5',
    pageConvTitle: '\uC218\uB834\u00B7\uBD84\uAE30 \uB9F5',
    pageConvSub: '4\uAC1C ETS \uC81C\uB3C4\uC758 \uD604\uC7AC\uC640 2030\uB144\uC758 \uBC29\uD5A5',
    pageRosettaTitle: '\uB85C\uC81C\uD0C0 \uC2A4\uD1A4',
    pageRosettaSub: '4\uAC1C \uC5B8\uC5B4 ETS \uC6A9\uC5B4\uC9D1 \u2014 \uC601\uC5B4\u00B7\uC77C\uBCF8\uC5B4\u00B7\uD55C\uAD6D\uC5B4\u00B7\uC911\uAD6D\uC5B4',
    chartPrice: '\uD0C4\uC18C \uAC00\uACA9 \uCD94\uC774 (USD/t)',
    chartRadar: '5\uCC28\uC6D0 ETS \uBE44\uAD50',
    chartGantt: '\uD560\uB2F9 \uB2E8\uACC4 \uD0C0\uC784\uB77C\uC778 (2005 \u2192 2040)',
    chartMethod: '\uD560\uB2F9 \uBC29\uC2DD \uAD6C\uC131 (%)',
    chartScatter: 'ETS \uC704\uCE58 \uB9F5: \uC81C\uB3C4 \uC5F0\uB839 \u00D7 \uD0C4\uC18C \uAC00\uACA9',
    aboutTitle: '\uB300\uC2DC\uBCF4\uB4DC \uC18C\uAC1C',
    detailCompare: '\uC0C1\uC138 \uBE44\uAD50',
    allocPath: '\uD560\uB2F9 \uBC29\uC2DD \uC804\uD658 \uACBD\uB85C',
    twoWorlds: '"\uB450 \uAC1C\uC758 \uC138\uACC4" \u2014 EU vs \uC544\uC2DC\uC544 ETS \uD328\uB7EC\uB2E4\uC784',
    keyInsights: '\uD575\uC2EC \uC778\uC0AC\uC774\uD2B8',
    convAxes: '\u2192 5\uB300 \uC218\uB834 \uCD95',
    divAxes: '\u2190 5\uB300 \uBD84\uAE30 \uCD95',
    searchPlaceholder: '4\uAC1C \uC5B8\uC5B4\uB85C \uAC80\uC0C9...',
    showingTerms: '\uD45C\uC2DC',
    ofTerms: '/',
    terms: '\uAC74',
    allCats: '\uC804\uCCB4',
    category: '\uCE74\uD14C\uACE0\uB9AC',
    metric: '\uC9C0\uD45C',
    year: '\uC5F0\uB3C4',
    bubbleNote: '\uBC84\uBE14 \uD06C\uAE30 = \uBC30\uCD9C\uB7C9 \uCEE4\uBC84 \uADDC\uBAA8 (\uC0C1\uB300\uAC12)',
    solidFaded: '\uC2E4\uC120 = \uD604\uC7AC(2026) | \uD750\uB9BC = \uC608\uCE21(2030)',
    jpNoPrice: '\uC77C\uBCF8 GX-ETS: \uC2DC\uC7A5 \uAC00\uACA9 \uBBF8\uD615\uC131',
    cbamNote: 'CBAM\uC740 \uC218\uB834\uC744 \uAC15\uC81C\uD558\uB294 \uB2E4\uB9AC \u2014 \uC544\uC2DC\uC544\uB294 \uD0C4\uC18C \uAC00\uACA9\uC744 \uC62C\uB9AC\uAC70\uB098 EU \uCC28\uC561\uC744 \uC9C0\uBD88',
    euWorld: 'EU\uC758 \uC138\uACC4',
    asiaWorld: '\uC544\uC2DC\uC544\uC758 \uC138\uACC4'
  },
  zh: {
    dashTitle: 'ETS\u8D8B\u540C\u4EEA\u8868\u677F',
    dashSub: '\u56DB\u56FDETS\u5236\u5EA62030\u5E74\u8D8B\u540C\u4E0E\u5206\u6B67',
    footer: '\u6570\u636E: ETS database | JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '\u4EF7\u683C', coverage: '\u8986\u76D6\u7387', entities: '\u7EB3\u5165\u4F01\u4E1A', since: '\u542F\u52A8',
    eu: 'EU', korea: '\u97E9\u56FD', china: '\u4E2D\u56FD', japan: '\u65E5\u672C',
    usdPerTon: 'USD/t', approx: '\u7EA6',
    convergence: '\u8D8B\u540C', divergence: '\u5206\u6B67',
    source: '\u6765\u6E90', noData: '\u5C1A\u65E0\u5E02\u573A\u6570\u636E',
    pageCompareTitle: '\u5236\u5EA6\u6BD4\u8F83',
    pageCompareSub: '\u96F7\u8FBE\u56FE \u2014 \u56DB\u56FDETS\u4E94\u5927\u5173\u952E\u7EF4\u5EA6\u6BD4\u8F83',
    pageAllocTitle: '\u5206\u914D\u65B9\u5F0F\u6F14\u53D8',
    pageAllocSub: '\u4ECE\u5386\u53F2\u6392\u653E\u6CD5\u5230\u57FA\u51C6\u503C\u6CD5\u518D\u5230\u62CD\u5356',
    pageCbamTitle: 'CBAM\u5F71\u54CD\u65F6\u95F4\u7EBF',
    pageCbamSub: 'EU\u78B3\u8FB9\u5883\u8C03\u8282\u673A\u5236 \u2014 \u65F6\u95F4\u7EBF\u4E0E\u4E9A\u6D32ETS\u5F71\u54CD',
    pageConvTitle: '\u8D8B\u540C\u00B7\u5206\u6B67\u5730\u56FE',
    pageConvSub: '\u56DB\u56FDETS\u5236\u5EA6\u7684\u73B0\u72B6\u4E0E2030\u5E74\u8D70\u5411',
    pageRosettaTitle: '\u7F57\u585E\u5854\u77F3\u7891',
    pageRosettaSub: '\u56DB\u8BEDETS\u672F\u8BED\u53C2\u8003 \u2014 \u82F1\u8BED\u00B7\u65E5\u8BED\u00B7\u97E9\u8BED\u00B7\u4E2D\u6587',
    chartPrice: '\u78B3\u4EF7\u683C\u8D8B\u52BF (USD/t)',
    chartRadar: '\u4E94\u7EFEETS\u6BD4\u8F83',
    chartGantt: '\u5206\u914D\u9636\u6BB5\u65F6\u95F4\u7EBF (2005 \u2192 2040)',
    chartMethod: '\u5206\u914D\u65B9\u5F0F\u6784\u6210 (%)',
    chartScatter: 'ETS\u5B9A\u4F4D\u56FE\uFF1A\u5236\u5EA6\u5E74\u9F84 \u00D7 \u78B3\u4EF7\u683C',
    aboutTitle: '\u5173\u4E8E\u6B64\u4EEA\u8868\u677F',
    detailCompare: '\u8BE6\u7EC6\u6BD4\u8F83',
    allocPath: '\u5206\u914D\u65B9\u5F0F\u8FC1\u79FB\u8DEF\u5F84',
    twoWorlds: '"\u4E24\u4E2A\u4E16\u754C" \u2014 EU vs \u4E9A\u6D32ETS\u8303\u5F0F',
    keyInsights: '\u5173\u952E\u53D1\u73B0',
    convAxes: '\u2192 5\u5927\u8D8B\u540C\u8F74',
    divAxes: '\u2190 5\u5927\u5206\u6B67\u8F74',
    searchPlaceholder: '\u56DB\u8BED\u641C\u7D22...',
    showingTerms: '\u663E\u793A',
    ofTerms: '/',
    terms: '\u6761',
    allCats: '\u5168\u90E8',
    category: '\u7C7B\u522B',
    metric: '\u6307\u6807',
    year: '\u5E74\u4EFD',
    bubbleNote: '\u6C14\u6CE1\u5927\u5C0F = \u8986\u76D6\u6392\u653E\u91CF\u89C4\u6A21\uFF08\u76F8\u5BF9\u503C\uFF09',
    solidFaded: '\u5B9E\u7EBF = \u5F53\u524D(2026) | \u6DE1\u8272 = \u9884\u6D4B(2030)',
    jpNoPrice: '\u65E5\u672CGXETS\uFF1A\u5C1A\u65E0\u5E02\u573A\u4EF7\u683C',
    cbamNote: 'CBAM\u662F\u5F3A\u5236\u8D8B\u540C\u7684\u6865\u6881 \u2014 \u4E9A\u6D32\u987B\u63D0\u9AD8\u78B3\u4EF7\u6216\u652F\u4ED8EU\u5DEE\u989D',
    euWorld: 'EU\u4E16\u754C',
    asiaWorld: '\u4E9A\u6D32\u4E16\u754C'
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
