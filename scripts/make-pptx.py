#!/usr/bin/env python3
"""make-pptx — a 16:9 PowerPoint deck from an outline JSON: real title/body placeholders (outline view and screen
readers work), one consistent grid, theme colours and fonts, speaker notes, slide numbers, density warnings.

Requires: python-pptx  ->  pip install python-pptx
Usage:    python make-pptx.py <outline.json> <out.pptx>
Output:   the PPTX + a JSON summary on stdout (slide count, warnings: density, missing notes, missing alt text).
Exit:     0 ok · 1 invalid outline · 2 usage · 3 missing dependency.
Layouts:  title · section · bullets · two_column · big_number · quote · table · image · closing
Outline shape and an example: skills/docs-pptx/SKILL.md, scripts/examples/deck.json
"""
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

try:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Emu, Inches, Pt
except ImportError:
    sys.stderr.write("make-pptx: missing Python library python-pptx.\nInstall it with:  pip install python-pptx\n")
    sys.exit(3)

W, H = Inches(13.333), Inches(7.5)
MX = Inches(0.75)            # side margin
BODY_TOP = Inches(1.85)
BODY_H = Inches(4.85)
LIMITS = {"bullets": 6, "bullet_chars": 110, "title_chars": 70, "table_rows": 8, "table_cols": 6}
LAYOUT = {"title": 0, "bullets": 1, "section": 2, "two_column": 3, "big_number": 5, "quote": 5, "table": 5, "image": 5, "closing": 2}


class OutlineError(Exception):
    pass


def rgb(hex_value, where):
    s = str(hex_value).lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        raise OutlineError(f"{where}: colour must be 6 hex digits, got {hex_value!r}")
    return RGBColor.from_string(s.upper())


NBSP = "\u00a0"
NBSP_BEFORE_UNIT = re.compile(r"(?<=\d) (?=(%|₴|грн|коп\.|тис\.|млн|млрд)(?!\w))")
NBSP_SCALE_CURRENCY = re.compile(r"(?:(?<=млн)|(?<=млрд)|(?<=тис\.)) (?=₴|грн)")


def typo(text):
    """Keep numbers with their units on one line: 37 %, 18,4 млн ₴ (no-break spaces)."""
    return NBSP_SCALE_CURRENCY.sub(NBSP, NBSP_BEFORE_UNIT.sub(NBSP, str(text)))


def style_runs(paragraph, font, size, color, bold=None, italic=None):
    for run in paragraph.runs:
        run.text = typo(run.text)
        run.font._rPr.set("cap", "none")  # some template layouts force ALL CAPS titles
        run.font.name = font
        run.font.size = Pt(size)
        run.font.color.rgb = color
        if bold is not None:
            run.font.bold = bold
        if italic is not None:
            run.font.italic = italic


