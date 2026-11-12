#!/usr/bin/env node
// html-to-pdf — print a local HTML file (document or slide deck) to PDF with a Chromium engine. Zero npm dependencies.
// Engines, in order: Playwright (if `playwright` resolves from the working directory or this folder)
//                    → an installed Chrome / Edge / Chromium in headless mode (--print-to-pdf).
// Usage: node html-to-pdf.mjs <in.html> <out.pdf> [--engine auto|playwright|browser] [--browser <path>] [--wait <ms>]
// Page size and margins come from the page's own CSS, so put them there:
//   A4 document: @page { size: A4; margin: 20mm 10mm 20mm 30mm }
//   16:9 deck:   @page { size: 1920px 1080px; margin: 0 }  and every .slide { break-after: page }
//   colours:     html { print-color-adjust: exact; -webkit-print-color-adjust: exact }
// Exit codes: 0 ok · 1 conversion failed · 2 usage · 3 no engine available (message says what to install).

import { existsSync, mkdtempSync, rmSync, statSync } from 'node:fs';
import { resolve, join, delimiter, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';

const INSTALL_HINT = [
  'No Chromium engine found. Any one of these fixes it:',
  '  - npm i -D playwright && npx playwright install chromium',
  '  - install Google Chrome, Microsoft Edge or Chromium',
  '  - pass --browser <path-to-chrome-or-edge> (or set CHROME_PATH)',
].join('\n');

function fail(code, msg) {
  console.error(`html-to-pdf: ${msg}`);
  process.exit(code);
}

function resolvePlaywright() {
  for (const base of [join(process.cwd(), 'noop.js'), fileURLToPath(import.meta.url)]) {
    try { return createRequire(base).resolve('playwright'); } catch { /* not installed here */ }
  }
  return null;
}

export function findBrowser(env = process.env, platform = process.platform) {
  if (env.CHROME_PATH) return existsSync(env.CHROME_PATH) ? env.CHROME_PATH : null;
  const candidates = [];
  if (platform === 'win32') {
    for (const root of [env.ProgramFiles, env['ProgramFiles(x86)'], env.LOCALAPPDATA].filter(Boolean)) {
      candidates.push(join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'), join(root, 'Microsoft', 'Edge', 'Application', 'msedge.exe'), join(root, 'Chromium', 'Application', 'chrome.exe'));
    }
  } else if (platform === 'darwin') {
    candidates.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Chromium.app/Contents/MacOS/Chromium');
  } else {
    for (const dir of (env.PATH || '').split(delimiter).filter(Boolean)) {
      for (const name of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge']) candidates.push(join(dir, name));
    }
  }
  return candidates.find((p) => existsSync(p)) || null;
}

async function viaPlaywright(modPath, input, output, waitMs) {
  const mod = await import(pathToFileURL(modPath).href);
  const chromium = mod.chromium || mod.default?.chromium;
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(input).href, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    if (waitMs) await page.waitForTimeout(waitMs);
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: output, preferCSSPageSize: true, printBackground: true });
  } finally {
    await browser.close();
  }
}

function printOnce(exe, input, output, waitMs, extra) {
  const profile = mkdtempSync(join(tmpdir(), 'html-to-pdf-'));
  try {
    const r = spawnSync(exe, [
      '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-extensions', ...extra,
      `--user-data-dir=${profile}`, '--no-pdf-header-footer', '--print-to-pdf-no-header',
      `--virtual-time-budget=${waitMs || 5000}`, `--print-to-pdf=${output}`, pathToFileURL(input).href,
    ], { encoding: 'utf8', timeout: 120000 });
    if (r.error) throw r.error;
    if (!existsSync(output) || statSync(output).size === 0) throw new Error(`browser exited ${r.status} without writing the PDF\n${(r.stderr || '').trim().slice(0, 800)}`);
  } finally {
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* the browser may still hold a lock on Windows */ }
  }
}

function viaBrowser(exe, input, output, waitMs) {
  try {
    printOnce(exe, input, output, waitMs, []);
  } catch (e) {
    // Linux containers and CI runners often cannot start Chromium's sandbox; the input is a local file the user chose.
    if (process.platform !== 'linux') throw e;
    console.error('html-to-pdf: retrying without the Chromium sandbox (sandbox could not start here)');
    printOnce(exe, input, output, waitMs, ['--no-sandbox']);
  }
}

async function main(argv) {
  const value = (name, def) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : def; };
  const valued = new Set(['--engine', '--browser', '--wait']);
  const pos = argv.filter((a, i) => !a.startsWith('--') && !valued.has(argv[i - 1]));
  if (argv.includes('--help') || pos.length !== 2) {
    console.log('Usage: node html-to-pdf.mjs <in.html> <out.pdf> [--engine auto|playwright|browser] [--browser <path>] [--wait <ms>]');
    process.exit(argv.includes('--help') ? 0 : 2);
  }
  const input = resolve(pos[0]);
  const output = resolve(pos[1]);
  const engine = value('--engine', 'auto');
  const waitMs = Number(value('--wait', '0')) || 0;
  if (!['auto', 'playwright', 'browser'].includes(engine)) fail(2, `unknown engine "${engine}"`);
  if (!existsSync(input)) fail(2, `input not found: ${input}`);
  if (!existsSync(dirname(output))) fail(2, `output folder does not exist: ${dirname(output)}`);

  const pw = engine === 'browser' ? null : resolvePlaywright();
  if (pw) {
    await viaPlaywright(pw, input, output, waitMs);
    console.log(JSON.stringify({ engine: 'playwright', output }));
    return;
  }
  if (engine === 'playwright') fail(3, `Playwright is not installed here.\n${INSTALL_HINT}`);
  const explicit = value('--browser');
  const exe = explicit ? (existsSync(explicit) ? explicit : null) : findBrowser();
  if (!exe) fail(3, explicit ? `browser not found at ${explicit}\n${INSTALL_HINT}` : INSTALL_HINT);
  viaBrowser(exe, input, output, waitMs);
  console.log(JSON.stringify({ engine: 'browser', browser: exe, output }));
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) main(process.argv.slice(2)).catch((e) => fail(1, e.message));
