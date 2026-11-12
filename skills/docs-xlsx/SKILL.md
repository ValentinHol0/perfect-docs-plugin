---
name: docs-xlsx
description: "Excel (XLSX) rules of perfect-docs — live formulas instead of pasted values, separated inputs and calculations, UAH and date formats, rounding to kopiyky, data validation drop-downs, charts, frozen headers, filters and A4 print setup, plus recalculation checks. Use when building, fixing or checking a spreadsheet, budget, price list, estimate, payment schedule or report table, or when /office or /xlsx routes here."
---

# Docs XLSX — spreadsheets that keep calculating

> **Harness:** written with Claude Code tool names. In Antigravity, translate with `${CLAUDE_PLUGIN_ROOT}/references/harness.md`.

A spreadsheet is a model: when an input changes, every dependent number must change. A pasted result is a bug waiting for the next edit.

## 1. Engine
- **Claude Code with Anthropic’s `xlsx` skill listed** (not `perfect-docs-plugin:xlsx`, the shortcut back to `/office`): use it for reading messy files, editing existing workbooks and its recalculation tooling; apply this skill’s rules to the result.
- **New workbook from data** (any harness): `python "${CLAUDE_PLUGIN_ROOT}/scripts/make-xlsx.py" spec.json out.xlsx` — formulas, names, validation, freeze, filter, chart, print setup in one pass (§8).
- **Edits by hand**: openpyxl (`pip install openpyxl` if missing — ask first). Load with `openpyxl.load_workbook(path)` to keep formulas; `data_only=True` only to read cached results, and never save that object over the original (formulas would be lost).

## 2. Model layout
1. **Inputs** (rates, prices, VAT rate, exchange rate, dates) in one labelled block or an «Вхідні дані» sheet, visibly marked (light-yellow fill), each a defined name (`vat_rate`, `usd_rate`). Formulas reference names, not `$B$3`.
2. **Calculations** in tables: one header row, one record per row, no blank rows or columns inside, no merged cells in data ranges, one data type per column.
3. **Outputs** (totals, KPIs, charts) reference calculations; a summary sheet never re-types numbers.
4. Units in headers («Сума, грн», «Вага, кг»), never inside cells as text («15 000 грн» in a cell is text, not a number).
5. Sheet names short, no special characters: «Кошторис», «Графік оплат», «Вхідні дані».

## 3. Formula rules
- Every derived number is a formula. Constants inside formulas only when they are definitions (`/100`, `*12` months) — business numbers (rates, prices) are inputs.
- Money: round at the line where the document rounds: `=ROUND(D6*E6,2)`; totals sum rounded lines. VAT: `=ROUND(total*vat_rate,2)` on top, or `=ROUND(total*vat_rate/(1+vat_rate),2)` when included — the same rules as `make-docx.py`, so the spreadsheet and the invoice agree to the kopiyka.
- Splitting a total into instalments or shares: every part `=ROUND(share*total,2)` except the last, which is `=total-SUM(previous parts)` — otherwise parts miss the total by a kopiyka (seen in testing: 2 × 16 407,34 ≠ 32 814,67).
- Totals: `SUM` over the data range; with filters use `SUBTOTAL(109, range)` so hidden rows drop out.
- Lookups: `INDEX/MATCH` (or `XLOOKUP` when everyone has Excel 2021/365); exact match always.
- Avoid volatile functions in models (`INDIRECT`, `OFFSET`, `TODAY`, `NOW`, `RAND`); put today’s date in an input cell.
- `IFERROR` only around an expected, explained error (division by an empty plan), never to hide `#REF!`.
- Formulas are stored in English with comma separators (`=ROUND(A1,2)`); Excel shows them in the user’s locale. Never write `;` separators or localised function names into the file.

## 4. Formats (Ukrainian defaults)
| Data | Number format code | Shows as (uk-UA) |
|---|---|---|
| Money in a column titled «…, грн» | `#,##0.00;[Red]-#,##0.00` | 15 000,00 |
| Money with unit in the cell | `#,##0.00\ "грн";[Red]-#,##0.00\ "грн"` | 15 000,00 грн |
| Integer counts | `#,##0` | 1 250 |
| Percent | `0.0%` | 20,0% |
| Date | `DD.MM.YYYY` | 12.11.2026 |
| Text codes (ЄДРПОУ, IBAN, phone, article numbers) | `@` (text) | 00123456 keeps leading zeros |
The thousands and decimal separators come from the viewer’s regional settings; the format code is always written with `,` and `.`. Codes such as ЄДРПОУ, РНОКПП, IBAN and barcodes are text, never numbers (Excel drops leading zeros and rounds long numbers past 15 digits).

## 5. Data entry quality
- **Validation** on every input column: drop-down lists for categories and units, `≥ 0` for quantities and prices, date ranges for dates; Ukrainian error message («Оберіть значення зі списку»). Lists longer than ~250 characters or containing commas live on a hidden `_lists` sheet.
- **Freeze panes** below the header row (and the first column for wide tables); **autofilter** on the header.
- Column widths set to content; wrap text in long text columns; numbers never wrapped.
- Conditional formatting sparingly: negative margin red, overdue dates — one rule per meaning.
- Protection only on request (lock formula cells, leave inputs unlocked); never a password the user did not choose.

