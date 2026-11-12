#!/usr/bin/env python3
"""make-docx — Ukrainian invoice (рахунок на оплату), act (акт наданих послуг / виконаних робіт) or waybill
(видаткова накладна) as a DOCX file from JSON. Totals are computed here with Decimal (ROUND_HALF_UP to kopiyky);
the amount in words comes from uah-words.mjs (one implementation for the whole plugin).

Requires: python-docx  ->  pip install python-docx
          Node.js >= 18 on PATH for the amount in words (or give "total_words" in the JSON; it is then unverified).
Usage:    python make-docx.py <data.json> <out.docx>
Output:   the DOCX + a JSON summary on stdout (totals, words, warnings).
Exit:     0 ok · 1 invalid data · 2 usage · 3 missing dependency.
JSON shape and field rules: skills/docs-templates/references/primary-documents.md; example: scripts/examples/act.json
"""
import json
import re
import shutil
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

try:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt
except ImportError:
    sys.stderr.write("make-docx: missing Python library python-docx.\nInstall it with:  pip install python-docx\n")
    sys.exit(3)

HERE = Path(__file__).resolve().parent
UAH_WORDS = HERE / "uah-words.mjs"
NBSP = "\u00a0"
KOP = Decimal("0.01")
MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]

KINDS = {
    "invoice": {"title": "Рахунок на оплату", "supplier": "Постачальник", "buyer": "Покупець", "item": "Товари (роботи, послуги)"},
    "act": {"title": "Акт", "supplier": "Виконавець", "buyer": "Замовник", "item": "Найменування послуги",
            "supplier_from": "Від Виконавця:", "buyer_from": "Від Замовника:"},
    "waybill": {"title": "Видаткова накладна", "supplier": "Постачальник", "buyer": "Покупець", "item": "Товар",
                "supplier_from": "Від постачальника:", "buyer_from": "Від покупця:"},
}


class DataError(Exception):
    pass


def money(value, field):
    try:
        d = Decimal(str(value).replace(" ", "").replace(NBSP, "").replace(",", "."))
    except InvalidOperation:
        raise DataError(f"{field}: not a number: {value!r}")
    if d < 0:
        raise DataError(f"{field}: negative value {value!r}")
    return d


