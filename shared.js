// === ETS Convergence Dashboard — shared.js ===
// Editorial/Magazine Design v2.0 — powered by frontend-design skill
// Common theme, navigation, i18n, and Plotly utilities

const THEME = {
  bg: '#0c1117', card: '#151d28', border: '#232e3c',
  text: '#dce4ec', muted: '#8a9bb0', dimmed: '#5a6b7f',
  accent: '#5BA4D9', gold: '#E8C468', hover: '#1c2736',
  countries: { EU: '#4A90D9', Korea: '#56B870', China: '#E8943A', Japan: '#D64545' }
};

const COUNTRY_FLAGS = { EU: '\u{1F1EA}\u{1F1FA}', Korea: '\u{1F1F0}\u{1F1F7}', China: '\u{1F1E8}\u{1F1F3}', Japan: '\u{1F1EF}\u{1F1F5}' };

const NAV_PAGES = [
  { id: 'index', href: 'index.html', en: 'Overview', ja: '\u6982\u8981', ko: '\uAC1C\uC694', zh: '\u6982\u89C8' },
  { id: 'compare', href: 'compare.html', en: 'Compare', ja: '\u6BD4\u8F03', ko: '\uBE44\uAD50', zh: '\u6BD4\u8F83' },
  { id: 'allocation', href: 'allocation.html', en: 'Allocation', ja: '\u5272\u5F53', ko: '\uD560\uB2F9', zh: '\u5206\u914D' },
  { id: 'banking', href: 'banking.html', en: 'Banking', ja: '\u7E70\u8D8A', ko: '\uC774\uC6D4', zh: '\u7ED3\u8F6C' },
  { id: 'cbam', href: 'cbam.html', en: 'CBAM', ja: 'CBAM', ko: 'CBAM', zh: 'CBAM' },
  { id: 'convergence', href: 'convergence.html', en: 'Convergence', ja: '\u7D71\u5408\u5206\u6790', ko: '\uC218\uB834\u00B7\uBD84\uAE30', zh: '\u8D8B\u540C\u00B7\u5206\u6B67' },
  { id: 'rosetta', href: 'rosetta.html', en: 'Rosetta', ja: '\u30ED\u30BC\u30C3\u30BF', ko: '\uB85C\uC81C\uD0C0', zh: '\u7F57\u585E\u5854' }
];

