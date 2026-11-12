---
name: docs-docx
description: "Word (DOCX) rules of perfect-docs — document structure, styles instead of manual formatting, numbering, tables, headers and footers with page numbers, Ukrainian typography («», apostrophe, no-break spaces) and the official-document profile of ДСТУ 4163:2020. Use when creating, editing, filling or checking any Word document, or when /office or /docx routes a Word task here."
---

# Docs DOCX — Word documents that survive editing

> **Harness:** written with Claude Code tool names. In Antigravity, translate with `${CLAUDE_PLUGIN_ROOT}/references/harness.md`.

A professional DOCX is built from styles, so the next person can edit it without breaking it: change the Normal style and the whole document follows. References in `${CLAUDE_SKILL_DIR}/references/`:

| File | Use it for |
|---|---|
| `ukrainian-typography.md` | Quotes, apostrophe, dashes, no-break spaces, numbers, dates, names, frequent errors, regex checks |
| `official-format.md` | ДСТУ 4163:2020 profile for orders, letters, minutes: margins, fonts, requisites, layouts, status of each value |

## 1. Engine
- **Claude Code with Anthropic’s `docx` skill listed** (e.g. `anthropic-skills:docx`, `document-skills:docx` — never `perfect-docs-plugin:docx`, which is only the shortcut back to `/office`): load it for file mechanics — creating with its toolchain, editing XML, tracked changes, comments, validation. Apply this skill’s rules to what it produces.
- **Otherwise** (Antigravity, other harnesses): python-docx. Check once: `python -c "import docx"`; missing → tell the user `pip install python-docx` and install only with their OK.
- Business documents with money (invoice, act, waybill) → `python "${CLAUDE_PLUGIN_ROOT}/scripts/make-docx.py" data.json out.docx` (docs-templates). Do not hand-build those tables.

## 2. Structure rules
1. **Styles, not direct formatting.** Title, Heading 1–3, Normal, List Bullet, List Number, Caption, a table style. Font, size, spacing live in styles; bold inside a sentence is the only common direct formatting.
2. **Spacing** with `space_before`/`space_after` on styles; never empty paragraphs for gaps; page breaks with «page break before» on the heading or a real break, never repeated Enter.
3. **Headings** keep with next paragraph; no heading alone at the bottom of a page; widow/orphan control on.
4. **Numbering**: bullets and numbered lists through list styles. Contract numbering «1.», «1.1.», «1.1.1.»: in an existing Word file keep its multilevel list; in generated files either a real multilevel list (Anthropic’s `docx` skill supports numbering definitions) or literal clause numbers written by the generator — never a mix. Re-check cross-references («п. 4.2») after any insertion.
5. **Tables**: header row repeats on each page (`w:tblHeader`), rows do not split (`w:cantSplit`), units in the header («Сума, грн»), numbers right-aligned with decimal comma and no-break thousands spaces, text left-aligned and top-aligned; total row bold; widths set explicitly (autofit off) so Word and LibreOffice agree.
6. **Headers and footers**: page numbers as fields, not typed numbers («Сторінка X з Y» via PAGE and NUMPAGES); different first page for letterheads; running header with the document name for long documents.
7. **Page**: A4; business default margins 20/10/20/30 mm (top/right/bottom/left), body 11–12 pt; official ОРД → `official-format.md`. Landscape only for a section with a wide table (section break before and after).
8. **Fonts with Cyrillic**: Times New Roman, Arial, Calibri, Cambria, Segoe UI — present on Windows and macOS Office; set `w:rFonts` ascii, hAnsi, cs and eastAsia so no script falls back. Do not embed decorative web fonts in DOCX.
9. **Images**: inline, width ≤ text width, alt text on every image, logos as PNG/SVG at print resolution (≥ 300 dpi at placed size).
10. **Metadata**: title, language `uk-UA` (or the document’s language), organisation as author; remove personal author names, comments and tracked changes before sending unless asked to keep them.

