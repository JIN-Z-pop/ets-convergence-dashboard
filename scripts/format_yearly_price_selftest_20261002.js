// shared.js の formatYearlyPrice(prices, key) の単体試験(node)。
// shared.js から <formatYearlyPrice> ... </formatYearlyPrice> の間だけを取り出して vm で回す(DOM に触れない純関数)。
//
// 使い方: node scripts/format_yearly_price_selftest_20261002.js [shared.js のパス]
//   rc 0 = 全部通った / rc 1 = 落ちた / rc 2 = 関数を取り出せない
//
// 期待値は関数とは別の作り方で出す: 2 桁の値は「整数 cents」から文字列で小数点を挿して作る(avg*100 の丸めを使わない)。
// 見る物: (1)0.00〜200.00 の 20,001 点で EU・中国の price 文字列が期待と一致 (2)韓国の 3 桁区切り
// (3)year の最大を数値で取る (4)fx が無い時は USD 無し (5)配列が無い・空・avg が数値でない=null (6)USD=Math.round(avg x fx)
// (7)対照: 丸めを Math.floor に変えた複製と、cents を介さず toFixed(1) で 1 桁にした複製は、この試験で落ちること。
//
// 非対象: loadPrices(取得)・画面の描画。fx の値そのもの。
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const sharedPath = process.argv[2] || path.join(__dirname, '..', 'shared.js');
const src = fs.readFileSync(sharedPath, 'utf8').replace(/\r\n/g, '\n');
const m = src.match(/\/\/ <formatYearlyPrice>\n([\s\S]*?)\/\/ <\/formatYearlyPrice>/);
if (!m) {
  console.log('FAIL: shared.js に <formatYearlyPrice> の区間が無い: ' + sharedPath);
  process.exit(2);
}

function load(code) {
  const ctx = vm.createContext({});
  vm.runInContext(code + '\nthis.__f = formatYearlyPrice;', ctx);
  return ctx.__f;
}

