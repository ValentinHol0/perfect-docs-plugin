---
name: docs-pptx
description: "Presentation rules of perfect-docs — storyline first, one idea per slide with claim titles, density limits, speaker notes, PPTX generated from an outline, and self-contained HTML slide decks with viewport-fit, keyboard navigation, Cyrillic-safe style presets and PDF export. Use when creating, restructuring or checking a presentation, pitch deck, report deck or HTML slides, or when /office or /pptx routes here."
---

# Docs PPTX — presentations people understand on first view

> **Harness:** written with Claude Code tool names. In Antigravity, translate with `${CLAUDE_PLUGIN_ROOT}/references/harness.md`.

A deck is an argument: each slide makes one claim, and the sequence of titles alone tells the whole story. References in `${CLAUDE_SKILL_DIR}/references/`, template in `${CLAUDE_SKILL_DIR}/assets/`:

| File | Use it for |
|---|---|
| `html-deck.md` | HTML decks: viewport-fit rules, density limits, check sizes, navigation, notes, PDF export, PPTX → HTML |
| `style-presets.md` | 12 Cyrillic-safe visual presets with contrast values, mood mapping, motion, preview method |
| `../assets/deck-template.html` | Working HTML deck skeleton (tokens, viewport frame, controller, print CSS) |

## 1. Engine and format
| Situation | Do |
|---|---|
| Existing .pptx/.potx to edit, a corporate template, comments | Claude Code with Anthropic’s `pptx` skill listed (not `perfect-docs-plugin:pptx`): use it for the file mechanics; apply §2–§5 here. Elsewhere: python-pptx, keep the template’s layouts and masters |
| New PowerPoint deck from content | write the outline JSON (§6) → `python "${CLAUDE_PLUGIN_ROOT}/scripts/make-pptx.py" outline.json out.pptx` |
| Deck shown in a browser, shared as a link, needs motion | HTML from `deck-template.html` (`html-deck.md`) |
| PDF handout | from HTML: `node "${CLAUDE_PLUGIN_ROOT}/scripts/html-to-pdf.mjs"`; from PPTX: PowerPoint/LibreOffice export |
| Lesson slides for school (НУШ) | content from perfect-teach (`/teach`) when installed; this skill builds the file |
| Brand-new visual identity, illustrations, ad creatives | perfect-brand (`/brand`) |

## 2. Storyline before slides
1. Write the audience, the decision or action you want, and the time slot in one line each.
2. Draft titles only — full-sentence claims, ≤ 70 characters: «Повторні клієнти дали 37 % виручки», not «Повторні клієнти». Read them in order: if the story does not hold, fix it here.
3. Proportions: ~1 slide per 1–2 minutes of talk; a 10-minute pitch ≈ 8–12 slides.
4. Skeletons:
   - **Pitch**: problem → solution → why now → market → traction (numbers) → business model → team → ask (amount, use of funds).
   - **Results report**: summary with the decision → results vs plan → what worked / what did not → risks → plan → decision needed.
   - **Sales presentation**: client’s situation → cost of the problem → solution → proof (case with numbers) → offer and price → next step.
   - **Training**: goal → 3–5 modules (concept → example → exercise) → recap → next steps.
5. First slide states the main conclusion; last slide states the ask or next step, never only «Дякую за увагу».

## 3. One idea per slide
- Title = the claim; body = evidence for that claim (number, chart, example, quote). Nothing else.
- Limits (the script warns): ≤ 6 bullets including sub-bullets, ≤ 110 characters per bullet, title ≤ 70 characters, tables ≤ 8 rows × 6 columns. Over the limit → split the slide or move detail to notes/appendix.
- Bullets are parallel in grammar and parallel in level; no single-bullet lists; no full stops at the end of short bullets.
- A number on a slide has a unit, a period and a source («CRM, січень–листопад 2026»). Unsourced numbers do not go on slides.
- Charts: one message, highlighted series in the accent colour, everything else grey; axis from zero for bars; the title says the conclusion.

## 4. Speaker notes
Every content slide of a talk gets notes: 50–150 words — what to say (not a copy of the slide), the transition to the next slide, sources and backup numbers, expected questions. Title, section and closing slides may skip notes. `make-pptx.py` writes them to the notes pane; HTML decks keep them in `<aside class="notes">`.