const LANG = {
  en: {
    dashTitle: 'ETS Convergence Dashboard',
    dashSub: '4-Country ETS Convergence & Divergence toward 2030',
    footer: 'JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: 'Price', coverage: 'Coverage', entities: 'Entities', since: 'Since',
    eu: 'EU', korea: 'Korea', china: 'China', japan: 'Japan',
    usdPerTon: 'USD/t', approx: 'approx.',
    convergence: 'Convergence', divergence: 'Divergence',
    source: 'Source', noData: 'No market data yet',
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
    chartPrice: 'Carbon Price Trends (USD/t)',
    chartRadar: '5-Dimension ETS Comparison',
    chartGantt: 'Allocation Phase Timeline (2005 \u2192 2040)',
    chartMethod: 'Allocation Method Mix (%)',
    chartScatter: 'ETS Position Map: System Age vs Carbon Price',
    aboutTitle: 'About This Dashboard',
    detailCompare: 'Detailed Comparison',
    allocPath: 'Allocation Method Migration Path',
    twoWorlds: '\u201CTwo Worlds\u201D \u2014 EU vs Asia ETS Paradigm',
    keyInsights: 'Key Insights',
    convAxes: '\u2192 5 Convergence Axes',
    divAxes: '\u2190 5 Divergence Axes',
    searchPlaceholder: 'Search across all 4 languages...',
    showingTerms: 'Showing',
    ofTerms: 'of',
    terms: 'terms',
    allCats: 'All',
    category: 'Category',
    metric: 'Metric',
    year: 'Year',
    bubbleNote: 'Bubble size = Covered emissions (relative)',
    solidFaded: 'Solid = Current (2026) | Faded = Predicted (2030)',
    jpNoPrice: 'Japan GX-ETS: no market price yet',
    cbamNote: 'CBAM is the bridge forcing convergence \u2014 Asia must either raise carbon prices or pay the EU difference',
    euWorld: 'EU World',
    asiaWorld: 'Asia World',
    phaseView: 'Phase:',
    pageBankingTitle: 'Banking Rules',
    pageBankingSub: 'How allowance carryover rules shape market behavior across 4 ETS systems',
    chartPhaseEvo: 'K-ETS Phase Evolution: Restriction vs Market Activity',
    chartTrading: 'K-ETS Trading Volume & Price (2015\u20132022)',
    chartCountryCompare: '4-Country Banking Rule Comparison',
    simTitle: 'Carryover Limit Simulator',
    simSub: 'Adjust net sales volume to see how much you can bank',
    simNetSales: 'Net Sales (tCO2)',
    simCarryover: 'Carryover Limit (tCO2)',
    simYear1: 'Year 1',
    simYear2: 'Year 2',
    simMinGuarantee: 'Min guarantee applied',
    bankingInsights: 'Key Insights',
    volume: 'Volume (Mt)',
    priceKRW: 'Price (\u20A9/t)',
    freeAlloc: 'Free Allocation %',
    auctionPct: 'Auction %',
    restriction: 'Restriction',
    banking: 'Banking',
    borrowing: 'Borrowing',
    offset: 'Offset',
    stabilization: 'Stabilization'
  },
  ja: {
    dashTitle: 'ETS\u7D71\u5408\u5206\u6790\u30C0\u30C3\u30B7\u30E5\u30DC\u30FC\u30C9',
    dashSub: '4\u30AB\u56FDETS\u5236\u5EA6\u306E2030\u5E74\u306B\u5411\u3051\u305F\u7D71\u5408\u5206\u6790',
    footer: 'JIN-Z-pop and his merry AI brothers | Plotly.js',
    price: '\u4FA1\u683C', coverage: '\u30AB\u30D0\u30FC\u7387', entities: '\u5BFE\u8C61\u4F01\u696D', since: '\u958B\u59CB',
    eu: 'EU', korea: '\u97D3\u56FD', china: '\u4E2D\u56FD', japan: '\u65E5\u672C',
    usdPerTon: 'USD/t', approx: '\u7D04',
    convergence: '\u53CE\u675F', divergence: '\u4E56\u96E2',
    source: '\u51FA\u5178', noData: '\u5E02\u5834\u30C7\u30FC\u30BF\u672A\u5F62\u6210',
    pageCompareTitle: '\u5236\u5EA6\u6BD4\u8F03',
    pageCompareSub: '\u30EC\u30FC\u30C0\u30FC\u30C1\u30E3\u30FC\u30C8 \u2014 4\u30AB\u56FDETS\u306E5\u3064\u306E\u4E3B\u8981\u6B21\u5143\u3092\u6BD4\u8F03',
    pageAllocTitle: '\u5272\u5F53\u65B9\u5F0F\u306E\u9032\u5316',
    pageAllocSub: '\u904E\u53BB\u6392\u51FA\u91CF\u57FA\u6E96\u304B\u3089\u30D9\u30F3\u30C1\u30DE\u30FC\u30AF\u3001\u30AA\u30FC\u30AF\u30B7\u30E7\u30F3\u3078',
    pageCbamTitle: 'CBAM\u30A4\u30F3\u30D1\u30AF\u30C8\u5E74\u8868',
    pageCbamSub: 'EU\u70AD\u7D20\u56FD\u5883\u8ABF\u6574\u30E1\u30AB\u30CB\u30BA\u30E0 \u2014 \u5E74\u8868\u3068\u30A2\u30B8\u30A2ETS\u3078\u306E\u5F71\u97FF',
    pageConvTitle: '\u7D71\u5408\u5206\u6790\u30DE\u30C3\u30D7',
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
    convAxes: '\u2192 5\u3064\u306E\u53CE\u675F\u8981\u56E0',
    divAxes: '\u2190 5\u3064\u306E\u4E56\u96E2\u8981\u56E0',
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
    cbamNote: 'CBAM\u306F\u5236\u5EA6\u7D71\u5408\u3092\u4FC3\u3059\u67B6\u3051\u6A4B \u2014 \u30A2\u30B8\u30A2\u306F\u70AD\u7D20\u4FA1\u683C\u3092\u5F15\u304D\u4E0A\u3052\u308B\u304B\u3001EU\u5DEE\u984D\u3092\u652F\u6255\u3046',
    euWorld: 'EU\u306E\u4E16\u754C',
    asiaWorld: '\u30A2\u30B8\u30A2\u306E\u4E16\u754C',
    phaseView: '\u30D5\u30A7\u30FC\u30BA:',
    pageBankingTitle: '\u30D0\u30F3\u30AD\u30F3\u30B0\u30EB\u30FC\u30EB',
    pageBankingSub: '\u6392\u51FA\u67A0\u306E\u7E70\u8D8A\u898F\u5236\u304C\u5E02\u5834\u884C\u52D5\u3092\u3069\u3046\u5F62\u4F5C\u308B\u304B \u2014 4\u30AB\u56FD\u6BD4\u8F03',
    chartPhaseEvo: 'K-ETS\u30D5\u30A7\u30FC\u30BA\u5225\u9032\u5316\uFF1A\u898F\u5236 vs \u5E02\u5834\u6D3B\u52D5',
    chartTrading: 'K-ETS\u53D6\u5F15\u91CF\u30FB\u4FA1\u683C\u63A8\u79FB (2015\u20132022)',
    chartCountryCompare: '4\u30AB\u56FD\u30D0\u30F3\u30AD\u30F3\u30B0\u30EB\u30FC\u30EB\u6BD4\u8F03',
    simTitle: '\u7E70\u8D8A\u4E0A\u9650\u30B7\u30DF\u30E5\u30EC\u30FC\u30BF',
    simSub: '\u7D14\u58F2\u6E21\u91CF\u3092\u8ABF\u6574\u3057\u3066\u7E70\u8D8A\u53EF\u80FD\u91CF\u3092\u78BA\u8A8D',
    simNetSales: '\u7D14\u58F2\u6E21\u91CF (tCO2)',
    simCarryover: '\u7E70\u8D8A\u4E0A\u9650 (tCO2)',
    simYear1: '\u7B2C1\u5E74\u5EA6',
    simYear2: '\u7B2C2\u5E74\u5EA6',
    simMinGuarantee: '\u6700\u4F4E\u4FDD\u8A3C\u67A0\u9069\u7528',
    bankingInsights: '\u4E3B\u8981\u306A\u77E5\u898B',
    volume: '\u53D6\u5F15\u91CF (Mt)',
    priceKRW: '\u4FA1\u683C (\u20A9/t)',
    freeAlloc: '\u7121\u511F\u5272\u5F53 %',
    auctionPct: '\u30AA\u30FC\u30AF\u30B7\u30E7\u30F3 %',
    restriction: '\u898F\u5236',
    banking: '\u7E70\u8D8A',
    borrowing: '\u501F\u5165',
    offset: '\u30AA\u30D5\u30BB\u30C3\u30C8',
    stabilization: '\u5E02\u5834\u5B89\u5B9A\u5316'
  },
  ko: {
    dashTitle: 'ETS \uC218\uB834 \uB300\uC2DC\uBCF4\uB4DC',
    dashSub: '4\uAC1C\uAD6D ETS \uC81C\uB3C4\uC758 2030\uB144 \uC218\uB834\uACFC \uBD84\uAE30',
    footer: 'JIN-Z-pop and his merry AI brothers | Plotly.js',
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
    asiaWorld: '\uC544\uC2DC\uC544\uC758 \uC138\uACC4',
    phaseView: '\uD398\uC774\uC988:',
    pageBankingTitle: '\uBC45\uD0B9 \uADDC\uCE59',
    pageBankingSub: '\uBC30\uCD9C\uAD8C \uC774\uC6D4 \uADDC\uC81C\uAC00 \uC2DC\uC7A5 \uD589\uB3D9\uC744 \uC5B4\uB5BB\uAC8C \uD615\uC131\uD558\uB294\uAC00 \u2014 4\uAC1C\uAD6D \uBE44\uAD50',
    chartPhaseEvo: 'K-ETS \uB2E8\uACC4\uBCC4 \uC9C4\uD654: \uADDC\uC81C vs \uC2DC\uC7A5 \uD65C\uB3D9',
    chartTrading: 'K-ETS \uAC70\uB798\uB7C9 \uBC0F \uAC00\uACA9 \uCD94\uC774 (2015\u20132022)',
    chartCountryCompare: '4\uAC1C\uAD6D \uBC45\uD0B9 \uADDC\uCE59 \uBE44\uAD50',
    simTitle: '\uC774\uC6D4 \uC0C1\uD55C \uC2DC\uBBAC\uB808\uC774\uD130',
    simSub: '\uC21C\uB9E4\uB3C4\uB7C9\uC744 \uC870\uC808\uD558\uC5EC \uC774\uC6D4 \uAC00\uB2A5\uB7C9\uC744 \uD655\uC778\uD558\uC138\uC694',
    simNetSales: '\uC21C\uB9E4\uB3C4\uB7C9 (tCO2)',
    simCarryover: '\uC774\uC6D4 \uC0C1\uD55C (tCO2)',
    simYear1: '1\uCC28\uB144\uB3C4',
    simYear2: '2\uCC28\uB144\uB3C4',
    simMinGuarantee: '\uCD5C\uC18C\uBCF4\uC7A5 \uC801\uC6A9',
    bankingInsights: '\uD575\uC2EC \uC778\uC0AC\uC774\uD2B8',
    volume: '\uAC70\uB798\uB7C9 (Mt)',
    priceKRW: '\uAC00\uACA9 (\u20A9/t)',
    freeAlloc: '\uBB34\uC0C1\uD560\uB2F9 %',
    auctionPct: '\uACBD\uB9E4 %',
    restriction: '\uADDC\uC81C',
    banking: '\uC774\uC6D4',
    borrowing: '\uCC28\uC785',
    offset: '\uC624\uD504\uC14B',
    stabilization: '\uC2DC\uC7A5\uC548\uC815\uD654'
  },
  zh: {
    dashTitle: 'ETS\u8D8B\u540C\u4EEA\u8868\u677F',
    dashSub: '\u56DB\u56FDETS\u5236\u5EA62030\u5E74\u8D8B\u540C\u4E0E\u5206\u6B67',
    footer: 'JIN-Z-pop and his merry AI brothers | Plotly.js',
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
    twoWorlds: '\u201C\u4E24\u4E2A\u4E16\u754C\u201D \u2014 EU vs \u4E9A\u6D32ETS\u8303\u5F0F',
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
    asiaWorld: '\u4E9A\u6D32\u4E16\u754C',
    phaseView: '\u9636\u6BB5:',
    pageBankingTitle: '\u7ED3\u8F6C\u89C4\u5219',
    pageBankingSub: '\u914D\u989D\u7ED3\u8F6C\u89C4\u5236\u5982\u4F55\u5851\u9020\u5E02\u573A\u884C\u4E3A \u2014 \u56DB\u56FD\u6BD4\u8F83',
    chartPhaseEvo: 'K-ETS\u9636\u6BB5\u6F14\u53D8\uFF1A\u89C4\u5236 vs \u5E02\u573A\u6D3B\u52A8',
    chartTrading: 'K-ETS\u4EA4\u6613\u91CF\u4E0E\u4EF7\u683C\u8D8B\u52BF (2015\u20132022)',
    chartCountryCompare: '\u56DB\u56FD\u7ED3\u8F6C\u89C4\u5219\u6BD4\u8F83',
    simTitle: '\u7ED3\u8F6C\u4E0A\u9650\u6A21\u62DF\u5668',
    simSub: '\u8C03\u6574\u51C0\u5356\u51FA\u91CF\u67E5\u770B\u53EF\u7ED3\u8F6C\u91CF',
    simNetSales: '\u51C0\u5356\u51FA\u91CF (tCO2)',
    simCarryover: '\u7ED3\u8F6C\u4E0A\u9650 (tCO2)',
    simYear1: '\u7B2C1\u5E74',
    simYear2: '\u7B2C2\u5E74',
    simMinGuarantee: '\u6700\u4F4E\u4FDD\u969C\u9002\u7528',
    bankingInsights: '\u5173\u952E\u53D1\u73B0',
    volume: '\u4EA4\u6613\u91CF (Mt)',
    priceKRW: '\u4EF7\u683C (\u20A9/t)',
    freeAlloc: '\u514D\u8D39\u5206\u914D %',
    auctionPct: '\u62CD\u5356 %',
    restriction: '\u89C4\u5236',
    banking: '\u7ED3\u8F6C',
    borrowing: '\u501F\u5165',
    offset: '\u62B5\u6D88',
    stabilization: '\u5E02\u573A\u7A33\u5B9A\u5316'
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
  document.querySelectorAll('.nav-link').forEach(a => {
    const page = NAV_PAGES.find(p => p.id === a.dataset.pageId);
    if (page) a.textContent = page[lang] || page.en;
  });
  window.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
}

// --- Navigation ---
function createNavHTML(currentPageId) {
  const lang = getLang();
  const links = NAV_PAGES.map(p => {
    const active = p.id === currentPageId ? ' nav-active' : '';
    return `<a href="${p.href}" class="nav-link${active}" data-page-id="${p.id}">${p[lang] || p.en}</a>`;
  }).join('');

  const langOptions = ['en','ja','ko','zh'].map(l => {
    const labels = { en: 'EN', ja: 'JA', ko: 'KO', zh: 'ZH' };
    const active = lang === l ? ' lang-active' : '';
    return `<button class="lang-btn${active}" onclick="switchLang('${l}')">${labels[l]}</button>`;
  }).join('');

  return `<nav class="top-nav">
    <a href="index.html" class="nav-brand">
      <span class="brand-mark"></span>
      <span class="brand-text" data-i18n="dashTitle">${t('dashTitle')}</span>
    </a>
    <div class="nav-links">${links}</div>
    <div class="lang-switcher">${langOptions}</div>
    <button class="nav-hamburger" onclick="this.parentElement.classList.toggle('open')" aria-label="Menu">\u2261</button>
  </nav>`;
}

function createFooterHTML() {
  return `<footer class="dash-footer">
    <div class="footer-rule"></div>
    <span data-i18n="footer">${t('footer')}</span>
  </footer>`;
}

// --- Common CSS (Editorial/Magazine v2) ---
function getCommonCSS() {
  return `
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
  --bg: ${THEME.bg};
  --card: ${THEME.card};
  --border: ${THEME.border};
  --text: ${THEME.text};
  --muted: ${THEME.muted};
  --dimmed: ${THEME.dimmed};
  --accent: ${THEME.accent};
  --gold: ${THEME.gold};
  --hover: ${THEME.hover};
  --eu: ${THEME.countries.EU};
  --korea: ${THEME.countries.Korea};
  --china: ${THEME.countries.China};
  --japan: ${THEME.countries.Japan};
  --font-display: 'DM Serif Display', 'Noto Serif JP', 'Noto Serif KR', 'Noto Serif SC', Georgia, serif;
  --font-body: 'DM Sans', 'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', system-ui, sans-serif;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-body);
  font-size: 17px;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  position: relative;
}

/* --- Grain overlay --- */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  opacity: 0.03;
  pointer-events: none;
  z-index: 9999;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 200px;
}

/* --- Ambient light --- */
body::after {
  content: '';
  position: fixed;
  top: -30%; left: 50%; transform: translateX(-50%);
  width: 120vw; height: 60vh;
  background: radial-gradient(ellipse, rgba(91,164,217,0.06) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* --- Fade-in animation --- */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-in {
  opacity: 0;
  animation: fadeUp 0.5s ease-out forwards;
}

/* ==================== NAV ==================== */
.top-nav {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 32px;
  background: rgba(12,17,23,0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}

.nav-brand {
  display: flex; align-items: center; gap: 10px;
  text-decoration: none; white-space: nowrap;
}
.brand-mark {
  display: inline-block; width: 8px; height: 24px;
  background: linear-gradient(180deg, var(--accent), var(--gold));
  border-radius: 2px;
}
.brand-text {
  font-family: var(--font-display);
  font-size: 1.15em; color: var(--text);
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex; gap: 2px; flex: 1; justify-content: center;
}
.nav-link {
  padding: 6px 16px;
  text-decoration: none; color: var(--muted);
  font-size: 0.9em; font-weight: 500;
  letter-spacing: 0.02em;
  border-bottom: 2px solid transparent;
  transition: color 0.2s, border-color 0.3s;
}
.nav-link:hover {
  color: var(--text);
  border-bottom-color: var(--dimmed);
}
.nav-link.nav-active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

.lang-switcher {
  display: flex; gap: 2px;
}
.lang-btn {
  background: none; border: 1px solid transparent;
  color: var(--dimmed); font-size: 0.8em; font-weight: 600;
  letter-spacing: 0.08em; padding: 4px 8px;
  border-radius: 4px; cursor: pointer;
  transition: all 0.2s; font-family: var(--font-body);
}
.lang-btn:hover {
  color: var(--muted); border-color: var(--border);
}
.lang-btn.lang-active {
  color: var(--gold); border-color: var(--gold);
}

.nav-hamburger {
  display: none; background: none; border: none;
  color: var(--text); font-size: 1.5em;
  cursor: pointer; padding: 4px 8px;
  line-height: 1;
}

@media (max-width: 768px) {
  .top-nav { padding: 12px 16px; }
  .nav-links {
    display: none; order: 10; width: 100%;
    flex-direction: column; gap: 0; padding-top: 12px;
    border-top: 1px solid var(--border); margin-top: 8px;
  }
  .nav-link { padding: 10px 0; border-bottom: none; }
  .top-nav.open .nav-links { display: flex; }
  .nav-hamburger { display: block; }
  .brand-text { font-size: 1em; }
  .lang-switcher { margin-left: auto; }
}

/* ==================== PAGE HEADER ==================== */
.page-header {
  text-align: center;
  padding: 28px 32px 18px;
  position: relative;
}
.page-header h1 {
  font-family: var(--font-display);
  font-size: 2em; font-weight: 400;
  color: var(--text);
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}
.page-header p {
  color: var(--muted); font-size: 0.92em;
  font-weight: 400; letter-spacing: 0.01em;
}
.page-header::after {
  content: '';
  display: block; width: 48px; height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--gold));
  margin: 20px auto 0;
  border-radius: 1px;
}

/* ==================== CARDS ==================== */
.cards {
  display: flex; gap: 16px; padding: 0 32px 28px;
  flex-wrap: wrap; justify-content: center;
  max-width: 1400px; margin: 8px auto 0;
}
.card {
  background: var(--card);
  border-radius: 8px; padding: 24px 28px;
  font-size: 18px;
  min-width: 220px; text-align: center;
  border: 1px solid var(--border);
  flex: 1; max-width: 310px;
  position: relative; overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.card .country-flag { font-size: 1.5em; }
.card .country-name {
  font-size: 0.82em; color: var(--muted);
  margin: 6px 0 10px;
  text-transform: uppercase; letter-spacing: 0.15em;
  font-weight: 600;
}
.card .value {
  font-family: var(--font-display);
  font-size: 1.8em; font-weight: 400;
  line-height: 1.2;
}
.card .label { color: var(--muted); font-size: 0.8em; margin-top: 6px; }
.card .sub { color: var(--dimmed); font-size: 0.82em; margin-top: 3px; }

/* ==================== CHARTS ==================== */
.chart-wrap {
  padding: 6px 32px; max-width: 1400px; margin: 0 auto;
}
.chart-box {
  background: var(--card);
  border-radius: 8px; margin-bottom: 12px;
  padding: 8px 20px 8px; border: 1px solid var(--border);
  transition: border-color 0.3s;
  min-height: 420px;
}
.chart-box:hover {
  border-color: var(--dimmed);
}

/* ==================== SECTIONS ==================== */
.section-title {
  font-family: var(--font-display);
  color: var(--text); font-size: 1.3em; font-weight: 400;
  margin: 32px 0 16px; padding-left: 32px;
  letter-spacing: -0.01em;
  position: relative;
}
.section-title::before {
  content: '';
  position: absolute; left: 20px; top: 50%;
  width: 4px; height: 60%; transform: translateY(-50%);
  background: var(--gold);
  border-radius: 2px;
}

/* ==================== ANALYSIS BOX ==================== */
.analysis-box {
  background: var(--card);
  border-radius: 8px; padding: 28px 32px;
  border: 1px solid var(--border);
  border-left: 3px solid var(--gold);
  margin: 16px 32px; max-width: 1400px;
  margin-left: auto; margin-right: auto;
  color: var(--text); line-height: 1.75;
}
.analysis-box h3 {
  font-family: var(--font-display);
  color: var(--text); margin-bottom: 12px;
  font-size: 1.15em; font-weight: 400;
}
.analysis-box p {
  margin-bottom: 12px; font-size: 0.9em;
  color: var(--muted);
}

/* ==================== PHASE SELECTOR ==================== */
.phase-btn {
  padding: 5px 14px; border-radius: 4px; font-size: 0.8em;
  font-family: var(--font-body); font-weight: 500;
  background: transparent; color: var(--btn-c, var(--muted));
  border: 1px solid var(--btn-c, var(--border));
  cursor: pointer; transition: all 0.2s;
}
.phase-btn:hover {
  background: color-mix(in srgb, var(--btn-c, var(--accent)) 15%, transparent);
}
.phase-btn-active {
  background: color-mix(in srgb, var(--btn-c, var(--accent)) 25%, transparent);
  color: var(--text); border-color: var(--btn-c, var(--accent));
  box-shadow: 0 0 8px color-mix(in srgb, var(--btn-c, var(--accent)) 30%, transparent);
}
.analysis-box code {
  background: rgba(91,164,217,0.1);
  color: var(--accent);
  padding: 2px 7px; border-radius: 3px;
  font-size: 0.86em;
}

/* ==================== FOOTER ==================== */
.dash-footer {
  text-align: center; padding: 28px 32px;
  color: var(--dimmed); font-size: 0.86em;
  letter-spacing: 0.03em;
}
.footer-rule {
  width: 64px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 0 auto 16px;
}

/* ==================== TABLE (Rosetta, Compare) ==================== */
table { border-collapse: collapse; }
th {
  font-family: var(--font-body);
  font-weight: 600; font-size: 0.78em;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}

/* ==================== MISC ==================== */
mark {
  background: rgba(232,196,104,0.25);
  color: var(--text);
  padding: 0 3px; border-radius: 2px;
}

::selection {
  background: rgba(91,164,217,0.3);
  color: var(--text);
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--dimmed); }
`;
}

// --- Plotly ---
function darkLayout(title, extra) {
  return Object.assign({
    height: 420,
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: THEME.card,
    font: { color: THEME.text, family: "'DM Sans', system-ui, sans-serif", size: 12 },
    title: {
      text: title,
      font: { color: THEME.text, size: 15, family: "'DM Serif Display', Georgia, serif" },
      x: 0.02, xanchor: 'left', y: 1, yanchor: 'top', pad: { t: 4 }
    },
    xaxis: {
      gridcolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 },
      linecolor: THEME.border
    },
    yaxis: {
      gridcolor: THEME.border, zerolinecolor: THEME.border,
      tickfont: { color: THEME.muted, size: 11 },
      linecolor: THEME.border
    },
    margin: { l: 60, r: 30, t: 52, b: 50 },
    legend: { font: { color: THEME.muted, size: 11 }, bgcolor: 'rgba(0,0,0,0)' },
    hoverlabel: {
      bgcolor: THEME.card, bordercolor: THEME.border,
      font: { color: THEME.text, family: "'DM Sans', system-ui, sans-serif", size: 12 }
    }
  }, extra || {});
}

