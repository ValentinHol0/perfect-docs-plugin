# Perfect Docs

Office files that look professional and calculate correctly: Word (DOCX), Excel (XLSX), PowerPoint (PPTX), PDF and HTML slide decks, plus Ukrainian business documents — договір про надання послуг / поставки, рахунок на оплату, акт наданих послуг (виконаних робіт), видаткова накладна, комерційна пропозиція, звіт. Totals, VAT and amounts in words come from tested scripts; required fields are tied to cited sources; an independent proofreader checks every document with money before it goes out.

Part of the **Perfect Suite**: the core `perfect-programming-plugin` (`/absolute`) builds sites, apps and programs; addons like this one cover a domain. Works on its own; with the core installed, technical work (document generators inside an app, CRM integrations) is handed to `/absolute`.

> Templates and checklists, not legal or tax advice. Legal and tax documents end with a verify-with-a-lawyer/accountant line.

## Use
`/office <what you need>` — or a shortcut: `/docx`, `/xlsx`, `/pptx`, `/pdf`. Examples: `/office акт № 27 за жовтень для ТОВ «Альфа», без ПДВ`, `/xlsx кошторис з ПДВ і графіком оплат`, `/pptx підсумки року на 10 слайдів з нотатками`, `/pdf об’єднай ці три файли`.

In **Claude Code**, when Anthropic’s document skills (`docx`, `xlsx`, `pptx`, `pdf`) are available, `/office` uses them for file mechanics and adds this plugin’s quality rules, Ukrainian templates and scripts. In **Antigravity** (no built-in document skills) the plugin’s own scripts do the work.

## Skills
| Skill | What it does |
|---|---|
| `office` (entry) | Engine choice, intake and defaults, routing, workflow, quality gates, output format, handoffs |
| `docx`, `xlsx`, `pptx`, `pdf` | Shortcut aliases that load `office` |
| `docs-docx` | Styles-based structure, numbering, tables, headers/footers, python-docx recipes, editing existing files; Ukrainian typography reference; ДСТУ 4163:2020 official-document profile with the status of every value |
| `docs-xlsx` | Inputs vs calculations, formula rules (rounding to kopiyky, remainder instalments), UAH/date formats, validation, charts, print setup, recalculation checks, CSV for Ukrainian Excel |
| `docs-pptx` | Storyline and claim titles, density limits, speaker notes, outline → PPTX, HTML decks (viewport fit, navigation, print-to-PDF), 12 Cyrillic-safe style presets with contrast values |
| `docs-pdf` | HTML/DOCX → PDF with Cyrillic, form filling, merge/split, text and table extraction, OCR, real redaction, preparing files for КЕП signing |
| `docs-templates` | Ukrainian business documents: requisites mapped to Law 996-XIV ст. 9, invoice/act/waybill JSON, contract skeletons, commercial proposal and report structures, `legal-basis.md` with sources and status |

Agent: `docs-proofreader` — read-only second pass: recomputes totals and VAT, compares the amount in words with the figures, checks required fields, citations, typography and formatting; returns PASS/FAIL with exact fixes.

## Scripts
| Script | Does | Needs |
|---|---|---|
| `scripts/uah-words.mjs` | Amount → Ukrainian words with correct gender and plural forms: `1234.56` → «одна тисяча двісті тридцять чотири гривні 56 копійок»; kopiyky as digits or words; exact parsing (rejects more than 2 decimals) | Node ≥ 18 |
| `scripts/make-docx.py` | Invoice, act or waybill DOCX from JSON: validates requisites and the IBAN checksum, Decimal totals and VAT (none / on top / included), amount in words, signatures | python-docx |
| `scripts/make-xlsx.py` | XLSX from JSON with live formulas (`[col]`, `[col:above]`, `{total}` tokens), defined names, validation, freeze, filter, chart, A4 print setup | openpyxl |
| `scripts/make-pptx.py` | 16:9 PPTX from an outline: 9 layouts on real placeholders, theme, notes, slide numbers, density / notes / alt-text warnings | python-pptx |
| `scripts/pdf-tools.py` | `info`, `merge`, `split`, `text`, `fields`, `fill`, `tables` | pypdf (+ pdfplumber for tables) |
| `scripts/html-to-pdf.mjs` | HTML document or slide deck → PDF through Playwright or a local Chrome / Edge / Chromium | a Chromium engine |
Python scripts print the exact `pip install …` line when a library is missing (exit code 3). Example inputs: `scripts/examples/` (act, invoice, waybill, workbook, deck). HTML deck template: `skills/docs-pptx/assets/deck-template.html`.

Sources: `skills/docs-templates/references/legal-basis.md` (checked 2026-11-12) — Закон № 996-XIV ст. 9, Положення № 88, ЦК (ст. 207, 638–642, 655, 691–692, 712, 901–907), loss of force of the Господарський кодекс (28.08.2025), ПКУ ст. 193, NBU IBAN format, КМУ № 55, Закон «Про стандартизацію» ст. 23; items left `[Unverified]` are marked there.

## Handoffs
- **Core (`/absolute`)** — anything that needs code: document generation inside an app or CRM, web calculators, sites. Brief: `.planning/handoff-docs.md`.
- **perfect-legal (`/legal`)** — contract wording, liability and penalties, contract review, site legal texts.
- **perfect-business (`/business`, `/fop`)** — ФОП tax group, VAT status, податкова накладна, ПРРО; it sends finished invoice/act content here for the file.
- **perfect-brand**, **perfect-translate**, **perfect-teach**, **perfect-research** — visuals, second language, lesson content, researched numbers.
Without a sibling installed, the addon writes a brief to `.planning/handoff-docs-to-<addon>.md` and names the addon to install.

## Install
- Claude Code: `/plugin marketplace add ValentinHol0/perfect-docs-plugin` → `/plugin install perfect-docs-plugin@perfect-docs-plugin`, or through the Perfect Suite hub: `/plugin marketplace add ValentinHol0/perfect-hub` → `/plugin install perfect-docs-plugin@perfect-suite`.
- Antigravity: `agy plugin install https://github.com/ValentinHol0/perfect-docs-plugin` (or a local folder path).
- Optional Python libraries for the generators: `pip install python-docx openpyxl python-pptx pypdf pdfplumber`.

## Develop
```bash
node scripts/check-plugin.mjs --external
node --test scripts/tests/docs.test.mjs
```
Tests cover the words converter (gender, plural and 11–14 cases, parsing errors), HTML → PDF (page count when a local Chromium exists, the no-engine message otherwise), and each Python script through `child_process` when its library is installed — plus the missing-library message path (`python -S`). `check-plugin.mjs`, `references/harness.md`, CI, `.gitattributes`, `.gitignore` are shared files synced from the core — don't edit them here.
