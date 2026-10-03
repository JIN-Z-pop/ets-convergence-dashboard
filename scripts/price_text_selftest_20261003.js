// shared.js の buildPriceTexts(prices, lang)・buildRadarPrice(prices) の単体試験(node)。
// shared.js から <formatYearlyPrice> と <priceText> の 2 区間だけを取り出して vm で回す(DOM に触れない純関数)。
//
// 使い方: node scripts/price_text_selftest_20261003.js [shared.js のパス]
//   rc 0 = 全部通った / rc 1 = 落ちた / rc 2 = 区間を取り出せない
//
// 期待値は関数とは別の作り方で出す(倍率は試験側で自分で割り算する・文は試験側で逐語に組む)。
// 見る物: (1)2026-10-02 の値(EU 74.86€/韓国 19,145₩/中国 85.23¥)で ja「約 6〜7 倍」・en「1/7–1/6」・ko/zh の倍率と分数
// (2)N == M の時は 1 つ (3)取れない市場が 1 つでもあれば数字は「—」・倍率の句なし・古い値なし
// (4)全言語・全ケースで undefined / NaN / /t/t が無い・旧固定値(€72 / $79 / 10 倍 等)が無い
// (5)年が市場で違う時(2026/2025) (6)レーダー: 17・15・取れなければ null(0 にしない)
// (7)対照: 丸めを Math.floor に変えた複製・en の分数の向きを逆にした複製・レーダーを floor にした複製は、この試験で落ちること。
//
// 非対象: 画面の描画(DOM)・loadPrices(取得)・fx の値そのもの・ko/zh の文の自然さ(画面の目視で確認する)。
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const sharedPath = process.argv[2] || path.join(__dirname, '..', 'shared.js');
const src = fs.readFileSync(sharedPath, 'utf8').replace(/\r\n/g, '\n');
const m1 = src.match(/\/\/ <formatYearlyPrice>\n([\s\S]*?)\/\/ <\/formatYearlyPrice>/);
const m2 = src.match(/\/\/ <priceText>\n([\s\S]*?)\/\/ <\/priceText>/);
if (!m1 || !m2) {
  console.log('FAIL: shared.js に <formatYearlyPrice> か <priceText> の区間が無い: ' + sharedPath);
  process.exit(2);
}

function load(code2) {
  const ctx = vm.createContext({});
  vm.runInContext(m1[1] + '\n' + code2 + '\nthis.__b = buildPriceTexts; this.__r = buildRadarPrice;', ctx);
  return { b: ctx.__b, r: ctx.__r };
}

// fx=1 にして avg の整数がそのまま usdValue になる入れ物(試験側の割り算と突き合わせやすい)
const FX1 = { EUR_USD: 1, KRW_USD: 1, CNY_USD: 1 };
const mk = (eu, kr, cn, years) => {
  const y = years || ['2026', '2026', '2026'];
  const p = { fx: FX1 };
  if (eu !== null) p.eu_eur = [{ year: y[0], avg_price: eu }];
  if (kr !== null) p.korea_krw = [{ year: y[1], avg_price: kr }];
  if (cn !== null) p.china_cny = [{ year: y[2], avg_price: cn }];
  return p;
};
// 2026-10-02 の実際の値(本物の fx)
const REAL = {
  eu_eur: [{ year: '2025', avg_price: 70.0 }, { year: '2026', avg_price: 74.86 }],
  korea_krw: [{ year: '2026', avg_price: 19145 }],
  china_cny: [{ year: '2026', avg_price: 85.23 }],
  fx: { EUR_USD: 1.1, KRW_USD: 0.0007142857142857143, CNY_USD: 0.1388888888888889 }
};

const LANGS = ['ja', 'en', 'ko', 'zh'];
const BAD = ['undefined', 'NaN', '/t/t', '[object', '€72', '$79', '~$8', '~$11', '$8-11', '$8-$11', '10x', '10倍', '10배', '桁違い', '자릿수', '量级', 'Order of magnitude', '1/10'];