## 6. Charts
| Message | Chart |
|---|---|
| Compare categories | column (bar if names are long or more than ~7 items) |
| Change over time | line (column for ≤ 6 periods) |
| Share of a whole, ≤ 5 parts | pie or 100 % stacked bar |
| Plan vs actual | clustered column or bullet-style bar |
Rules: title states the message with the unit («Виручка за кварталами, млн грн»); value axis from zero for columns and bars; one colour per series, no 3D, no shadow; data labels or gridlines, rarely both; source under the chart in reports. Place charts below the table or on their own sheet so print scaling does not shrink the table. Charts need a full data visualisation pass → also follow the `dataviz` guidance if the harness offers it.

## 7. Print and export
A4; orientation by width (landscape above ~7 columns); fit to 1 page wide, any number of pages tall; repeat the header row on every page; footer «Сторінка &P з &N» and the file name; margins ≈ 1.3–1.5 cm; print area set when the sheet has helper columns; gridlines off for reports. PDF export: Excel/LibreOffice «Export as PDF» or `soffice --headless --convert-to pdf`.

## 8. `make-xlsx.py` spec (shape)
```json
{ "sheets": [ {
  "name": "Кошторис", "title": "Кошторис робіт — листопад 2026",
  "inputs":  [ { "name": "vat_rate", "label": "Ставка ПДВ", "value": 0.2, "type": "percent" } ],
  "columns": [
    { "key": "name",  "header": "Найменування", "type": "text", "width": 40 },
    { "key": "unit",  "header": "Од.", "type": "text", "validation": ["год", "шт", "послуга"] },
    { "key": "qty",   "header": "Кількість", "type": "number", "validation": { "min": 0 } },
    { "key": "price", "header": "Ціна, грн", "type": "money" },
    { "key": "sum",   "header": "Сума, грн", "type": "money", "formula": "=ROUND([qty]*[price],2)" } ],
  "rows":    [ { "name": "Верстка", "unit": "год", "qty": 12.5, "price": 800 } ],
  "totals":  { "label": "Разом", "sum": "SUM" },
  "summary": [ { "key": "vat", "label": "ПДВ", "formula": "=ROUND({sum}*vat_rate,2)", "type": "money" },
               { "key": "grand", "label": "Усього", "formula": "={sum}+{vat}", "type": "money", "define": "grand_total" } ],
  "chart":   { "type": "bar", "title": "Вартість за статтями, грн", "categories": "name", "values": ["sum"] },
  "print":   { "orientation": "portrait" } } ] }
```
Tokens: `[key]` same-row cell; `[key:above]` that column from the first data row to the row above; `{key}` a total or summary cell; input names and `define` names are workbook-wide. A row may override its column formula: `"formulas": {"amount": "=grand_total-SUM([amount:above])"}`. Types: text, int, number, money, uah, percent, date. Full example: `${CLAUDE_PLUGIN_ROOT}/scripts/examples/workbook.json`.

## 9. Verify before delivery
openpyxl writes formulas without cached results; the script sets «calculate on open». Before you quote any number from the file, get it computed:
- Excel on Windows: PowerShell `New-Object -ComObject Excel.Application` → `Workbooks.Open(path)` → `CalculateFull()` → read `.Range("F11").Text`.
- LibreOffice: `soffice --headless --convert-to xlsx --outdir recalculated book.xlsx`, then `openpyxl.load_workbook(..., data_only=True)` and read values. If values come back empty, the conversion did not recalculate — open the file in Excel/LibreOffice instead and say so.
- Scan every sheet for `#REF!`, `#NAME?`, `#VALUE!`, `#DIV/0!`, `#N/A`; any hit blocks delivery.
- Cross-check one total by hand or with the JSON summary (totals in an invoice DOCX must equal the spreadsheet).

## 10. CSV for Ukrainian Excel users
Excel with Ukrainian regional settings expects `;` as the CSV delimiter (comma is the decimal separator) and needs a UTF-8 BOM to show Cyrillic correctly. Write `encoding="utf-8-sig"`, `delimiter=";"`, dates `DD.MM.YYYY`. For systems that import CSV (1C/BAS, M.E.Doc, marketplaces), follow their import spec instead.

## 11. Checklist
- [ ] Inputs separated, named, highlighted; no business constants inside formulas.
- [ ] Every derived cell is a formula; totals reconcile; instalments end with a remainder formula.
- [ ] Money rounded with `ROUND(…,2)` where documents round.
- [ ] Formats: money, dates, percents, text codes as text.
- [ ] Validation on inputs; header frozen; filter on.
- [ ] Chart titles carry the message and unit; axis from zero.
- [ ] A4 print setup, header row repeated, page numbers.
- [ ] Recalculated once; no error values; numbers quoted from computed results.