def no_bullet(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("marL", "0")
    pPr.set("indent", "0")
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    pPr.append(pPr.makeelement(qn("a:buNone"), {}))


def place(shape, left, top, width, height):
    shape.left, shape.top, shape.width, shape.height = Emu(int(left)), Emu(int(top)), Emu(int(width)), Emu(int(height))


def textbox(slide, left, top, width, height, text, font, size, color, bold=False, italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Emu(int(left)), Emu(int(top)), Emu(int(width)), Emu(int(height)))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        style_runs(p, font, size, color, bold, italic)
    return tb


def set_title(slide, text, th, size=32, top=Inches(0.55), height=Inches(1.15), anchor=MSO_ANCHOR.BOTTOM, color=None):
    title = slide.shapes.title
    place(title, MX, top, W - 2 * MX, height)
    tf = title.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.text = text
    for p in tf.paragraphs:
        p.alignment = PP_ALIGN.LEFT
        style_runs(p, th["heading_font"], size, color or th["text"], bold=True)
    return title


def fill_bullets(tf, items, th, base=22, heading=None):
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    first = True
    if heading:
        p = tf.paragraphs[0]
        p.text = heading
        p.space_after = Pt(12)
        no_bullet(p)
        style_runs(p, th["heading_font"], base + 2, th["accent"], bold=True)
        first = False
    for item in items:
        for text, level in ([(item, 0)] if isinstance(item, str) else [(sub, 1) for sub in item]):
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.text = str(text)
            p.level = level
            p.space_after = Pt(10 if level == 0 else 6)
            style_runs(p, th["font"], base if level == 0 else base - 4, th["text"] if level == 0 else th["muted"])


def accent_rule(slide, th, top=Inches(1.78)):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MX, Emu(int(top)), Inches(0.9), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = th["accent"]
    bar.line.fill.background()


def remove_unused_placeholders(slide):
    """Empty placeholders show "Click to add text" in edit mode — drop every unused one except the title."""
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx == 0:
            continue
        if not ph.has_text_frame or not ph.text_frame.text.strip():
            ph._element.getparent().remove(ph._element)


def count_bullets(items):
    return sum(1 if isinstance(i, str) else len(i) for i in items)


def check_text(n, s, warnings):
    title = s.get("title", "")
    if len(title) > LIMITS["title_chars"]:
        warnings.append(f"slide {n}: title is {len(title)} chars (max {LIMITS['title_chars']}) — make it a shorter claim")
    bullets = s.get("bullets") or []
    if count_bullets(bullets) > LIMITS["bullets"]:
        warnings.append(f"slide {n}: {count_bullets(bullets)} bullets (max {LIMITS['bullets']}) — split the slide")
    for b in [b for i in bullets for b in ([i] if isinstance(i, str) else i)]:
        if len(b) > LIMITS["bullet_chars"]:
            warnings.append(f"slide {n}: a bullet has {len(b)} chars (max {LIMITS['bullet_chars']}) — move detail to notes")


def build(outline, base_dir, out):
    t = outline.get("theme") or {}
    th = {
        "font": t.get("font", "Arial"),
        "heading_font": t.get("heading_font", t.get("font", "Arial")),
        "text": rgb(t.get("text", "1B1D22"), "theme.text"),
        "muted": rgb(t.get("muted", "5D6470"), "theme.muted"),
        "accent": rgb(t.get("accent", "C2410C"), "theme.accent"),
        "on_accent": rgb(t.get("on_accent", "FFFFFF"), "theme.on_accent"),
        "background": rgb(t.get("background", "FFFFFF"), "theme.background"),
    }
    slides = outline.get("slides") or []
    if not slides:
        raise OutlineError("slides: at least one slide is required")
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    warnings = []
    require_notes = outline.get("require_notes", True)
    footer = outline.get("footer", "")

    for n, s in enumerate(slides, 1):
        kind = s.get("layout", "bullets")
        if kind not in LAYOUT:
            raise OutlineError(f"slide {n}: unknown layout {kind!r} (use {', '.join(LAYOUT)})")
        slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT[kind]])
        inverse = kind in ("section", "closing")
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = th["accent"] if inverse else th["background"]
        fg = th["on_accent"] if inverse else th["text"]
        check_text(n, s, warnings)
        if kind != "quote" and not s.get("title"):
            raise OutlineError(f"slide {n}: title is required (every slide states its point in the title)")

        if kind == "title":
            set_title(slide, s["title"], th, size=44, top=Inches(2.0), height=Inches(2.0))
            sub = slide.placeholders[1]
            place(sub, MX, Inches(4.35), W - 2 * MX, Inches(1.2))
            sub.text_frame.text = s.get("subtitle", "")
            for p in sub.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT
                no_bullet(p)
                style_runs(p, th["font"], 22, th["muted"])
            accent_rule(slide, th, top=Inches(4.15))
            if s.get("meta"):
                textbox(slide, MX, Inches(6.3), W - 2 * MX, Inches(0.5), s["meta"], th["font"], 14, th["muted"])
        elif kind in ("section", "closing"):
            set_title(slide, s["title"], th, size=40, top=Inches(2.2), height=Inches(1.8), color=fg)
            body = slide.placeholders[1]
            place(body, MX, Inches(4.15), W - 2 * MX, Inches(1.6))
            body.text_frame.text = s.get("subtitle", "")
            for p in body.text_frame.paragraphs:
                no_bullet(p)
                style_runs(p, th["font"], 20, fg)
        elif kind == "bullets":
            set_title(slide, s["title"], th)
            accent_rule(slide, th)
            body = slide.placeholders[1]
            place(body, MX, BODY_TOP + Inches(0.15), W - 2 * MX, BODY_H)
            fill_bullets(body.text_frame, s.get("bullets") or [], th)
        elif kind == "two_column":
            set_title(slide, s["title"], th)
            accent_rule(slide, th)
            gap = Inches(0.5)
            col_w = (W - 2 * MX - gap) / 2
            for idx, side, left in ((1, "left", MX), (2, "right", MX + col_w + gap)):
                ph = slide.placeholders[idx]
                place(ph, left, BODY_TOP + Inches(0.15), col_w, BODY_H)
                col = s.get(side) or {}
                items = col.get("bullets") or []
                fill_bullets(ph.text_frame, items, th, base=20, heading=col.get("heading"))
                check_text(n, {"bullets": items}, warnings)
        elif kind == "big_number":
            set_title(slide, s["title"], th)
            accent_rule(slide, th)
            textbox(slide, MX, Inches(2.2), W - 2 * MX, Inches(2.2), s.get("number", ""), th["heading_font"], 110, th["accent"], bold=True, anchor=MSO_ANCHOR.MIDDLE)
            textbox(slide, MX, Inches(4.5), Inches(9.5), Inches(1.4), s.get("caption", ""), th["font"], 24, th["text"])
            if s.get("source"):
                textbox(slide, MX, Inches(6.2), W - 2 * MX, Inches(0.5), f"Джерело: {s['source']}", th["font"], 12, th["muted"])
            else:
                warnings.append(f"slide {n}: big number without a source")
        elif kind == "quote":
            quote = str(s.get("quote", "")).strip().strip('«»"')
            set_title(slide, f"«{quote}»", th, size=34, top=Inches(1.6), height=Inches(3.2), anchor=MSO_ANCHOR.MIDDLE)
            for p in slide.shapes.title.text_frame.paragraphs:
                style_runs(p, th["heading_font"], 34, th["text"], bold=False, italic=True)
            textbox(slide, MX, Inches(5.0), W - 2 * MX, Inches(0.8), f"— {s.get('author', '')}", th["font"], 20, th["muted"])
        elif kind == "table":
            set_title(slide, s["title"], th)
            accent_rule(slide, th)
            cols, rows = s.get("columns") or [], s.get("rows") or []
            if not cols or not rows:
                raise OutlineError(f"slide {n}: table needs columns and rows")
            if len(rows) > LIMITS["table_rows"] or len(cols) > LIMITS["table_cols"]:
                warnings.append(f"slide {n}: table {len(rows)}x{len(cols)} exceeds {LIMITS['table_rows']}x{LIMITS['table_cols']} — move the full table to an appendix or XLSX")
            row_h = Inches(0.5)
            gt = slide.shapes.add_table(len(rows) + 1, len(cols), MX, BODY_TOP + Inches(0.2), W - 2 * MX, row_h * (len(rows) + 1)).table
            numeric = re.compile(r"^[\s+\-−]*[\d\s.,]+\s*(%|₴|грн|тис\.|млн)?$")
            for ci, name in enumerate(cols):
                cell = gt.cell(0, ci)
                cell.text = str(name)
                cell.fill.solid()
                cell.fill.fore_color.rgb = th["accent"]
                style_runs(cell.text_frame.paragraphs[0], th["font"], 16, th["on_accent"], bold=True)
            for ri, row in enumerate(rows, 1):
                if len(row) != len(cols):
                    raise OutlineError(f"slide {n}: table row {ri} has {len(row)} cells, expected {len(cols)}")
                for ci, val in enumerate(row):
                    cell = gt.cell(ri, ci)
                    cell.text = str(val)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = th["background"] if ri % 2 else RGBColor(0xF3, 0xF4, 0xF6)
                    p = cell.text_frame.paragraphs[0]
                    if numeric.match(str(val)):
                        p.alignment = PP_ALIGN.RIGHT
                    style_runs(p, th["font"], 15, th["text"])
        elif kind == "image":
            set_title(slide, s["title"], th)
            accent_rule(slide, th)
            img = Path(s.get("image", ""))
            if not img.is_absolute():
                img = base_dir / img
            if not img.is_file():
                raise OutlineError(f"slide {n}: image not found: {img}")
            pic = slide.shapes.add_picture(str(img), MX, BODY_TOP + Inches(0.2))
            box_w, box_h = W - 2 * MX, BODY_H - Inches(0.7)
            scale = min(box_w / pic.width, box_h / pic.height, 1.0)
            pic.width, pic.height = int(pic.width * scale), int(pic.height * scale)
            pic.left = int((W - pic.width) / 2)
            if s.get("alt"):
                pic._element.nvPicPr.cNvPr.set("descr", s["alt"])
            else:
                warnings.append(f"slide {n}: image without alt text")
            if s.get("caption"):
                textbox(slide, MX, BODY_TOP + Inches(0.3) + pic.height, W - 2 * MX, Inches(0.5), s["caption"], th["font"], 14, th["muted"])

        remove_unused_placeholders(slide)
        if n > 1:
            textbox(slide, W - MX - Inches(1.0), H - Inches(0.55), Inches(1.0), Inches(0.35), str(n), th["font"], 12, fg if inverse else th["muted"], align=PP_ALIGN.RIGHT)
            if footer:
                textbox(slide, MX, H - Inches(0.55), Inches(8), Inches(0.35), footer, th["font"], 12, fg if inverse else th["muted"])
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]
        elif require_notes and kind not in ("title", "section", "closing"):
            warnings.append(f"slide {n}: no speaker notes")

    props = prs.core_properties
    props.title = outline.get("title") or slides[0].get("title", "")
    props.language = outline.get("language", "uk-UA")
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return len(slides), warnings


def main(argv):
    if len(argv) != 2 or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    src, out = Path(argv[0]), Path(argv[1])
    try:
        outline = json.loads(src.read_text(encoding="utf-8"))
        count, warnings = build(outline, src.resolve().parent, out)
    except (OutlineError, json.JSONDecodeError, OSError, KeyError) as e:
        sys.stderr.write(f"make-pptx: {e}\n")
        return 1
    print(json.dumps({"file": str(out), "slides": count, "warnings": warnings}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