function runAll(fns) {
  const fails = [];
  const eq = (name, got, want) => { if (got !== want) fails.push(`${name}\n    got =${JSON.stringify(got)}\n    want=${JSON.stringify(want)}`); };
  const has = (name, s, sub) => { if (!String(s).includes(sub)) fails.push(`${name}: 「${sub}」が無い: ${JSON.stringify(s)}`); };
  const hasNot = (name, s, sub) => { if (String(s).includes(sub)) fails.push(`${name}: 「${sub}」が有る: ${JSON.stringify(s)}`); };

  // (1) 2026-10-02 の値: EU 74.86×1.1→82・韓国 19145×0.000714→14・中国 85.23×0.1389→12 → N=round(82/14)=6・M=round(82/12)=7
  const eu = Math.round(74.86 * 1.1), kr = Math.round(19145 * 0.0007142857142857143), cn = Math.round(85.23 * 0.1388888888888889);
  eq('試験側の USD(EU)', eu, 82); eq('試験側の USD(KR)', kr, 14); eq('試験側の USD(CN)', cn, 12);
  const N = Math.round(eu / Math.max(kr, cn)), M = Math.round(eu / Math.min(kr, cn));
  eq('試験側の N', N, 6); eq('試験側の M', M, 7);
  const ja = fns.b(REAL, 'ja'), en = fns.b(REAL, 'en'), ko = fns.b(REAL, 'ko'), zh = fns.b(REAL, 'zh');
  eq('ja t1', ja.t1, '炭素価格 €74.86/t（2026 年平均）— 世界最高水準');
  eq('ja t2', ja.t2, '炭素価格$12〜$14/t（2026 年平均）— EU の約 6〜7 分の 1');
  eq('ja t3Title', ja.t3Title, '2. 大きな価格差');
  eq('ja t3Desc', ja.t3Desc, 'EU 約 $82/t vs 韓国 約 $14/t vs 中国 約 $12/t（2026 年平均・約 6〜7 倍）。この差は、異なる経済的優先順位と炭素コスト許容度を反映。');
  eq('ja t4Gap', ja.t4Gap, '約 6〜7 倍の格差（$12〜$14 vs $82）');
  eq('en t1', en.t1, '€74.86/t carbon price (2026 avg) — among the world\'s highest');
  eq('en t2', en.t2, '$12–$14/t carbon prices (2026 avg) — about 1/7–1/6 of EU');
  eq('en t3Title', en.t3Title, '2. Large Price Gap');
  eq('ko t3Title', ko.t3Title, '2. 큰 가격 격차');
  eq('zh t3Title', zh.t3Title, '2. 显著价格差');   // 「巨大」は ja「大きな」・en「Large」・ko「큰」より強い=4 言語で主張の強さを揃える
  eq('en t3Desc', en.t3Desc, 'EU ~$82/t vs Korea ~$14/t vs China ~$12/t (2026 avg, about 6–7x). The gap reflects different economic priorities and carbon cost tolerance.');
  eq('en t4Gap', en.t4Gap, 'roughly 6–7x gap ($12–$14 vs $82)');
  has('ko t2', ko.t2, '$12~$14/t'); has('ko t2', ko.t2, 'EU의 약 6~7분의 1'); has('ko t3Desc', ko.t3Desc, '약 6~7배'); has('ko t4Gap', ko.t4Gap, '약 6~7배 격차($12~$14 vs $82)');
  has('zh t2', zh.t2, '$12～$14/t'); has('zh t2', zh.t2, '约为EU的1/7～1/6'); has('zh t3Desc', zh.t3Desc, '约6～7倍'); has('zh t4Gap', zh.t4Gap, '约6～7倍差距($12～$14 vs $82)');
  eq('n', ja.n, 6); eq('m', ja.m, 7);

  // (2) N == M: EU 82・韓国 14・中国 13 → N=round(82/14)=6・M=round(82/13)=round(6.31)=6
  const same = mk(82, 14, 13);
  const sj = fns.b(same, 'ja'), se = fns.b(same, 'en'), sk = fns.b(same, 'ko'), sz = fns.b(same, 'zh');
  eq('N==M ja t2', sj.t2, '炭素価格$13〜$14/t（2026 年平均）— EU の約 6 分の 1');
  eq('N==M ja t4Gap', sj.t4Gap, '約 6 倍の格差（$13〜$14 vs $82）');
  eq('N==M en t2', se.t2, '$13–$14/t carbon prices (2026 avg) — about 1/6 of EU');
  has('N==M en t3Desc', se.t3Desc, 'about 6x)'); has('N==M ko t2', sk.t2, 'EU의 약 6분의 1'); has('N==M zh t2', sz.t2, '约为EU的1/6');
  // lo == hi(韓国も中国も 13): 範囲でなく 1 つ
  const one = fns.b(mk(82, 13, 13), 'en');
  eq('lo==hi en t2', one.t2, '$13/t carbon prices (2026 avg) — about 1/6 of EU');

  // (3) 取れない市場が 1 つでもあれば「—」・倍率の句なし・古い値なし
  const cases = {
    'KR なし': mk(82, null, 12), 'CN なし': mk(82, 14, null), 'EU なし': mk(null, 14, 12), '全部なし': mk(null, null, null),
    'prices null': null, 'prices undefined': undefined, 'avg が文字列': { eu_eur: [{ year: '2026', avg_price: '74.86' }], fx: FX1 },
    'fx なし': { eu_eur: [{ year: '2026', avg_price: 74.86 }], korea_krw: [{ year: '2026', avg_price: 19145 }], china_cny: [{ year: '2026', avg_price: 85.23 }] }
  };
  for (const [name, p] of Object.entries(cases)) {
    for (const lang of LANGS) {
      const r = fns.b(p, lang);
      const all = [r.t1, r.t2, r.t3Desc, r.t4Gap].join(' | ');
      const nth = name + ' ' + lang;
      if (!all.includes('—')) fails.push(`${nth}: 「—」が無い: ${all}`);
      for (const bad of ['倍', '배', 'x)', '分の', '분의', '1/']) hasNot(nth + ' 倍率句', r.t2 + r.t3Desc + r.t4Gap, bad);
      if (r.n !== null || r.m !== null) fails.push(`${nth}: 倍率 n/m が null でない`);
    }
  }
  // 部分的に取れた時、取れた数字は残り取れない所だけ「—」
  eq('KR なし ja t3Desc', fns.b(mk(82, null, 12), 'ja').t3Desc, 'EU 約 $82/t vs 韓国 — vs 中国 約 $12/t。この差は、異なる経済的優先順位と炭素コスト許容度を反映。');
  // 欠け時の T3: 取れない市場は「—」だけ(/t も約も付けない)・取れた市場は従来どおり。4 言語
  const nc = { ja: 'EU 約 $82/t vs 韓国 約 $14/t vs 中国 — ', en: 'EU ~$82/t vs Korea ~$14/t vs China — ', ko: 'EU 약 $82/t vs 한국 약 $14/t vs 중국 — ', zh: 'EU 约$82/t vs 韩国 约$14/t vs 中国 — ' };
  for (const lang of LANGS) {
    const d = fns.b(mk(82, 14, null), lang).t3Desc;
    if (!d.startsWith(nc[lang].trim()) ) fails.push(`欠け T3 ${lang}: ${JSON.stringify(d)}`);
    hasNot('欠け T3 ' + lang + ' —/t', d, '—/t');
  }
  eq('EU なし ja t1', fns.b(mk(null, 14, 12), 'ja').t1, '炭素価格 —');
  eq('KR なし en t2', fns.b(mk(82, null, 12), 'en').t2, 'Carbon price —');

  // (4) 全言語・全ケース(正常・N==M・欠け)で禁止語が無い
  const pool = [REAL, same, mk(82, 13, 13), ...Object.values(cases)];
  for (const p of pool) {
    for (const lang of LANGS) {
      const r = fns.b(p, lang);
      for (const k of ['t1', 't2', 't3Title', 't3Desc', 't4Gap']) {
        for (const bad of BAD) {
          // 数字で終わる語(~$8・€72・$79 等)は「~$82」のような正当な 2 桁に部分一致させない=後ろが数字でない時だけ
          const re = new RegExp(bad.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + (/\d$/.test(bad) ? '(?!\\d)' : ''));
          if (re.test(r[k])) fails.push(`禁止語 ${lang}.${k}: 「${bad}」が有る: ${JSON.stringify(r[k])}`);
        }
      }
    }
  }

  // (5) 年が市場で違う: 中国だけ 2025 → asia 文は「2026/2025」・EU 文は EU の年
  const ys = fns.b(mk(82, 14, 12, ['2026', '2026', '2025']), 'ja');
  has('年違い t2', ys.t2, '（2026/2025 年平均）'); has('年違い t1', ys.t1, '（2026 年平均）'); has('年違い t3Desc', ys.t3Desc, '（2026/2025 年平均・約 6〜7 倍）');

  // (6) レーダー: 14/82=17.07→17・12/82=14.63→15・取れなければ null
  const rd = fns.r(REAL);
  eq('radar Korea', rd && rd.Korea, Math.round(kr / eu * 100)); eq('radar China', rd && rd.China, Math.round(cn / eu * 100));
  eq('radar Korea 値', rd && rd.Korea, 17); eq('radar China 値', rd && rd.China, 15);
  // 韓国 16/82=19.51(round=20・floor=19)・中国 12/82=14.63(15)=floor と round が分かれる入力(10-02 の値では韓国が 17.07 で分からない)
  const rd2 = fns.r(mk(82, 16, 12));
  eq('radar Korea 19.51→20', rd2 && rd2.Korea, 20); eq('radar China 14.63→15', rd2 && rd2.China, 15);
  for (const [name, p] of Object.entries(cases)) eq('radar null: ' + name, fns.r(p), null);
  return fails;
}

