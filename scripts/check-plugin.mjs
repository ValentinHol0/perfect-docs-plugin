#!/usr/bin/env node
// check-plugin — cross-harness self-test for PPP (Claude Code + Antigravity). Zero dependencies.
// Usage: node scripts/check-plugin.mjs [pluginRoot] [--external]
//   --external also runs `claude plugin validate` and `agy plugin validate --strict` when those CLIs are found.
// Exit 1 on any error.

import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';

const ROOT = resolve(process.argv.slice(2).find((a) => !a.startsWith('--')) || join(dirname(fileURLToPath(import.meta.url)), '..'));
const EXTERNAL = process.argv.includes('--external');
const errors = [];
const warnings = [];
const err = (m) => errors.push(m);
const warn = (m) => warnings.push(m);
const read = (p) => readFileSync(join(ROOT, p), 'utf8');
const exists = (p) => existsSync(join(ROOT, p));

// Minimal frontmatter parser: scalars, quoted scalars, block lists, booleans.
export function frontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!m) return null;
  const data = {};
  let listKey = null;
  for (const line of m[1].split(/\r?\n/)) {
    if (!line.trim() || line.trim().startsWith('#')) continue;
    const item = line.match(/^\s+-\s+(.*)$/);
    if (item && listKey) { data[listKey].push(item[1].trim()); continue; }
    const kv = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/);
    if (!kv) { err(`unparseable frontmatter line: "${line}"`); continue; }
    let v = kv[2].trim();
    if (v === '') { data[kv[1]] = []; listKey = kv[1]; continue; }
    listKey = null;
    if (/^".*"$|^'.*'$/.test(v)) v = v.slice(1, -1);
    else if (v === 'true' || v === 'false') v = v === 'true';
    else if (/:\s/.test(v)) err(`unquoted ": " in value of "${kv[1]}" (YAML will reject it)`);
    data[kv[1]] = v;
  }
  return { data, body: text.slice(m[0].length) };
}