## 3. Ukrainian typography — the short list
«лапки», apostrophe ’, dash — with spaces, ranges 2025–2026, № 27, 15 000,00 грн, 37 %, «12 листопада 2026 р.», «Олена ІВАНЕНКО» in signatures, no-break spaces between number and unit, after м./вул./ст./п. Full rules and the automated check list: `ukrainian-typography.md`. Run that check on every document before delivery.

## 4. python-docx recipes
```python
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

doc = docx.Document()
s = doc.sections[0]
s.page_width, s.page_height = Mm(210), Mm(297)
s.top_margin, s.right_margin, s.bottom_margin, s.left_margin = Mm(20), Mm(10), Mm(20), Mm(30)

normal = doc.styles["Normal"]
normal.font.name, normal.font.size = "Times New Roman", Pt(12)
rfonts = normal.element.get_or_add_rPr().get_or_add_rFonts()
for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
    rfonts.set(qn(attr), "Times New Roman")
normal.paragraph_format.space_after = Pt(6)

def field(paragraph, instr):                      # PAGE, NUMPAGES, TOC \o "1-3" \h
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    run, text = OxmlElement("w:r"), OxmlElement("w:t")
    text.text = "1"
    run.append(text)
    fld.append(run)
    paragraph._p.append(fld)

foot = s.footer.paragraphs[0]
foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
foot.add_run("Сторінка ")
field(foot, "PAGE")
foot.add_run(" з ")
field(foot, "NUMPAGES")

def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    for tag in ("w:tblHeader", "w:cantSplit"):
        tr_pr.append(OxmlElement(tag))

NBSP = chr(0xA0)                                    # «15 000 грн», «№ 27»
```
Fields show «1» until Word updates them (F9, or automatically when printing / exporting to PDF). A TOC field needs an update in Word or LibreOffice before delivery; say so if you cannot run one.

## 5. Editing an existing document
- Never rebuild a user’s document from scratch to change a part; edit in place and keep its styles, numbering and section settings.
- Word splits text into runs at random places, so `{{placeholder}}` may span runs. Replace at paragraph level: join the runs’ text, replace, write the result into the first run, clear the rest (keeps the first run’s formatting). Walk body paragraphs, table cells (recursively — tables nest), headers and footers.
- After filling, search for leftovers: `{{`, `[`, `XXX`, «Лорем», `____` that should hold a value.
- Tracked changes: python-docx cannot write them. Claude Code → Anthropic’s `docx` skill. Elsewhere → deliver a clean revised file plus a change table (clause · was · now · why), and tell the user they can produce redlines in Word: Review → Compare.
- Read/extract: paragraphs and tables (`doc.paragraphs`, `doc.tables`, nested `cell.tables`) — text in text boxes and shapes needs XML (`w:txbxContent`); mention if the document uses them.

## 6. Verify by looking
Render and inspect every page before delivery:
- LibreOffice: `soffice --headless --convert-to pdf --outdir out file.docx`
- Windows with Word: PowerShell `New-Object -ComObject Word.Application` → `Documents.Open(path)` → `SaveAs(pdfPath, 17)`
- Then PNG pages: `python -c "import pymupdf; d=pymupdf.open('out/file.pdf'); [p.get_pixmap(dpi=80).save(f'out/p{i+1}.png') for i, p in enumerate(d)]"` (PyMuPDF), or `pdftoppm -png -r 80 out/file.pdf out/p`.
Look for: broken table widths, a heading alone at a page bottom, wrapped signature lines, wrong font fallback (boxes or a different face in Cyrillic), placeholders left, page count.

## 7. Delivery checklist
- [ ] Styles carry all formatting; no empty-paragraph spacing.
- [ ] Headings and lists numbered consistently; cross-references valid.
- [ ] Tables: header repeat, no split rows, numbers right-aligned, units in headers.
- [ ] Page numbers are fields; first-page header correct.
- [ ] Typography check from `ukrainian-typography.md` §6 passed.
- [ ] All amounts computed by a script; words from `uah-words.mjs`.
- [ ] Rendered to PDF and every page looked at.
- [ ] Metadata set; comments/tracked changes removed unless requested.
- [ ] File in `deliverables/docs/` (or the user’s folder) with a descriptive Latin name.