function runAll(f) {
  const fails = [];
  const check = (name, got, want) => {
    if (JSON.stringify(got) !== JSON.stringify(want)) fails.push(`${name}: got=${JSON.stringify(got)} want=${JSON.stringify(want)}`);
  };
  const fx = { EUR_USD: 1.1, KRW_USD: 0.0007142857142857143, CNY_USD: 0.1388888888888889 };
  const mk = (key, avg, year) => ({ [key]: [{ year: year || '2026', avg_price: avg }], fx });

  // (1) 0.00〜200.00 の 20,001 点(EU・中国)
  let n = 0;
  for (let c = 0; c <= 20000; c++) {
    const avg = JSON.parse((Math.floor(c / 100) + '.' + String(c % 100).padStart(2, '0')));  // JSON が読む値と同じ double
    const want = Math.floor(c / 100) + '.' + String(c % 100).padStart(2, '0');
    const e = f(mk('eu_eur', avg), 'eu_eur');
    const ch = f(mk('china_cny', avg), 'china_cny');
    if (!e || e.price !== '€' + want + '/t') fails.push(`EU ${avg}: got=${e && e.price} want=€${want}/t`);
    if (!ch || ch.price !== '¥' + want + '/t') fails.push(`CN ${avg}: got=${ch && ch.price} want=¥${want}/t`);
    n++;
    if (fails.length > 20) break;
  }

  // (2) 韓国の 3 桁区切り
  for (const [avg, want] of [[0, '0'], [999, '999'], [1000, '1,000'], [19097.0, '19,097'], [1234567, '1,234,567'], [19097.4, '19,097'], [19097.5, '19,098']]) {
    const k = f(mk('korea_krw', avg), 'korea_krw');
    check('KR ' + avg, k && k.price, '₩' + want + '/t');
  }

  // (3) year の最大を数値で: "999" と "2026" は文字列比較だと "999" が勝つ
  const ys = { eu_eur: [{ year: '999', avg_price: 1.11 }, { year: '2026', avg_price: 74.86 }, { year: '2025', avg_price: 60.0 }], fx };
  const y = f(ys, 'eu_eur');
  check('year max', y && [y.year, y.price], ['2026', '€74.86/t']);

  // (4) fx が無い・不正 = USD 無し(price は出る)
  for (const bad of [undefined, {}, { EUR_USD: null }, { EUR_USD: 'x' }, { EUR_USD: 0 }]) {
    const r = f({ eu_eur: [{ year: '2026', avg_price: 74.86 }], fx: bad }, 'eu_eur');
    check('fx missing ' + JSON.stringify(bad), r && [r.price, r.usd, r.usdValue, r.table], ['€74.86/t', null, null, '~€74.86/t']);
  }
  const noFxKey = f({ eu_eur: [{ year: '2026', avg_price: 74.86 }] }, 'eu_eur');
  check('fx object absent', noFxKey && noFxKey.usd, null);

  // (5) null になる入力
  for (const [name, p, key] of [
    ['prices null', null, 'eu_eur'], ['prices undefined', undefined, 'eu_eur'], ['array absent', { fx }, 'eu_eur'],
    ['array empty', { eu_eur: [], fx }, 'eu_eur'], ['not array', { eu_eur: {}, fx }, 'eu_eur'],
    ['avg null', { eu_eur: [{ year: '2026', avg_price: null }], fx }, 'eu_eur'],
    ['avg string', { eu_eur: [{ year: '2026', avg_price: '74.86' }], fx }, 'eu_eur'],
    ['avg NaN', { eu_eur: [{ year: '2026', avg_price: NaN }], fx }, 'eu_eur'],
    ['avg negative', { eu_eur: [{ year: '2026', avg_price: -1 }], fx }, 'eu_eur'],
    ['unknown key', { jp: [{ year: '2026', avg_price: 1 }], fx }, 'jp'],
  ]) {
    check('null: ' + name, f(p, key), null);
  }

  // (6) USD = Math.round(avg x fx)・table の書式
  const eu = f(mk('eu_eur', 74.86), 'eu_eur');
  check('EU usd', eu && [eu.usd, eu.usdValue, eu.table], ['~$' + Math.round(74.86 * 1.1) + '/t', Math.round(74.86 * 1.1), '~€74.86/t (~$' + Math.round(74.86 * 1.1) + ')']);
  const kr = f(mk('korea_krw', 19097.0), 'korea_krw');
  check('KR usd', kr && [kr.usdValue, kr.table], [Math.round(19097.0 * 0.0007142857142857143), '~₩19,097/t (~$' + Math.round(19097.0 * 0.0007142857142857143) + ')']);
  const cn = f(mk('china_cny', 85.2), 'china_cny');
  check('CN 85.2 keeps 2 digits', cn && cn.price, '¥85.20/t');
  // EU の fx=1.1 で avg x fx が厳密に x.5 になる点(2 桁値 20,001 点のうち c*11 % 1000 == 500)で、Math.round が x.5 を上へ丸めること
  for (let c = 0; c <= 20000; c++) {
    if ((c * 11) % 1000 !== 500) continue;
    const avg = JSON.parse((Math.floor(c / 100) + '.' + String(c % 100).padStart(2, '0')));
    const r = f(mk('eu_eur', avg), 'eu_eur');
    check('USD tie c=' + c, r && r.usdValue, Math.floor((c * 11 + 500) / 1000));
  }
  return { fails, n };
}

// ---- 本体 ----
const real = load(m[1]);
const r = runAll(real);
if (r.fails.length) {
  console.log('FAIL (本体): ' + r.fails.length + ' 件(先頭 5 件)');
  r.fails.slice(0, 5).forEach(x => console.log('  ' + x));
  process.exit(1);
}
console.log(`OK: 本体 全項目通過(EU・中国の 2 桁値 ${r.n} 点を含む)`);

// ---- (7) 対照: 壊した複製が落ちること ----
const mutants = [
  ['Math.round(avg * 100) -> Math.floor(avg * 100)', 'Math.round(avg * 100)', 'Math.floor(avg * 100)'],
  ['2 桁を toFixed(1) 経由の 1 桁に', "const cents = Math.round(avg * 100);\n    num = Math.floor(cents / 100) + '.' + String(cents % 100).padStart(2, '0');", 'num = avg.toFixed(1);'],
  ['year を文字列比較に', 'Number(r.year) > Number(row.year)', 'String(r.year) > String(row.year)'],
  ['USD を Math.floor に', 'Math.round(avg * fx)', 'Math.floor(avg * fx)'],
];
let bad = 0;
for (const [name, from, to] of mutants) {
  if (m[1].split(from).length !== 2) {
    console.log(`FAIL: 対照の置換対象が 1 か所で見つからない(試験の足場が古い): ${name}`);
    bad++;
    continue;
  }
  const res = runAll(load(m[1].replace(from, to)));
  if (res.fails.length === 0) {
    console.log(`FAIL: 壊した複製が通ってしまった=この試験はそれを捕まえられない: ${name}`);
    bad++;
  } else {
    console.log(`OK: 壊した複製は落ちる(${res.fails.length} 件): ${name}`);
  }
}
if (bad) process.exit(1);
console.log('ALL PASS');
