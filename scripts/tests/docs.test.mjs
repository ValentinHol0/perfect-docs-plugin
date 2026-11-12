// Tests for perfect-docs-plugin scripts. Run: node --test scripts/tests/docs.test.mjs
// Python generators are exercised through child_process when python + the library are installed;
// the "missing library" message path is always exercised (python -S hides site-packages).
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { uahToWords, parseAmount, integerToWords, pluralUk, HRYVNIA } from '../uah-words.mjs';
import { findBrowser } from '../html-to-pdf.mjs';

const SCRIPTS = join(dirname(fileURLToPath(import.meta.url)), '..');
const EX = join(SCRIPTS, 'examples');
const NBSP = String.fromCharCode(0xa0);
const tmp = mkdtempSync(join(tmpdir(), 'docs-test-'));
const run = (cmd, args, opts = {}) => spawnSync(cmd, args, { encoding: 'utf8', timeout: 120000, ...opts });

// ---------- uah-words ----------
describe('uah-words', () => {
  const cases = [
    ['1234.56', 'одна тисяча двісті тридцять чотири гривні 56 копійок'],
    ['1', 'одна гривня 00 копійок'],
    ['2', 'дві гривні 00 копійок'],
    ['5', 'п’ять гривень 00 копійок'],
    ['11', 'одинадцять гривень 00 копійок'],
    ['12', 'дванадцять гривень 00 копійок'],
    ['13', 'тринадцять гривень 00 копійок'],
    ['14', 'чотирнадцять гривень 00 копійок'],
    ['21', 'двадцять одна гривня 00 копійок'],
    ['22.02', 'двадцять дві гривні 02 копійки'],
    ['41.21', 'сорок одна гривня 21 копійка'],
    ['101', 'сто одна гривня 00 копійок'],
    ['111.11', 'сто одинадцять гривень 11 копійок'],
    ['1000', 'одна тисяча гривень 00 копійок'],
    ['2000', 'дві тисячі гривень 00 копійок'],
    ['5000', 'п’ять тисяч гривень 00 копійок'],
    ['11000', 'одинадцять тисяч гривень 00 копійок'],
    ['21000', 'двадцять одна тисяча гривень 00 копійок'],
    ['1000000', 'один мільйон гривень 00 копійок'],
    ['1000001', 'один мільйон одна гривня 00 копійок'],
    ['2000000', 'два мільйони гривень 00 копійок'],
    ['5000000', 'п’ять мільйонів гривень 00 копійок'],
    ['2000000000', 'два мільярди гривень 00 копійок'],
    ['0.01', 'нуль гривень 01 копійка'],
    ['0', 'нуль гривень 00 копійок'],
    ['999999999999.99', 'дев’ятсот дев’яносто дев’ять мільярдів дев’ятсот дев’яносто дев’ять мільйонів дев’ятсот дев’яносто дев’ять тисяч дев’ятсот дев’яносто дев’ять гривень 99 копійок'],
  ];
  for (const [amount, words] of cases) test(`${amount} → ${words}`, () => assert.equal(uahToWords(amount), words));

  test('kopiyky in words keep feminine forms', () => {
    assert.equal(uahToWords('1.01', { kop: 'words' }), 'одна гривня одна копійка');
    assert.equal(uahToWords('2.02', { kop: 'words' }), 'дві гривні дві копійки');
    assert.equal(uahToWords('5.11', { kop: 'words' }), 'п’ять гривень одинадцять копійок');
    assert.equal(uahToWords('0.5', { kop: 'words' }), 'нуль гривень п’ятдесят копійок');
  });
  test('capitalize and ASCII apostrophe', () => {
    assert.equal(uahToWords('5', { capitalize: true }), 'П’ять гривень 00 копійок');
    assert.equal(uahToWords('9', { apostrophe: 'ascii' }), "дев'ять гривень 00 копійок");
  });
  test('parses Ukrainian and plain formats exactly', () => {
    assert.deepEqual(parseAmount('1 234,56'), { hryvnias: 1234, kopiyky: 56 });
    assert.deepEqual(parseAmount(`1${NBSP}234${NBSP}567,8`), { hryvnias: 1234567, kopiyky: 80 });
    assert.deepEqual(parseAmount(1234.5), { hryvnias: 1234, kopiyky: 50 });
    assert.deepEqual(parseAmount('7'), { hryvnias: 7, kopiyky: 0 });
  });
  test('rejects ambiguous or inexact input instead of rounding silently', () => {
    assert.throws(() => parseAmount('1.234'), /2 decimal places/);
    assert.throws(() => parseAmount(0.1 + 0.2), /2 decimal places/);
    assert.throws(() => parseAmount('1,234.56'), /ambiguous/);
    assert.throws(() => parseAmount('-5'), /negative/);
    assert.throws(() => parseAmount('abc'), /not an amount/);
    assert.throws(() => parseAmount(NaN), /finite/);
    assert.throws(() => parseAmount('1000000000000'), /out of range/);
    assert.throws(() => uahToWords('1', { kop: 'roman' }), /kop must be/);
  });
  test('plural rule covers 11–14 exceptions in every hundred', () => {
    for (const [n, form] of [[1, 'гривня'], [3, 'гривні'], [11, 'гривень'], [12, 'гривень'], [14, 'гривень'], [111, 'гривень'], [112, 'гривень'], [121, 'гривня'], [122, 'гривні'], [1001, 'гривня']]) {
      assert.equal(pluralUk(n, HRYVNIA), form, String(n));
    }
    assert.equal(integerToWords(1, false), 'один');
    assert.equal(integerToWords(1, true), 'одна');
  });
  test('CLI: words, --json, errors and usage', () => {
    const cli = join(SCRIPTS, 'uah-words.mjs');
    let r = run(process.execPath, [cli, '1234.56']);
    assert.equal(r.status, 0);
    assert.equal(r.stdout.trim(), 'одна тисяча двісті тридцять чотири гривні 56 копійок');
    r = run(process.execPath, [cli, '1 234,56', '--json', '--kop', 'words', '--capitalize']);
    assert.deepEqual(JSON.parse(r.stdout), { amount: '1234.56', hryvnias: 1234, kopiyky: 56, words: 'Одна тисяча двісті тридцять чотири гривні п’ятдесят шість копійок' });
    r = run(process.execPath, [cli, '1.234']);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /decimal places/);
    assert.equal(run(process.execPath, [cli]).status, 2);
  });
});