// 1. Manifests
let claude, ag;
try { claude = JSON.parse(read('.claude-plugin/plugin.json')); } catch (e) { err(`.claude-plugin/plugin.json: ${e.message}`); }
try { ag = JSON.parse(read('.antigravity-plugin/plugin.json')); } catch (e) { err(`.antigravity-plugin/plugin.json: ${e.message}`); }
if (claude && ag) {
  if (claude.name !== ag.name) err(`manifest names differ: ${claude.name} vs ${ag.name}`);
  if (claude.version !== ag.version) err(`manifest versions differ: ${claude.version} vs ${ag.version}`);
  if (exists('.claude-plugin/marketplace.json')) {
    try {
      const entry = (JSON.parse(read('.claude-plugin/marketplace.json')).plugins || []).find((p) => p.name === claude.name);
      if (entry && entry.version && entry.version !== claude.version) err(`marketplace.json lists ${entry.version}, plugin.json is ${claude.version}`);
    } catch (e) { err(`.claude-plugin/marketplace.json: ${e.message}`); }
  }
  const agAllowed = new Set(['$schema', 'name', 'displayName', 'display_name', 'description', 'version', 'disabled', 'logo', 'suggestedPrompts', 'suggested_prompts', 'skills', 'author', 'homepage', 'repository', 'license', 'keywords', 'extensions']);
  for (const k of Object.keys(ag)) if (!agAllowed.has(k)) err(`.antigravity-plugin/plugin.json: field "${k}" is not in the Antigravity schema`);
  if ((ag.suggestedPrompts || []).length > 3) err('Antigravity allows at most 3 suggestedPrompts');
  if ('slashCommands' in claude) warn('.claude-plugin/plugin.json: slashCommands is ignored by Claude Code');
  for (const group of Object.values(claude.hooks || {})) {
    for (const h of group.flatMap((g) => g.hooks || [])) {
      const script = (h.command || '').match(/\$\{CLAUDE_PLUGIN_ROOT\}\/([^"\s]+)/);
      if (script && !exists(script[1])) err(`hook command points to missing ${script[1]}`);
    }
  }
}
if (exists('commands')) warn('commands/ is never loaded by Antigravity — use alias skills with disable-model-invocation');
if (exists('hooks/hooks.json')) warn('hooks/hooks.json is reported as never loaded by Antigravity — inline hooks in .claude-plugin/plugin.json');
if (!exists('rules/AGENTS.md')) err('rules/AGENTS.md (Antigravity always-on bootstrap) missing');
else if (statSync(join(ROOT, 'rules/AGENTS.md')).size > 6000) warn('rules/AGENTS.md is loaded in every Antigravity session — keep it under 6 KB');

// 2. Skills
if (!exists('skills')) err('skills/ folder missing');
const skillNames = new Set(exists('skills') ? readdirSync(join(ROOT, 'skills')).filter((d) => exists(`skills/${d}/SKILL.md`)) : []);
for (const dir of skillNames) {
  const rel = `skills/${dir}/SKILL.md`;
  const text = read(rel);
  const fm = frontmatter(text);
  if (!fm) { err(`${rel}: no frontmatter`); continue; }
  const { data, body } = fm;
  if (data.name !== dir) err(`${rel}: name "${data.name}" must equal folder "${dir}"`);
  if (!data.description) err(`${rel}: description missing`);
  else {
    if (data.description.length > 1024) err(`${rel}: description ${data.description.length} chars (max 1024)`);
    if (/[<>]/.test(data.description)) err(`${rel}: description contains < or >`);
  }
  const bytes = Buffer.byteLength(body, 'utf8');
  if (bytes > 24000) err(`${rel}: body ${bytes} bytes — Antigravity loads only the first 24000`);
  else if (bytes > 20000) warn(`${rel}: body ${bytes} bytes — close to Antigravity's 24000 limit`);
  if (data['disable-model-invocation'] === true) {
    const target = body.match(/`([a-z0-9-]+)` (skill|subagent)/);
    if (target && target[2] === 'skill' && !skillNames.has(target[1])) err(`${rel}: alias target "${target[1]}" does not exist`);
  }
  for (const m of text.matchAll(/\$\{CLAUDE_SKILL_DIR\}\/([\w./-]+)/g)) {
    const p = `skills/${dir}/${m[1].replace(/[.,)]+$/, '')}`;
    if (!exists(p)) err(`${rel}: references missing ${p}`);
  }
}

// 3. All markdown: plugin-root references must exist
function walk(d, out = []) {
  for (const n of readdirSync(join(ROOT, d))) {
    if (n === 'node_modules' || n === '.git') continue;
    const p = d ? `${d}/${n}` : n;
    if (statSync(join(ROOT, p)).isDirectory()) walk(p, out);
    else if (p.endsWith('.md')) out.push(p);
  }
  return out;
}
for (const rel of walk('')) {
  const text = read(rel);
  for (const m of text.matchAll(/(?:\$\{CLAUDE_PLUGIN_ROOT\}|<PLUGIN_ROOT>)\/([\w./-]+)/g)) {
    const p = m[1].replace(/[.,)]+$/, '');
    if (!exists(p)) err(`${rel}: references missing ${p}`);
  }
}

// 4. Agents: frontmatter valid in BOTH harnesses
const AG_MODELS = new Set(['inherit', 'flash_lite', 'flash', 'pro']);
for (const f of (exists('agents') ? readdirSync(join(ROOT, 'agents')) : []).filter((n) => n.endsWith('.md'))) {
  const rel = `agents/${f}`;
  const fm = frontmatter(read(rel));
  if (!fm) { err(`${rel}: no frontmatter`); continue; }
  const { data } = fm;
  if (data.name !== f.replace(/\.md$/, '')) err(`${rel}: name must equal file name`);
  if (!data.description) err(`${rel}: description missing`);
  if ('tools' in data) err(`${rel}: "tools" breaks one harness (Claude and Antigravity use different tool names) — omit it; restrict with disallowedTools (Claude) and prose`);
  if (data.model && !AG_MODELS.has(data.model)) err(`${rel}: model "${data.model}" is invalid in Antigravity — use inherit and choose tiers at dispatch`);
  if (data.disallowedTools && !Array.isArray(data.disallowedTools)) err(`${rel}: disallowedTools must be a YAML list`);
}

// 5. Installed copies older than this source (Antigravity global install)
if (ag) {
  const agInstalled = [join(homedir(), '.gemini', 'config', 'plugins', ag.name, '.antigravity-plugin', 'plugin.json'), join(homedir(), '.gemini', 'config', 'plugins', ag.name, 'plugin.json')].find((p) => existsSync(p));
  if (agInstalled) {
    try {
      const v = JSON.parse(readFileSync(agInstalled, 'utf8')).version;
      if (v !== ag.version) warn(`Antigravity has ${ag.name} ${v} installed; this source is ${ag.version} — reinstall with: agy plugin install "${ROOT}"`);
    } catch { /* unreadable install manifest — ignore */ }
  }
}

// 6. Optional external validators
if (EXTERNAL) {
  const tryRun = (label, cmd, args) => {
    const r = spawnSync(cmd, args, { encoding: 'utf8', timeout: 120000 });
    if (r.error) { warn(`${label}: not run (${r.error.code || r.error.message})`); return; }
    const out = `${r.stdout}\n${r.stderr}`;
    if (r.status !== 0) err(`${label} failed:\n${out.trim()}`);
    else console.log(`${label}: OK`);
  };
  tryRun('claude plugin validate', process.env.CLAUDE_CODE_EXECPATH || 'claude', ['plugin', 'validate', ROOT]);
  const agy = [join(homedir(), '.gemini', 'bin', process.platform === 'win32' ? 'agy.exe' : 'agy'), 'agy'].find((p) => p === 'agy' || existsSync(p));
  tryRun('agy plugin validate --strict', agy, ['plugin', 'validate', ROOT, '--strict']);
}

for (const w of warnings) console.log(`WARN  ${w}`);
for (const e of errors) console.log(`ERROR ${e}`);
console.log(`check-plugin: ${skillNames.size} skills · ${errors.length} errors · ${warnings.length} warnings`);
process.exit(errors.length ? 1 : 0);
