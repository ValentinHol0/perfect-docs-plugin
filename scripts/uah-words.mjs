#!/usr/bin/env node
// uah-words — an amount in hryvnias and kopiyky written out in Ukrainian words, for invoices, acts,
// waybills and contracts ("сума прописом"). Zero dependencies, Node >= 18. Exact: no floating point.
//
// CLI:  node uah-words.mjs <amount> [--kop digits|words] [--capitalize] [--apostrophe typographic|ascii] [--json]
//       node uah-words.mjs 1234.56          -> одна тисяча двісті тридцять чотири гривні 56 копійок
//       node uah-words.mjs "1 234,56" --kop words --capitalize
// Input: "1234.56", "1234,56", "1 234,56" (spaces / no-break spaces as thousands separators), 0 <= amount < 10^12.
//        More than 2 decimal places is an error — round the amount first, never silently here.
// Library: import { uahToWords, parseAmount, integerToWords, pluralUk } from './uah-words.mjs'

import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const APOS = '’'; // typographic apostrophe used in the word tables below
const UNITS_M = ['', 'один', 'два', 'три', 'чотири', 'п’ять', 'шість', 'сім', 'вісім', 'дев’ять'];
const UNITS_F = ['', 'одна', 'дві', 'три', 'чотири', 'п’ять', 'шість', 'сім', 'вісім', 'дев’ять'];
const TEENS = ['десять', 'одинадцять', 'дванадцять', 'тринадцять', 'чотирнадцять', 'п’ятнадцять', 'шістнадцять', 'сімнадцять', 'вісімнадцять', 'дев’ятнадцять'];
const TENS = ['', '', 'двадцять', 'тридцять', 'сорок', 'п’ятдесят', 'шістдесят', 'сімдесят', 'вісімдесят', 'дев’яносто'];
const HUNDREDS = ['', 'сто', 'двісті', 'триста', 'чотириста', 'п’ятсот', 'шістсот', 'сімсот', 'вісімсот', 'дев’ятсот'];
// [one, few, many] + grammatical gender of the counted noun
const SCALES = [
  null, // units: the counted noun (гривня) is appended by the caller
  { forms: ['тисяча', 'тисячі', 'тисяч'], fem: true },
  { forms: ['мільйон', 'мільйони', 'мільйонів'], fem: false },
  { forms: ['мільярд', 'мільярди', 'мільярдів'], fem: false },
];
export const HRYVNIA = ['гривня', 'гривні', 'гривень'];
export const KOPIYKA = ['копійка', 'копійки', 'копійок'];
export const MAX_HRYVNIAS = 999_999_999_999;

/** Ukrainian plural form for an integer count: 1 гривня, 2–4 гривні, 0/5–20 гривень, 21 гривня, 111 гривень. */
export function pluralUk(n, [one, few, many]) {
  const n100 = n % 100;
  const n10 = n % 10;
  if (n100 >= 11 && n100 <= 14) return many;
  if (n10 === 1) return one;
  if (n10 >= 2 && n10 <= 4) return few;
  return many;
}

function triad(n, fem) {
  const out = [];
  const rest = n % 100;
  if (n >= 100) out.push(HUNDREDS[Math.floor(n / 100)]);
  if (rest >= 10 && rest < 20) out.push(TEENS[rest - 10]);
  else {
    if (rest >= 20) out.push(TENS[Math.floor(rest / 10)]);
    if (rest % 10) out.push((fem ? UNITS_F : UNITS_M)[rest % 10]);
  }
  return out;
}

/** Integer 0..999 999 999 999 in words; `fem` = gender of the noun that follows (гривня, копійка → true). */
export function integerToWords(n, fem = false) {
  if (!Number.isSafeInteger(n) || n < 0 || n > MAX_HRYVNIAS) throw new RangeError(`out of range: ${n}`);
  if (n === 0) return 'нуль';
  const words = [];
  const groups = [];
  for (let rest = n; rest > 0; rest = Math.floor(rest / 1000)) groups.push(rest % 1000);
  for (let i = groups.length - 1; i >= 0; i--) {
    const g = groups[i];
    if (!g) continue;
    const scale = SCALES[i];
    words.push(...triad(g, scale ? scale.fem : fem));
    if (scale) words.push(pluralUk(g, scale.forms));
  }
  return words.join(' ');
}