// ---------- html-to-pdf ----------
describe('html-to-pdf', () => {
  const cli = join(SCRIPTS, 'html-to-pdf.mjs');
  const html = join(tmp, 'deck.html');
  writeFileSync(html, `<!doctype html><html lang="uk"><meta charset="utf-8"><style>@page{size:1920px 1080px;margin:0}*{margin:0}.slide:last-child{break-after:auto}
    .slide{width:1920px;height:1080px;break-after:page;font:64px Arial}</style>
    <section class="slide">Слайд 1</section><section class="slide">Слайд 2</section></html>`);

  test('explains how to get an engine when none is available', () => {
    const r = run(process.execPath, [cli, html, join(tmp, 'x.pdf'), '--engine', 'browser', '--browser', join(tmp, 'no-such-browser.exe')]);
    assert.equal(r.status, 3);
    assert.match(r.stderr, /npm i -D playwright/);
    assert.match(r.stderr, /Chrome/);
  });
  test('usage error without arguments', () => assert.equal(run(process.execPath, [cli]).status, 2));
  test('findBrowser honours CHROME_PATH', () => {
    assert.equal(findBrowser({ CHROME_PATH: join(tmp, 'missing') }, 'linux'), null);
    assert.equal(findBrowser({ CHROME_PATH: html }, 'linux'), html);
  });
  const browser = findBrowser();
  test('prints one PDF page per slide with a local Chromium', { skip: browser ? false : 'no Chrome/Edge/Chromium installed' }, () => {
    const out = join(tmp, 'deck.pdf');
    const r = run(process.execPath, [cli, html, out, '--engine', 'browser']);
    assert.equal(r.status, 0, r.stderr);
    const pdf = readFileSync(out, 'latin1');
    assert.ok(pdf.startsWith('%PDF-'));
    assert.equal((pdf.match(/\/Type\s*\/Page(?![s\w])/g) || []).length, 2);
  });
});