def fmt(d):
    """15000 -> '15 000,00' with no-break spaces (Ukrainian number format)."""
    q = d.quantize(KOP, rounding=ROUND_HALF_UP)
    whole, frac = f"{q:.2f}".split(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return f"{NBSP.join(groups)},{frac}"


def fmt_qty(d):
    s = f"{d.normalize():f}"
    return s.replace(".", ",")


def date_words(iso):
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        raise DataError(f"date must be YYYY-MM-DD, got {iso!r}")
    y, mo, d = int(m[1]), int(m[2]), int(m[3])
    if not 1 <= mo <= 12 or not 1 <= d <= 31:
        raise DataError(f"invalid date {iso!r}")
    return f"{d:02d}{NBSP}{MONTHS[mo - 1]} {y}{NBSP}р."


def date_digits(iso):
    y, mo, d = iso.split("-")
    return f"{d}.{mo}.{y}"


def iban_ok(iban):
    s = re.sub(r"\s", "", iban or "").upper()
    if not re.fullmatch(r"UA\d{27}", s):
        return False
    moved = s[4:] + s[:4]
    digits = "".join(str(int(c, 36)) for c in moved)
    return int(digits) % 97 == 1


def code_label(party):
    if party.get("code_label"):
        return party["code_label"]
    code = str(party.get("code", ""))
    return "код ЄДРПОУ" if len(code) == 8 else "РНОКПП" if len(code) == 10 else "код"


def validate(data):
    errors, warnings = [], []
    kind = data.get("type")
    if kind not in KINDS:
        raise DataError(f'type must be one of {", ".join(KINDS)}; got {kind!r}')
    for f in ("number", "date"):
        if not str(data.get(f, "")).strip():
            errors.append(f"{f} is required")
    for role in ("supplier", "buyer"):
        p = data.get(role) or {}
        if not p.get("name"):
            errors.append(f"{role}.name is required")
        code = str(p.get("code", ""))
        if code and not re.fullmatch(r"\d{8}|\d{10}", code) and not p.get("code_label"):
            errors.append(f"{role}.code must be 8 digits (ЄДРПОУ) or 10 digits (РНОКПП); set code_label for other identifiers")
        if p.get("iban") and not iban_ok(p["iban"]):
            errors.append(f"{role}.iban fails the UA IBAN check (UA + 27 digits, ISO 13616 mod-97)")
    sup, buy = data.get("supplier") or {}, data.get("buyer") or {}
    if not sup.get("code"):
        errors.append("supplier.code is required (ЄДРПОУ or РНОКПП)")
    if not buy.get("code"):
        warnings.append("buyer.code is empty — fine for a private person, required for a company or ФОП")
    if kind == "invoice" and not sup.get("iban"):
        errors.append("supplier.iban is required on an invoice")
    if kind in ("act", "waybill"):
        for role, p in (("supplier", sup), ("buyer", buy)):
            if not p.get("signer"):
                errors.append(f"{role}.signer is required: a primary document identifies who took part (Law 996-XIV art. 9)")
            if not p.get("signer_position"):
                warnings.append(f"{role}.signer_position is empty — positions of responsible persons are a mandatory requisite of a primary document")
    if not data.get("basis"):
        warnings.append("basis (договір / замовлення) is empty")
    items = data.get("items") or []
    if not items:
        errors.append("items: at least one line is required")
    for i, it in enumerate(items, 1):
        for f in ("name", "unit", "qty", "price"):
            if it.get(f) in (None, ""):
                errors.append(f"items[{i}].{f} is required")
    vat = data.get("vat") or {}
    if vat.get("mode", "none") not in ("none", "on_top", "included"):
        errors.append('vat.mode must be "none", "on_top" or "included"')
    if errors:
        raise DataError("; ".join(errors))
    return warnings


def compute(data):
    lines = []
    for i, it in enumerate(data["items"], 1):
        qty = money(it["qty"], f"items[{i}].qty")
        if qty == 0:
            raise DataError(f"items[{i}].qty is zero")
        price = money(it["price"], f"items[{i}].price")
        lines.append({"n": i, "name": it["name"], "unit": it["unit"], "qty": qty, "price": price,
                      "sum": (qty * price).quantize(KOP, rounding=ROUND_HALF_UP)})
    lines_sum = sum((ln["sum"] for ln in lines), Decimal("0"))
    vat = data.get("vat") or {}
    mode = vat.get("mode", "none")
    rate = money(vat.get("rate", 20), "vat.rate") if mode != "none" else Decimal("0")
    if mode == "on_top":
        subtotal = lines_sum
        tax = (subtotal * rate / 100).quantize(KOP, rounding=ROUND_HALF_UP)
        total = subtotal + tax
    elif mode == "included":
        total = lines_sum
        tax = (total * rate / (100 + rate)).quantize(KOP, rounding=ROUND_HALF_UP)
        subtotal = total - tax
    else:
        subtotal, tax, total = lines_sum, Decimal("0.00"), lines_sum
    return lines, {"mode": mode, "rate": rate, "subtotal": subtotal, "vat": tax, "total": total}


def amount_words(total, given, warnings):
    node = shutil.which("node")
    if not node:
        if given:
            warnings.append("total_words taken from JSON unverified (Node.js not found)")
            return given
        sys.stderr.write("make-docx: Node.js >= 18 is required for the amount in words (node not found on PATH).\n"
                         "Install Node.js or add \"total_words\" to the JSON.\n")
        sys.exit(3)
    r = subprocess.run([node, str(UAH_WORDS), f"{total:.2f}", "--json", "--capitalize"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise DataError(f"uah-words failed: {r.stderr.strip()}")
    words = json.loads(r.stdout)["words"]
    if given and given.strip().rstrip(".").lower() != words.lower():
        raise DataError(f'total_words does not match the total {fmt(total)}: expected "{words}"')
    return words


# ---------- DOCX helpers ----------

def set_fonts(doc, family, size):
    for style_name in ("Normal", "Table Grid"):
        try:
            st = doc.styles[style_name]
        except KeyError:
            continue
        st.font.name = family
        st.font.size = Pt(size)
        rpr = st.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.insert(0, rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), family)
    pf = doc.styles["Normal"].paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(0), Pt(2), 1.0


def para(container, text="", bold=False, size=None, align=None, space_after=None):
    p = container.add_paragraph()
    if text:
        run = p.add_run(text)
        run.bold = bold
        if size:
            run.font.size = Pt(size)
    if align:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    return p


def cell_text(cell, text, bold=False, align=None, size=None):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(0)


def no_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def widths(table, mm):
    table.autofit = False
    for row in table.rows:
        for cell, w in zip(row.cells, mm):
            cell.width = Mm(w)


def row_flags(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)
    if header:
        h = OxmlElement("w:tblHeader")
        trPr.append(h)


def party_lines(p):
    out = [p["name"]]
    if p.get("code"):
        out.append(f"{code_label(p)} {p['code']}")
    if p.get("address"):
        out.append(p["address"])
    if p.get("iban"):
        iban = re.sub(r"\s", "", p["iban"]).upper()
        bank = f", {p['bank']}" if p.get("bank") else ""
        out.append(f"IBAN {iban}{bank}")
    if p.get("tax_status"):
        out.append(p["tax_status"])
    if p.get("phone"):
        out.append(f"тел. {p['phone']}")
    return "\n".join(out)


def build(data, lines, totals, words, out_path):
    kind = data["type"]
    labels = {**KINDS[kind], **(data.get("labels") or {})}
    style = data.get("style") or {}
    doc = Document()
    set_fonts(doc, style.get("font", "Times New Roman"), style.get("size", 11))
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    top, right, bottom, left = style.get("margins_mm", [20, 10, 20, 30])
    sec.top_margin, sec.right_margin, sec.bottom_margin, sec.left_margin = Mm(top), Mm(right), Mm(bottom), Mm(left)
    text_width = 210 - left - right
    sup, buy = data["supplier"], data["buyer"]
    number, d_words = data["number"], date_words(data["date"])

    if kind == "act":
        what = "здачі-приймання виконаних робіт" if data.get("act_kind") == "works" else "приймання-передачі наданих послуг"
        para(doc, f"АКТ №{NBSP}{number}", bold=True, size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
        para(doc, what, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
        p = para(doc, space_after=8)
        p.paragraph_format.tab_stops.add_tab_stop(Mm(text_width), WD_TAB_ALIGNMENT.RIGHT)
        p.add_run(f"{data.get('place', '')}\t{d_words}")
        works = data.get("act_kind") == "works"
        rep_s = f", {sup['represented_by']}" if sup.get("represented_by") else ""
        rep_b = f", {buy['represented_by']}" if buy.get("represented_by") else ""
        basis = f" згідно з {data['basis']}" if data.get("basis") else ""
        period = f" за {data['period']}" if data.get("period") else ""
        verb = "виконав, а Замовник прийняв такі роботи" if works else "надав, а Замовник прийняв такі послуги"
        intro = (f"{sup['name']}{rep_s} (далі — {labels['supplier']}), з однієї сторони, та {buy['name']}{rep_b} "
                 f"(далі — {labels['buyer']}), з іншої сторони, склали цей акт про те, що {labels['supplier']} {verb}{basis}{period}:")
        p = para(doc, intro, space_after=6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if works:
            labels["item"] = "Найменування роботи"
    else:
        para(doc, f"{labels['title']} №{NBSP}{number} від {d_words}", bold=True, size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
        rows = [(labels["supplier"], party_lines(sup)), (labels["buyer"], party_lines(buy))]
        if data.get("basis"):
            rows.append(("Підстава" if kind == "waybill" else "Договір", data["basis"]))
        if kind == "waybill" and data.get("place"):
            rows.append(("Місце складання", data["place"]))
        t = doc.add_table(rows=len(rows), cols=2)
        no_borders(t)
        for r, (label, value) in zip(t.rows, rows):
            cell_text(r.cells[0], f"{label}:", bold=True)
            cell_text(r.cells[1], value)
        widths(t, [38, text_width - 38])
        para(doc, space_after=4)

    # items table
    head = ["№", labels["item"], "Од.", "Кількість", "Ціна, грн", "Сума, грн"]
    col_mm = [9, text_width - 9 - 20 - 20 - 26 - 28, 20, 20, 26, 28]
    t = doc.add_table(rows=1 + len(lines), cols=6)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, h in zip(t.rows[0].cells, head):
        cell_text(c, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    row_flags(t.rows[0], header=True)
    R = WD_ALIGN_PARAGRAPH.RIGHT
    for row, ln in zip(t.rows[1:], lines):
        vals = [str(ln["n"]), ln["name"], ln["unit"], fmt_qty(ln["qty"]), fmt(ln["price"]), fmt(ln["sum"])]
        aligns = [WD_ALIGN_PARAGRAPH.CENTER, None, WD_ALIGN_PARAGRAPH.CENTER, R, R, R]
        for c, v, a in zip(row.cells, vals, aligns):
            cell_text(c, v, align=a)
        row_flags(row)
    widths(t, col_mm)

    # totals
    rate = f"{totals['rate'].normalize():f}".replace(".", ",")
    if totals["mode"] == "on_top":
        tot_rows = [("Разом без ПДВ:", fmt(totals["subtotal"])), (f"ПДВ {rate}{NBSP}%:", fmt(totals["vat"])), ("Усього з ПДВ:", fmt(totals["total"]))]
    elif totals["mode"] == "included":
        tot_rows = [("Усього з ПДВ:", fmt(totals["total"])), (f"у тому числі ПДВ {rate}{NBSP}%:", fmt(totals["vat"]))]
    else:
        tot_rows = [("Усього:", fmt(totals["total"])), ("ПДВ:", "без ПДВ")]
    t = doc.add_table(rows=len(tot_rows), cols=2)
    no_borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.RIGHT
    for r, (label, value) in zip(t.rows, tot_rows):
        cell_text(r.cells[0], label, bold=True, align=R)
        cell_text(r.cells[1], value, bold=True, align=R)
    widths(t, [60, 32])
    para(doc, space_after=2)

    vat_phrase = "без ПДВ" if totals["mode"] == "none" else f"у тому числі ПДВ {fmt(totals['vat'])}{NBSP}грн"
    para(doc, f"Усього найменувань {len(lines)}, на суму {fmt(totals['total'])}{NBSP}грн.", space_after=0)
    p = para(doc, space_after=6)
    p.add_run("Сума прописом: ").bold = True
    p.add_run(f"{words}, {vat_phrase}.")

    if kind == "invoice":
        if data.get("due_date"):
            para(doc, f"Рахунок дійсний до {date_words(data['due_date'])}", space_after=0)
        purpose = data.get("payment_purpose") or f"Оплата за рахунком №{NBSP}{number} від {date_digits(data['date'])}, {vat_phrase}"
        para(doc, f"Призначення платежу: {purpose}", space_after=6)
    if kind == "act":
        closing = data.get("closing_text") or (
            f"{'Роботи виконано' if data.get('act_kind') == 'works' else 'Послуги надано'} в повному обсязі, у встановлені строки та належної якості. "
            f"{labels['buyer']} претензій щодо обсягу, якості та строків не має.")
        para(doc, closing, space_after=2).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        copies = ("Акт складено в електронній формі та підписано кваліфікованими електронними підписами сторін."
                  if data.get("electronic") else "Акт складено у двох примірниках, по одному для кожної зі сторін.")
        para(doc, copies, space_after=6)
    for note in data.get("notes") or []:
        para(doc, note, space_after=2)
    para(doc, space_after=6)

    # signatures
    def sig_block(cell, heading, party, action=None):
        cell.text = ""
        lines_ = [heading]
        if party.get("signer_position"):
            lines_.append(party["signer_position"])
        if action:
            lines_.append(action)
        lines_.append(f"______________ {party.get('signer', '').replace(' ', NBSP)}".rstrip())
        if data.get("seal"):
            lines_.append("М. П.")
        for i, ln in enumerate(lines_):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            r = p.add_run(ln)
            r.bold = i == 0
            p.paragraph_format.space_after = Pt(4)

    if kind == "invoice":
        t = doc.add_table(rows=1, cols=1)
        no_borders(t)
        sig_block(t.rows[0].cells[0], f"{labels['supplier']}:", sup)
    else:
        t = doc.add_table(rows=1, cols=2)
        no_borders(t)
        actions = (None, None) if kind == "act" else ("Відвантажив(ла)", "Отримав(ла)")
        sig_block(t.rows[0].cells[0], labels["supplier_from"], sup, actions[0])
        sig_block(t.rows[0].cells[1], labels["buyer_from"], buy, actions[1])
        widths(t, [text_width / 2, text_width / 2])

    props = doc.core_properties
    props.title = f"{labels['title']} № {number} від {date_digits(data['date'])}"
    props.language = "uk-UA"
    doc.save(out_path)


def main(argv):
    if len(argv) != 2 or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    src, out = Path(argv[0]), Path(argv[1])
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
        warnings = validate(data)
        date_words(data["date"])
        lines, totals = compute(data)
        words = amount_words(totals["total"], data.get("total_words"), warnings)
        out.parent.mkdir(parents=True, exist_ok=True)
        build(data, lines, totals, words, out)
    except (DataError, json.JSONDecodeError, OSError) as e:
        sys.stderr.write(f"make-docx: {e}\n")
        return 1
    print(json.dumps({"file": str(out), "type": data["type"], "number": data["number"], "items": len(lines),
                      "subtotal": f"{totals['subtotal']:.2f}", "vat": f"{totals['vat']:.2f}", "total": f"{totals['total']:.2f}",
                      "words": words, "warnings": warnings}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
