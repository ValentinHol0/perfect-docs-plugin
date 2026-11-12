#!/usr/bin/env python3
"""make-xlsx — a working XLSX from JSON: live formulas (never pasted results), UAH number formats, named inputs,
data validation, frozen header, autofilter, a chart and A4 print setup.

Requires: openpyxl  ->  pip install openpyxl
Usage:    python make-xlsx.py <spec.json> <out.xlsx>
Output:   the XLSX + a JSON summary on stdout (sheets, rows, formulas written, defined names).
Exit:     0 ok · 1 invalid spec · 2 usage · 3 missing dependency.

Formula tokens (inside any "formula" string):
  [key]        the cell of column `key` in the same row            "=[qty]*[price]"
  [key:above]  that column from the first data row to the row above   "=grand_total-SUM([amount:above])"
  {key}        the single cell named `key`: a column total or a summary row     "=ROUND({sum}*vat_rate,2)"
A row may override its column formula: {"stage": "Остаточний", "formulas": {"amount": "=grand_total-SUM([amount:above])"}}
  names   inputs, and summary rows with "define", become workbook-level defined names   vat_rate, grand_total
Column types: text, int, number, money (#,##0.00), uah (#,##0.00 "грн"), percent, date (DD.MM.YYYY).
Spec shape and an example: skills/docs-xlsx/SKILL.md, scripts/examples/workbook.json
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

try:
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter, quote_sheetname
    from openpyxl.workbook.defined_name import DefinedName
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:
    sys.stderr.write("make-xlsx: missing Python library openpyxl.\nInstall it with:  pip install openpyxl\n")
    sys.exit(3)

FORMATS = {
    "text": "@",
    "int": "#,##0",
    "number": "#,##0.00",
    "money": "#,##0.00;[Red]-#,##0.00",
    "uah": '#,##0.00\\ "грн";[Red]-#,##0.00\\ "грн"',
    "percent": "0.0%",
    "date": "DD.MM.YYYY",
}
THIN = Side(style="thin", color="A6A6A6")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="E7E6E6")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")  # inputs are visibly different from calculations
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
AGGREGATES = {"SUM": "SUM", "AVERAGE": "AVERAGE", "MIN": "MIN", "MAX": "MAX", "COUNT": "COUNT"}


class SpecError(Exception):
    pass


def resolve(formula, row_cols, row, cells, where, first=None):
    def col_ref(m):
        key, above = m.group(1), m.group(2)
        if key not in row_cols:
            raise SpecError(f"{where}: unknown column [{key}]")
        if row is None:
            raise SpecError(f"{where}: [{key}] needs a table row — use {{{key}}} for a total")
        if above:
            if first is None or row <= first:
                raise SpecError(f"{where}: [{key}:above] has no rows above it")
            return f"{row_cols[key]}{first}:{row_cols[key]}{row - 1}"
        return f"{row_cols[key]}{row}"

    def cell_ref(m):
        key = m.group(1)
        if key not in cells:
            raise SpecError(f"{where}: unknown cell {{{key}}} (define a column total or a summary row with that key first)")
        return cells[key]

    out = re.sub(r"\[([A-Za-z_][A-Za-z0-9_]*)(:above)?\]", col_ref, formula)
    out = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", cell_ref, out)
    if not out.startswith("="):
        raise SpecError(f"{where}: a formula must start with '='")
    return out


def convert(value, ctype, where):
    if value is None or value == "":
        return None
    if ctype == "date":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
            raise SpecError(f"{where}: date must be YYYY-MM-DD, got {value!r}")
        return date.fromisoformat(str(value))
    if ctype in ("int", "number", "money", "uah", "percent"):
        if isinstance(value, str) and value.startswith("="):
            raise SpecError(f"{where}: put formulas in the column's \"formula\", not in row data")
        try:
            num = float(str(value).replace(" ", "").replace("\u00a0", "").replace(",", "."))
        except ValueError:
            raise SpecError(f"{where}: not a number: {value!r}")
        return int(num) if ctype == "int" and num.is_integer() else num
    return str(value)


def add_name(wb, name, ref, names_seen, stats):
    if not NAME_RE.match(name or "") or re.fullmatch(r"[A-Za-z]{1,3}\d+", name):
        raise SpecError(f"name {name!r} must be an ASCII letter/underscore identifier that is not a cell address")
    if name in names_seen:
        raise SpecError(f"name {name!r} is defined twice")
    names_seen.add(name)
    wb.defined_names[name] = DefinedName(name, attr_text=ref)
    stats["names"].append(name)


def build_sheet(wb, spec, names_seen, stats):
    ws = wb.create_sheet(spec.get("name", f"Sheet{len(wb.worksheets) + 1}")[:31])
    title_q = quote_sheetname(ws.title)
    r = 1
    if spec.get("title"):
        ws.cell(r, 1, spec["title"]).font = Font(bold=True, size=14)
        r += 2

    columns = spec.get("columns") or []
    if not columns:
        raise SpecError(f"sheet {ws.title}: columns are required")
    col_widths = [c.get("width", max(10, min(45, len(str(c.get("header", c.get("key", "")))) + 4))) for c in columns]

    # inputs (assumptions) block: label (merged across narrow columns) | value, each value a defined name
    span = 1
    while span < len(columns) - 1 and sum(col_widths[:span]) < 18:
        span += 1
    for inp in spec.get("inputs") or []:
        name = inp.get("name", "")
        vcol = span + 1
        add_name(wb, name, f"{title_q}!${get_column_letter(vcol)}${r}", names_seen, stats)
        ws.cell(r, 1, inp.get("label", name)).font = Font(bold=True)
        if span > 1:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=span)
        c = ws.cell(r, vcol, convert(inp.get("value"), inp.get("type", "number"), f"input {name}"))
        c.number_format = FORMATS.get(inp.get("type", "number"), FORMATS["number"])
        c.fill, c.border = INPUT_FILL, BOX
        if inp.get("note"):
            ws.cell(r, vcol + 1, inp["note"]).font = Font(italic=True, color="7F7F7F")
        r += 1
    if spec.get("inputs"):
        r += 1
    keys = [c.get("key") for c in columns]
    if len(set(keys)) != len(keys) or not all(k and NAME_RE.match(k) for k in keys):
        raise SpecError(f"sheet {ws.title}: every column needs a unique identifier key")
    row_cols = {c["key"]: get_column_letter(i) for i, c in enumerate(columns, 1)}

    header_row = r
    for i, col in enumerate(columns, 1):
        c = ws.cell(header_row, i, col.get("header", col["key"]))
        c.font, c.fill, c.border = Font(bold=True), HEAD_FILL, BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = col_widths[i - 1]
    rows = spec.get("rows") or []
    first = header_row + 1
    last = header_row + len(rows)
    for ri, data in enumerate(rows):
        rr = first + ri
        for ci, col in enumerate(columns, 1):
            ctype = col.get("type", "text")
            where = f"sheet {ws.title} row {ri + 1} column {col['key']}"
            row_formula = (data.get("formulas") or {}).get(col["key"])
            if row_formula or col.get("formula"):
                value = resolve(row_formula or col["formula"], row_cols, rr, {}, where, first)
                stats["formulas"] += 1
            else:
                value = convert(data.get(col["key"]), ctype, where)
            c = ws.cell(rr, ci, value)
            c.number_format = FORMATS.get(ctype, "General")
            c.border = BOX
            if ctype == "text":
                c.alignment = Alignment(wrap_text=True, vertical="top")
    stats["rows"] += len(rows)

    cells = {}
    r = last + 1
    totals = spec.get("totals") or {}
    if totals and rows:
        first_total = min(keys.index(k) + 1 for k in totals if k in keys)
        label_col = max(1, first_total - 1)
        ws.cell(r, label_col, totals.get("label", "Разом")).font = Font(bold=True)
        for ci, col in enumerate(columns, 1):
            agg = totals.get(col["key"])
            if not agg:
                continue
            letter = row_cols[col["key"]]
            rng = f"{letter}{first}:{letter}{last}"
            if agg.upper() == "SUBTOTAL":
                formula = f"=SUBTOTAL(109,{rng})"  # ignores rows hidden by the filter
            elif agg.upper() in AGGREGATES:
                formula = f"={AGGREGATES[agg.upper()]}({rng})"
            else:
                raise SpecError(f"sheet {ws.title}: unknown total {agg!r} for {col['key']}")
            c = ws.cell(r, ci, formula)
            c.font, c.border = Font(bold=True), Border(top=Side(style="medium"))
            c.number_format = FORMATS.get(col.get("type", "number"), "General")
            cells[col["key"]] = f"${letter}${r}"
            stats["formulas"] += 1
        r += 1

    value_col = len(columns)
    for srow in spec.get("summary") or []:
        key = srow.get("key")
        if not key or not NAME_RE.match(key) or key in cells:
            raise SpecError(f"sheet {ws.title}: summary rows need a unique identifier key")
        ws.cell(r, max(1, value_col - 1), srow.get("label", key)).font = Font(bold=bool(srow.get("bold")))
        ws.cell(r, max(1, value_col - 1)).alignment = Alignment(horizontal="right")
        c = ws.cell(r, value_col, resolve(srow["formula"], row_cols, None, cells, f"summary {key}"))
        c.number_format = FORMATS.get(srow.get("type", "number"), "General")
        c.font = Font(bold=bool(srow.get("bold")))
        cells[key] = f"${get_column_letter(value_col)}${r}"
        stats["formulas"] += 1
        if srow.get("define"):  # expose the result to other sheets as a defined name
            add_name(wb, srow["define"], f"{title_q}!{cells[key]}", names_seen, stats)
        r += 1

    # data validation on input columns
    for ci, col in enumerate(columns, 1):
        rule = col.get("validation")
        if not rule or not rows:
            continue
        letter = row_cols[col["key"]]
        rng = f"{letter}{first}:{letter}{last + int(spec.get('spare_rows', 0))}"
        if isinstance(rule, list) or "list" in rule:
            values = rule if isinstance(rule, list) else rule["list"]
            joined = ",".join(str(v) for v in values)
            if len(joined) > 250 or any("," in str(v) for v in values):
                lists = wb["_lists"] if "_lists" in wb.sheetnames else wb.create_sheet("_lists")
                lists.sheet_state = "hidden"
                stats["list_columns"] = lc = stats.get("list_columns", 0) + 1
                for vi, v in enumerate(values, 1):
                    lists.cell(vi, lc, v)
                lcol = get_column_letter(lc)
                dv = DataValidation(type="list", formula1=f"_lists!${lcol}$1:${lcol}${len(values)}", allow_blank=True)
            else:
                dv = DataValidation(type="list", formula1=f'"{joined}"', allow_blank=True)
            dv.error, dv.errorTitle = "Оберіть значення зі списку", "Недопустиме значення"
        else:
            kind = "whole" if rule.get("whole") else "decimal"
            lo, hi = rule.get("min"), rule.get("max")
            if lo is not None and hi is not None:
                dv = DataValidation(type=kind, operator="between", formula1=str(lo), formula2=str(hi))
            elif lo is not None:
                dv = DataValidation(type=kind, operator="greaterThanOrEqual", formula1=str(lo))
            elif hi is not None:
                dv = DataValidation(type=kind, operator="lessThanOrEqual", formula1=str(hi))
            else:
                raise SpecError(f"sheet {ws.title}: validation for {col['key']} needs list, min or max")
            dv.error, dv.errorTitle = "Значення поза допустимим діапазоном", "Недопустиме значення"
        dv.showErrorMessage = True
        ws.add_data_validation(dv)
        dv.add(rng)
        stats["validations"] += 1

    if spec.get("freeze", True):
        ws.freeze_panes = ws.cell(header_row + 1, 1 + int(spec.get("freeze_cols", 0)))
    if spec.get("autofilter", True) and rows:
        ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(columns))}{last}"

    chart_spec = spec.get("chart")
    if chart_spec and rows:
        kind = chart_spec.get("type", "bar")
        chart = {"bar": BarChart, "line": LineChart, "pie": PieChart}.get(kind)
        if not chart:
            raise SpecError(f"sheet {ws.title}: chart type must be bar, line or pie")
        ch = chart()
        ch.title = chart_spec.get("title")
        if kind == "bar":
            ch.type = "bar" if chart_spec.get("horizontal") else "col"
        for key in chart_spec.get("values") or []:
            if key not in row_cols:
                raise SpecError(f"sheet {ws.title}: chart value column {key!r} not found")
            ci = keys.index(key) + 1
            ch.add_data(Reference(ws, min_col=ci, min_row=header_row, max_row=last), titles_from_data=True)
        cat = chart_spec.get("categories")
        if cat:
            ch.set_categories(Reference(ws, min_col=keys.index(cat) + 1, min_row=first, max_row=last))
        if kind != "pie":
            ch.varyColors = False  # one series = one colour
            ch.x_axis.delete = ch.y_axis.delete = False  # newer Excel hides axes openpyxl leaves undeclared
            ch.y_axis.number_format = "#,##0"
            if len(chart_spec.get("values") or []) == 1:
                ch.legend = None
        ch.width, ch.height = chart_spec.get("width_cm", 16), chart_spec.get("height_cm", 8)
        # default anchor: below the table, so fit-to-width printing does not shrink the table to fit a chart beside it
        ws.add_chart(ch, chart_spec.get("anchor", f"A{r + 1}"))
        stats["charts"] += 1

    pr = spec.get("print") or {}
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = pr.get("orientation", "landscape" if len(columns) > 6 else "portrait")
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{header_row}:{header_row}"
    ws.page_margins.left = ws.page_margins.right = 0.5
    ws.page_margins.top = ws.page_margins.bottom = 0.6
    ws.oddFooter.center.text = "Сторінка &P з &N"
    ws.oddFooter.left.text = pr.get("footer", "&F")
    return ws


def main(argv):
    if len(argv) != 2 or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    src, out = Path(argv[0]), Path(argv[1])
    stats = {"rows": 0, "formulas": 0, "validations": 0, "charts": 0, "names": []}
    try:
        spec = json.loads(src.read_text(encoding="utf-8"))
        sheets = spec.get("sheets") or []
        if not sheets:
            raise SpecError("sheets: at least one sheet is required")
        wb = Workbook()
        wb.remove(wb.active)
        names_seen = set()
        for sheet in sheets:
            build_sheet(wb, sheet, names_seen, stats)
        if "_lists" in wb.sheetnames:
            wb.move_sheet("_lists", offset=len(wb.sheetnames))
        wb.calculation.fullCalcOnLoad = True  # Excel/LibreOffice compute every formula when the file opens
        out.parent.mkdir(parents=True, exist_ok=True)
        wb.save(out)
    except (SpecError, json.JSONDecodeError, OSError, KeyError, ValueError) as e:
        sys.stderr.write(f"make-xlsx: {e}\n")
        return 1
    stats.pop("list_columns", None)
    print(json.dumps({"file": str(out), "sheets": [s.get("name") for s in sheets], **stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