// ---- 本体 ----
const real = load(m2[1]);
const fails = runAll(real);
if (fails.length) {
  console.log('FAIL (本体): ' + fails.length + ' 件(先頭 8 件)');
  fails.slice(0, 8).forEach(x => console.log('  ' + x));
  process.exit(1);
}
console.log('OK: 本体 全項目通過(4 言語 × 正常・N==M・lo==hi・欠け 8 通り・年違い・レーダー)');

// ---- (7) 対照: 壊した複製が落ちること ----
const mutants = [
  ['倍率の N を Math.floor に(6→5)', 'N = Math.round(eu.v / hi);', 'N = Math.floor(eu.v / hi);'],
  ['en の分数の向きを逆に(1/7–1/6→1/6–1/7)', "'1/' + M + T.sep + '1/' + N)\n      : lang === 'zh'", "'1/' + N + T.sep + '1/' + M)\n      : lang === 'zh'"],
  ['レーダーの韓国を Math.floor に', 'Math.round(kr.v / eu.v * 100)', 'Math.floor(kr.v / eu.v * 100)'],
  ['レーダーの中国を Math.floor に(14.63→14)', 'Math.round(cn.v / eu.v * 100)', 'Math.floor(cn.v / eu.v * 100)'],
  ['取れない時にも倍率を出す(all を常に真に)', 'const all = !!(eu && kr && cn);', 'const all = true;'],
  ['欠け時の中国の句に「約 —/t」を付ける(修正前の形)', 'o.cP = cn ? T.ap(o.c) : DASH;', 'o.cP = T.ap(o.c);'],
  ['ko の範囲記号を日本語の波ダッシュに戻す(修正前の形)', "ko: {\n      sep: '~',", "ko: {\n      sep: '〜',"],
  ['レーダーが取れない時 null でなく 0', 'if (!(eu && kr && cn)) return null;', 'if (!(eu && kr && cn)) return { Korea: 0, China: 0 };'],
];
let bad = 0;
for (const [name, from, to] of mutants) {
  if (m2[1].split(from).length !== 2) {
    console.log(`FAIL: 対照の置換対象が 1 か所で見つからない(試験の足場が古い): ${name}`);
    bad++;
    continue;
  }
  let res;
  try { res = runAll(load(m2[1].replace(from, to))); } catch (e) { res = ['例外: ' + e.message]; }
  if (res.length === 0) {
    console.log(`FAIL: 壊した複製が通ってしまった=この試験はそれを捕まえられない: ${name}`);
    bad++;
  } else {
    console.log(`OK: 壊した複製は落ちる(${res.length} 件): ${name}`);
  }
}
if (bad) process.exit(1);
console.log('ALL PASS');