/** Parse an amount into exact integers { hryvnias, kopiyky }. Accepts a number or a string. */
export function parseAmount(input) {
  let s;
  if (typeof input === 'number') {
    if (!Number.isFinite(input)) throw new TypeError(`not a finite number: ${input}`);
    s = String(input);
    if (/e/i.test(s)) throw new RangeError(`amount out of range: ${input}`);
  } else if (typeof input === 'string') {
    s = input.trim().replace(/\s/g, '');
  } else throw new TypeError('amount must be a number or a string');
  if (s.startsWith('-')) throw new RangeError(`negative amount: ${input}`);
  if (s.includes(',') && s.includes('.')) throw new SyntaxError(`ambiguous separators in "${input}" — write 1234.56 or 1 234,56`);
  s = s.replace(',', '.');
  const m = s.match(/^(\d+)(?:\.(\d*))?$/);
  if (!m) throw new SyntaxError(`not an amount: "${input}"`);
  const frac = m[2] || '';
  if (frac.length > 2) throw new RangeError(`more than 2 decimal places in "${input}" — round to kopiyky first`);
  const hryvnias = Number(m[1]);
  if (!Number.isSafeInteger(hryvnias) || hryvnias > MAX_HRYVNIAS) throw new RangeError(`amount out of range (max ${MAX_HRYVNIAS}.99): ${input}`);
  return { hryvnias, kopiyky: Number(frac.padEnd(2, '0')) };
}

/**
 * Amount in words.
 * opts.kop: 'digits' (default, "56 копійок" — usual in invoices and acts) | 'words' ("п’ятдесят шість копійок")
 * opts.capitalize: first letter upper-case (default false)
 * opts.apostrophe: 'typographic' (default, ’ U+2019) | 'ascii' (' U+0027, for systems that reject U+2019)
 */
export function uahToWords(amount, opts = {}) {
  const { kop = 'digits', capitalize = false, apostrophe = 'typographic' } = opts;
  if (kop !== 'digits' && kop !== 'words') throw new TypeError(`kop must be "digits" or "words", got "${kop}"`);
  const { hryvnias, kopiyky } = parseAmount(amount);
  const uah = `${integerToWords(hryvnias, true)} ${pluralUk(hryvnias, HRYVNIA)}`;
  const kopText = kop === 'words' ? integerToWords(kopiyky, true) : String(kopiyky).padStart(2, '0');
  let out = `${uah} ${kopText} ${pluralUk(kopiyky, KOPIYKA)}`;
  if (apostrophe === 'ascii') out = out.replaceAll(APOS, "'");
  if (capitalize) out = out[0].toUpperCase() + out.slice(1);
  return out;
}

// CLI
const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const args = process.argv.slice(2);
  const flag = (name) => args.includes(name);
  const value = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
  const valued = new Set(['--kop', '--apostrophe']);
  const positional = args.filter((a, i) => !a.startsWith('--') && !valued.has(args[i - 1]));
  if (flag('--help') || positional.length !== 1) {
    console.log('Usage: node uah-words.mjs <amount> [--kop digits|words] [--capitalize] [--apostrophe typographic|ascii] [--json]');
    process.exit(flag('--help') ? 0 : 2);
  }
  try {
    const opts = { kop: value('--kop', 'digits'), capitalize: flag('--capitalize'), apostrophe: value('--apostrophe', 'typographic') };
    const words = uahToWords(positional[0], opts);
    if (flag('--json')) {
      const { hryvnias, kopiyky } = parseAmount(positional[0]);
      console.log(JSON.stringify({ amount: `${hryvnias}.${String(kopiyky).padStart(2, '0')}`, hryvnias, kopiyky, words }));
    } else console.log(words);
  } catch (e) {
    console.error(`uah-words: ${e.message}`);
    process.exit(1);
  }
}