## 5. Visual rules (PPTX and HTML)
- 16:9; safe margins ≥ 0.75 in (≈ 5 % of width); one grid for all slides; titles at the same position on every slide.
- Type: titles 28–44 pt, body ≥ 18 pt (≥ 20 pt for rooms), footnotes ≥ 12 pt. Fonts with Cyrillic only: Arial, Calibri, Segoe UI for PPTX that others edit; web presets in `style-presets.md`.
- Colour: background, ink, muted, one accent (+ status colours only when they mean something); body text contrast ≥ 4.5:1.
- Images: full-bleed or on the grid, never stretched; alt text for every meaningful image; no clip-art, no stock photos of handshakes.
- Slide numbers on every slide except the title; footer with organisation/date for decks that travel as files.
- Ukrainian typography from docs-docx: «», ’, —, no-break space between number and unit («37 %», «1,8 млн ₴» — `make-pptx.py` inserts these automatically).

## 6. Outline JSON for `make-pptx.py`
```json
{ "title": "Підсумки року", "footer": "ТОВ «Приклад» · грудень 2026",
  "theme": { "font": "Arial", "heading_font": "Arial", "accent": "1F4E79", "text": "1B1D22", "muted": "5D6470", "background": "FFFFFF" },
  "slides": [
    { "layout": "title", "title": "Повторні клієнти дали 37 % виручки", "subtitle": "Підсумки 2026 року", "meta": "Відділ продажів · 15.12.2026" },
    { "layout": "bullets", "title": "Виручка зросла, але залежить від трьох клієнтів", "bullets": ["Виручка — 18,4 млн ₴", ["sub-point"]], "notes": "…" },
    { "layout": "big_number", "title": "…", "number": "37 %", "caption": "…", "source": "CRM, 2026", "notes": "…" },
    { "layout": "two_column", "title": "…", "left": { "heading": "Працює", "bullets": ["…"] }, "right": { "heading": "Не працює", "bullets": ["…"] } },
    { "layout": "table", "title": "…", "columns": ["Квартал", "Виручка, млн ₴"], "rows": [["I", "4,2"]] },
    { "layout": "image", "title": "…", "image": "chart.png", "alt": "…", "caption": "…" },
    { "layout": "quote", "quote": "…", "author": "клієнт, інтерв’ю" },
    { "layout": "section", "title": "Частина 2. План" },
    { "layout": "closing", "title": "Рішення: бюджет 600 тис. ₴", "subtitle": "Погодити до 20 грудня" } ] }
```
The script uses real title and body placeholders (outline view, accessibility), sets 16:9, applies the theme, removes empty placeholders, adds slide numbers and footer, writes notes, and returns warnings: density, missing notes, missing alt text, big number without a source. Resolve every warning or tell the user why it stays. Full example: `${CLAUDE_PLUGIN_ROOT}/scripts/examples/deck.json`.

## 7. HTML deck workflow
1. Content first: titles and notes as in §2–§4 (the same outline can feed `make-pptx.py`).
2. Style: user’s brand → its colours and Cyrillic-capable fonts; otherwise pick from `style-presets.md` by feeling, or show three one-slide previews.
3. Copy `deck-template.html` to `deliverables/docs/<name>.html`, replace the token block, build slides from the patterns (kicker, headline, points, figure, cols, inverse).
4. Verify per `html-deck.md` §2 (zero overflow at all sizes) and §7.
5. Export the PDF handout with `html-to-pdf.mjs`.

## 8. Verify by looking
- PPTX → PDF: PowerPoint (Windows PowerShell COM: `Presentations.Open(path)` → `SaveAs(pdf, 32)`) or `soffice --headless --convert-to pdf deck.pptx`.
- Contact sheet of all slides: PyMuPDF `page.show_pdf_page` into a grid, or `pdftoppm -png -r 50`; look for text overflowing boxes, titles wrapping to 3 lines, empty placeholders, low-contrast text, inconsistent title positions.
- Read the titles in sequence once more — the story must work without the bodies.

## 9. Checklist
- [ ] Titles alone tell the story; first slide = conclusion, last = ask.
- [ ] One idea per slide; within density limits; no script warnings left unexplained.
- [ ] Every number has unit, period, source.
- [ ] Notes on every content slide of a talk.
- [ ] 16:9, one grid, Cyrillic fonts, contrast ≥ 4.5:1 for body.
- [ ] Rendered and inspected; HTML decks pass the overflow check; PDF has one page per slide.