// ---------- Python scripts ----------
const PY = ['python3', 'python'].find((c) => run(c, ['-c', 'import sys; print(sys.version_info[0])']).stdout?.trim() === '3');
const has = (mod) => Boolean(PY) && run(PY, ['-c', `import ${mod}`]).status === 0;
const hiddenBySiteless = (mod) => Boolean(PY) && run(PY, ['-S', '-c', `import ${mod}`]).status !== 0;
const py = (script, args) => run(PY, [join(SCRIPTS, script), ...args], { env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
const pyEval = (code, ...args) => {
  const r = run(PY, ['-c', `import sys; sys.stdout.reconfigure(encoding="utf-8")\n${code}`, ...args]);
  assert.equal(r.status, 0, r.stderr);
  return r.stdout;
};
const writeJson = (name, obj) => { const p = join(tmp, name); writeFileSync(p, JSON.stringify(obj)); return p; };
const example = (name) => JSON.parse(readFileSync(join(EX, name), 'utf8'));

describe('python: missing-library message', { skip: PY ? false : 'python 3 not found' }, () => {
  for (const [script, mod, pkg, args] of [
    ['make-docx.py', 'docx', 'python-docx', [join(EX, 'act.json'), join(tmp, 'a.docx')]],
    ['make-xlsx.py', 'openpyxl', 'openpyxl', [join(EX, 'workbook.json'), join(tmp, 'a.xlsx')]],
    ['make-pptx.py', 'pptx', 'python-pptx', [join(EX, 'deck.json'), join(tmp, 'a.pptx')]],
    ['pdf-tools.py', 'pypdf', 'pypdf', ['info', join(SCRIPTS, 'tests', 'docs.test.mjs')]],
  ]) {
    test(`${script} says "pip install ${pkg}" and exits 3`, { skip: hiddenBySiteless(mod) ? false : `${mod} importable without site-packages` }, () => {
      const r = run(PY, ['-S', join(SCRIPTS, script), ...args]);
      assert.equal(r.status, 3, r.stderr);
      assert.match(r.stderr, new RegExp(`pip install ${pkg}`));
    });
  }
});

describe('make-docx', { skip: has('docx') ? false : 'python-docx not installed' }, () => {
  const docText = (file) => pyEval('import docx\nd = docx.Document(sys.argv[1])\nprint("\\n".join(p.text for p in d.paragraphs))\nprint("\\n".join(c.text for t in d.tables for r in t.rows for c in r.cells))', file);

  test('act: totals, amount in words, required parts', () => {
    const out = join(tmp, 'act.docx');
    const r = py('make-docx.py', [join(EX, 'act.json'), out]);
    assert.equal(r.status, 0, r.stderr);
    const s = JSON.parse(r.stdout);
    assert.equal(s.total, '27345.56');
    assert.equal(s.vat, '0.00');
    assert.equal(s.words, 'Двадцять сім тисяч триста сорок п’ять гривень 56 копійок');
    const text = docText(out);
    assert.match(text, /АКТ №.27/);
    assert.ok(text.includes(`27${NBSP}345,56`), 'Ukrainian number format with no-break space');
    assert.ok(text.includes('Сума прописом: Двадцять сім тисяч триста сорок п’ять гривень 56 копійок, без ПДВ.'));
    assert.match(text, /Від Виконавця:[\s\S]*Від Замовника:/);
    assert.ok(text.includes(`Петро${NBSP}ПЕТРЕНКО`));
  });
  test('invoice with VAT included: VAT = total × 20/120, payment purpose', () => {
    const out = join(tmp, 'invoice.docx');
    const r = py('make-docx.py', [join(EX, 'invoice.json'), out]);
    assert.equal(r.status, 0, r.stderr);
    const s = JSON.parse(r.stdout);
    assert.deepEqual([s.subtotal, s.vat, s.total], ['9455.00', '1891.00', '11346.00']);
    const text = docText(out);
    assert.match(text, /Призначення платежу: Оплата за рахунком №.104 від 12\.11\.2026, у тому числі ПДВ 1.891,00.грн/);
    assert.match(text, /IBAN UA623052990000000000000000000/);
  });
  test('VAT on top is added to the subtotal and rounded half-up', () => {
    const data = { ...example('act.json'), vat: { mode: 'on_top', rate: 20 }, items: [{ name: 'Послуга', unit: 'послуга', qty: 1, price: '100.03' }] };
    const r = py('make-docx.py', [writeJson('ontop.json', data), join(tmp, 'ontop.docx')]);
    assert.equal(r.status, 0, r.stderr);
    const s = JSON.parse(r.stdout);
    assert.deepEqual([s.subtotal, s.vat, s.total], ['100.03', '20.01', '120.04']);
    assert.equal(s.words, 'Сто двадцять гривень 04 копійки');
  });
  test('waybill renders shipping signatures', () => {
    const out = join(tmp, 'waybill.docx');
    assert.equal(py('make-docx.py', [join(EX, 'waybill.json'), out]).status, 0);
    assert.match(docText(out), /Відвантажив\(ла\)[\s\S]*Отримав\(ла\)/);
  });
  test('rejects missing code, bad IBAN, missing signer and wrong total_words', () => {
    const base = example('invoice.json');
    for (const [data, re] of [
      [{ ...base, supplier: { ...base.supplier, code: '' } }, /supplier\.code is required/],
      [{ ...base, supplier: { ...base.supplier, iban: 'UA623052990000000000000000001' } }, /IBAN check/],
      [{ ...example('act.json'), buyer: { ...example('act.json').buyer, signer: '' } }, /buyer\.signer is required/],
      [{ ...base, total_words: 'Одна гривня 00 копійок' }, /total_words does not match/],
      [{ ...base, items: [] }, /at least one line/],
    ]) {
      const r = py('make-docx.py', [writeJson('bad.json', data), join(tmp, 'bad.docx')]);
      assert.equal(r.status, 1, r.stdout);
      assert.match(r.stderr, re);
    }
  });
});

describe('make-xlsx', { skip: has('openpyxl') ? false : 'openpyxl not installed' }, () => {
  test('writes live formulas, names, validation, freeze panes, chart and print setup', () => {
    const out = join(tmp, 'book.xlsx');
    const r = py('make-xlsx.py', [join(EX, 'workbook.json'), out]);
    assert.equal(r.status, 0, r.stderr);
    const s = JSON.parse(r.stdout);
    assert.deepEqual(s.names, ['vat_rate', 'grand_total']);
    assert.equal(s.charts, 1);
    const info = JSON.parse(pyEval(`import json, openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
a, b = wb["Кошторис"], wb["Графік оплат"]
print(json.dumps({"f6": a["F6"].value, "f9": a["F9"].value, "f10": a["F10"].value, "f11": a["F11"].value,
  "fmt": a["F6"].number_format, "freeze": a.freeze_panes, "filter": a.auto_filter.ref, "dv": len(a.data_validations.dataValidation),
  "charts": len(a._charts), "titles": a.print_title_rows, "fit": a.page_setup.fitToWidth, "paper": a.page_setup.paperSize,
  "d2": b["D2"].value, "d4": b["D4"].value, "date": b["A2"].number_format, "lists": wb["_lists"].sheet_state,
  "names": {n: wb.defined_names[n].attr_text for n in wb.defined_names}, "calc": wb.calculation.fullCalcOnLoad}, ensure_ascii=False))`, out));
    assert.equal(info.f6, '=ROUND(D6*E6,2)');
    assert.equal(info.f9, '=SUM(F6:F8)');
    assert.equal(info.f10, '=ROUND($F$9*vat_rate,2)');
    assert.equal(info.f11, '=$F$9+$F$10');
    assert.equal(info.d2, '=ROUND(C2*grand_total,2)');
    assert.equal(info.d4, '=grand_total-SUM(D2:D3)', 'last instalment takes the rounding remainder');
    assert.equal(info.freeze, 'A6');
    assert.equal(info.filter, 'A5:F8');
    assert.equal(info.dv, 3);
    assert.equal(info.charts, 1);
    assert.equal(info.titles, '$5:$5');
    assert.equal(info.fit, 1);
    assert.equal(String(info.paper), '9');
    assert.equal(info.date, 'DD.MM.YYYY');
    assert.equal(info.lists, 'hidden', 'long or comma-containing lists live on a hidden sheet');
    assert.equal(info.names.grand_total, "'Кошторис'!$F$11");
    assert.equal(info.calc, true);
  });
  test('rejects unknown columns and pasted formulas in data', () => {
    const bad1 = { sheets: [{ name: 'A', columns: [{ key: 'a', type: 'number', formula: '=[nope]*2' }], rows: [{}] }] };
    let r = py('make-xlsx.py', [writeJson('x1.json', bad1), join(tmp, 'x1.xlsx')]);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /unknown column \[nope\]/);
    const bad2 = { sheets: [{ name: 'A', columns: [{ key: 'a', type: 'number' }], rows: [{ a: '=1+1' }] }] };
    r = py('make-xlsx.py', [writeJson('x2.json', bad2), join(tmp, 'x2.xlsx')]);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /put formulas in the column/);
  });
});