var plotlyConfig = { responsive: true, displayModeBar: false };

// --- Staggered fade-in ---
function applyFadeIn() {
  const targets = document.querySelectorAll('.card, .chart-box, .analysis-box, .two-worlds, .timeline');
  targets.forEach((el, i) => {
    el.classList.add('fade-in');
    el.style.animationDelay = `${i * 60}ms`;
  });
}

// --- Page init ---
function initPage(pageId) {
  // Google Fonts preconnect
  const preconnect = document.createElement('link');
  preconnect.rel = 'preconnect';
  preconnect.href = 'https://fonts.googleapis.com';
  document.head.appendChild(preconnect);
  const preconnect2 = document.createElement('link');
  preconnect2.rel = 'preconnect';
  preconnect2.href = 'https://fonts.gstatic.com';
  preconnect2.crossOrigin = 'anonymous';
  document.head.appendChild(preconnect2);

  // Inject CSS
  const style = document.createElement('style');
  style.textContent = getCommonCSS();
  document.head.appendChild(style);

  // Inject nav
  document.body.insertAdjacentHTML('afterbegin', createNavHTML(pageId));

  // Inject footer
  document.body.insertAdjacentHTML('beforeend', createFooterHTML());

  // Apply fade-in after DOM settles
  requestAnimationFrame(() => {
    requestAnimationFrame(applyFadeIn);
  });
}
