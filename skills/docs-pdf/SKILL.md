---
name: docs-pdf
description: "PDF work of perfect-docs — create PDFs from HTML or DOCX with correct Cyrillic, fill AcroForm fields, merge, split, extract text and tables, handle scanned PDFs with OCR, redact properly and prepare files for electronic signing. Use when the user needs a PDF made, filled, combined, split, read or checked, or when /office or /pdf routes here."
---

# Docs PDF — make, fill, combine, read

> **Harness:** written with Claude Code tool names. In Antigravity, translate with `${CLAUDE_PLUGIN_ROOT}/references/harness.md`.

PDF is the final, fixed form of a document. Build the content in an editable source (HTML, DOCX, XLSX, PPTX), then print it to PDF; edit the source, never the PDF, when content changes.

## 1. Engine
- **Claude Code with Anthropic’s `pdf` skill listed** (not `perfect-docs-plugin:pdf`, the shortcut back to `/office`): use it for OCR, watermarks, encryption, image extraction and anything not covered below; keep §2–§6 rules.
- **This plugin’s scripts** (any harness):
  - `node "${CLAUDE_PLUGIN_ROOT}/scripts/html-to-pdf.mjs" in.html out.pdf` — Chromium print (Playwright if installed, else local Chrome/Edge/Chromium).
  - `python "${CLAUDE_PLUGIN_ROOT}/scripts/pdf-tools.py" <info|merge|split|text|fields|fill|tables> …` — pypdf (`pip install pypdf`); `tables` also needs `pip install pdfplumber`. Missing library → the script prints the install line (exit 3); install only with the user’s OK.

## 2. Create a PDF
| Source | Route | Why |
|---|---|---|
| Document designed for print (proposal, report, certificate, price list) | HTML + CSS → `html-to-pdf.mjs` | full typographic control, any Cyrillic web font, tables that break cleanly |
| Existing DOCX / XLSX / PPTX | export: Word/Excel/PowerPoint «Save as PDF», or `soffice --headless --convert-to pdf --outdir out file.docx` | keeps the editable source as the master |
| HTML slide deck | `html-to-pdf.mjs` (one page per slide via the deck’s print CSS) | see docs-pptx `html-deck.md` §5 |
| Programmatic PDF (reportlab and similar) | only with a registered TTF that has Cyrillic (Arial, DejaVu Sans, Noto Sans) | the 14 built-in PDF fonts (Helvetica, Times) have no Cyrillic — Ukrainian text comes out as black boxes |

A4 HTML document skeleton:
```html
<!doctype html><html lang="uk"><head><meta charset="utf-8"><title>Комерційна пропозиція № 12</title>
<style>
  @page { size: A4; margin: 20mm 10mm 20mm 30mm; }
  html { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  body { font: 11pt/1.45 "Times New Roman", serif; color: #111; margin: 0; }
  h1 { font-size: 16pt; margin: 0 0 6mm; break-after: avoid; }
  table { width: 100%; border-collapse: collapse; } thead { display: table-header-group; }
  tr, img, figure { break-inside: avoid; } td.num { text-align: right; white-space: nowrap; }
</style></head><body> … </body></html>
```
`thead { display: table-header-group }` repeats table headers on every page. Page numbers in the margin (`@page { @bottom-center { content: counter(page) } }`) depend on the Chromium version — **[Unverified]** for the installed one: test once; if they do not render, use the DOCX route for documents that need numbered pages.

Metadata: set `<title>` (becomes the PDF title) and `lang`. Check after export: `pdf-tools.py info out.pdf` (pages, page size in points: A4 = 595 × 842, 16:9 deck = 1440 × 810).

## 3. Fill a form
1. `pdf-tools.py fields form.pdf` → names, types, current values, options of check boxes and lists.
2. Map the user’s data to field names in `values.json` (`{"client_name": "ТОВ «Приклад»", "agree": "/Yes"}` — check-box values are the states listed by `fields`).
3. `pdf-tools.py fill form.pdf values.json filled.pdf` — unknown names stop the script; the file is marked so viewers rebuild field appearances (needed for Cyrillic).
4. Verify: `fields filled.pdf`, then open or render a page. If a viewer shows empty fields or wrong glyphs, open in Adobe Acrobat Reader, which regenerates appearances; flattening a form with Cyrillic needs a Cyrillic font embedded — use Anthropic’s `pdf` skill or overlay text (below).
5. **Flat PDF without fields** (`fill` says «no AcroForm fields»): overlay text at coordinates with PyMuPDF and a Cyrillic TTF — `page.insert_text((x, y), "ТОВ «Приклад»", fontname="arial", fontfile=r"C:\Windows\Fonts\arial.ttf", fontsize=10)`; find coordinates from `page.get_text("words")`. Or rebuild the form in HTML when it will be reused.
Personal data in forms (passport, РНОКПП, addresses) stays local; never send forms to online services.

## 4. Merge, split, reorder
- Merge: `pdf-tools.py merge out.pdf a.pdf b.pdf c.pdf` (order as given).
- Split: `pdf-tools.py split in.pdf out_dir --ranges 1-3,4,5-` (no ranges → one file per page).
- Rotate / reorder: pypdf — `w = pypdf.PdfWriter(clone_from="in.pdf"); w.pages[0].rotate(90); w.write("out.pdf")`; reorder by appending pages in the new order to a new writer.
- Size: scans heavier than ~5 MB per page usually need recompression (Anthropic’s `pdf` skill, Ghostscript, or re-scan at 200–300 dpi greyscale).

## 5. Read: text, tables, scans
- Text: `pdf-tools.py text in.pdf [--pages 2-4]` (pages separated by a form feed). Reading order in multi-column layouts can be wrong — check before quoting.
- Tables: `pdf-tools.py tables in.pdf out_dir` → one CSV per table (UTF-8 with BOM). Merged cells and borderless tables break detection: verify row counts and totals against the PDF, then build the XLSX with docs-xlsx.
- **Scanned PDF** (text command prints nothing and warns): OCR with Ukrainian + English models — `ocrmypdf -l ukr+eng in.pdf out.pdf` (adds a text layer) or `tesseract page.png out -l ukr+eng pdf`. Both need installation (Tesseract with the `ukr` language data). Proofread OCR output: numbers and «і/ї/є» are the usual errors.
- Never quote numbers from a PDF you could not extract or read reliably — say which pages failed.

## 6. Redaction, security, signing
- Redaction must delete the content, not cover it: PyMuPDF `page.add_redact_annot(rect)` then `page.apply_redactions()`; verify with `text` that the words are gone. Black rectangles drawn on top leave the text extractable.
- Remove metadata that leaks names or paths before sending (`pypdf` writer `add_metadata` with clean values, or the source app’s «Inspect document»).
- Passwords/encryption: only with a password the user provides for this purpose; never store it in files or logs.
- Electronic signature (КЕП): prepare the final PDF; the user signs it in their signing tool (e.g. Дія.Підпис, a bank or a qualified provider). Never handle keys or key passwords. After signing, the PDF must not change.

## 7. Checklist
- [ ] Source file kept and delivered alongside the PDF when the user may need changes.
- [ ] Cyrillic renders in the intended font on every page (render 2–3 pages to PNG and look).
- [ ] Page size and count as expected (`info`).
- [ ] Forms: every intended field filled, no unknown names, appearance checked.
- [ ] Extracted text/tables reconciled with the PDF; OCR proofread.
- [ ] No personal data left in metadata; redactions verified by text extraction.