describe('make-pptx', { skip: has('pptx') ? false : 'python-pptx not installed' }, () => {
  test('16:9 deck with titles, notes and no warnings for the example', () => {
    const out = join(tmp, 'deck.pptx');
    const r = py('make-pptx.py', [join(EX, 'deck.json'), out]);
    assert.equal(r.status, 0, r.stderr);
    const s = JSON.parse(r.stdout);
    assert.equal(s.slides, 7);
    assert.deepEqual(s.warnings, []);
    const info = JSON.parse(pyEval(`import json
from pptx import Presentation
p = Presentation(sys.argv[1])
print(json.dumps({"w": p.slide_width, "h": p.slide_height, "titles": [s.shapes.title.text if s.shapes.title else None for s in p.slides],
  "notes2": p.slides[1].notes_slide.notes_text_frame.text, "empty_ph": sum(1 for s in p.slides for ph in s.placeholders if ph.has_text_frame and not ph.text_frame.text.strip())}, ensure_ascii=False))`, out));
    assert.equal(Math.round((info.w / info.h) * 100), 178);
    assert.ok(info.titles.every(Boolean), 'every slide has a real title placeholder');
    assert.ok(info.titles[2].startsWith('Повторні клієнти'));
    assert.match(info.notes2, /ризик концентрації/);
    assert.equal(info.empty_ph, 0, 'no "Click to add text" placeholders left');
    assert.ok(info.titles[0].includes(`37${NBSP}%`), 'number and % kept together');
  });
  test('warns on dense slides and missing notes, rejects unknown layouts', () => {
    const dense = { slides: [{ layout: 'bullets', title: 'Забагато пунктів', bullets: ['1', '2', '3', '4', '5', '6', '7', '8'] }] };
    let r = py('make-pptx.py', [writeJson('dense.json', dense), join(tmp, 'dense.pptx')]);
    assert.equal(r.status, 0, r.stderr);
    const w = JSON.parse(r.stdout).warnings.join(' | ');
    assert.match(w, /8 bullets/);
    assert.match(w, /no speaker notes/);
    r = py('make-pptx.py', [writeJson('badlayout.json', { slides: [{ layout: 'hero', title: 'X' }] }), join(tmp, 'bad.pptx')]);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /unknown layout/);
  });
});

// Minimal hand-built PDFs (Latin text + one AcroForm text field) so the tests need no PDF library.
function buildPdf(objects) {
  let out = '%PDF-1.4\n';
  const offsets = [];
  objects.forEach((body, i) => { offsets.push(Buffer.byteLength(out, 'latin1')); out += `${i + 1} 0 obj\n${body}\nendobj\n`; });
  const xref = Buffer.byteLength(out, 'latin1');
  out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${offsets.map((o) => `${String(o).padStart(10, '0')} 00000 n \n`).join('')}`;
  out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(out, 'latin1');
}
const stream = 'BT /F1 18 Tf 72 720 Td (Hello PDF) Tj ET';
const font = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>';
const content = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`;

describe('pdf-tools', { skip: has('pypdf') ? false : 'pypdf not installed' }, () => {
  const textPdf = join(tmp, 'text.pdf');
  const formPdf = join(tmp, 'form.pdf');
  writeFileSync(textPdf, buildPdf(['<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>', font, content]));
  writeFileSync(formPdf, buildPdf(['<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [6 0 R] /DA (/Helv 0 Tf 0 g) /DR << /Font << /Helv 4 0 R >> >> >> >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R /Annots [6 0 R] >>',
    font, content, '<< /Type /Annot /Subtype /Widget /FT /Tx /T (client) /Rect [72 600 300 620] /P 3 0 R /F 4 /DA (/Helv 12 Tf 0 g) >>']));

  test('info, merge, split and text', () => {
    let r = py('pdf-tools.py', ['info', textPdf]);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(JSON.parse(r.stdout).pages, 1);
    const merged = join(tmp, 'merged.pdf');
    r = py('pdf-tools.py', ['merge', merged, textPdf, formPdf, textPdf]);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(JSON.parse(r.stdout).pages, 3);
    r = py('pdf-tools.py', ['split', merged, join(tmp, 'parts'), '--ranges', '1-2,3']);
    assert.equal(r.status, 0, r.stderr);
    assert.deepEqual(readdirSync(join(tmp, 'parts')).sort(), ['merged_p1-2.pdf', 'merged_p3.pdf']);
    r = py('pdf-tools.py', ['text', merged, '--pages', '3']);
    assert.match(r.stdout, /Hello PDF/);
    r = py('pdf-tools.py', ['split', merged, join(tmp, 'parts'), '--ranges', '2-9']);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /outside 1-3/);
  });
  test('lists and fills AcroForm fields with Cyrillic values', () => {
    let r = py('pdf-tools.py', ['fields', formPdf]);
    assert.equal(r.status, 0, r.stderr);
    assert.deepEqual(JSON.parse(r.stdout).map((f) => [f.name, f.type]), [['client', 'text']]);
    const filled = join(tmp, 'filled.pdf');
    r = py('pdf-tools.py', ['fill', formPdf, writeJson('values.json', { client: 'ТОВ «Приклад»' }), filled]);
    assert.equal(r.status, 0, r.stderr);
    r = py('pdf-tools.py', ['fields', filled]);
    assert.equal(JSON.parse(r.stdout)[0].value, 'ТОВ «Приклад»');
    r = py('pdf-tools.py', ['fill', formPdf, writeJson('bad-values.json', { nope: 1 }), join(tmp, 'x.pdf')]);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /unknown field names: nope/);
    r = py('pdf-tools.py', ['fill', textPdf, writeJson('v2.json', { client: 'x' }), join(tmp, 'y.pdf')]);
    assert.match(r.stderr, /no AcroForm fields/);
  });
  test('missing input file is a clear error', () => {
    const r = py('pdf-tools.py', ['info', join(tmp, 'absent.pdf')]);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /file not found/);
    assert.ok(!existsSync(join(tmp, 'absent.pdf')));
  });
});
