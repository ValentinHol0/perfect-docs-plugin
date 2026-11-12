# HTML slide decks — build, fit, navigate, export

A deck as one self-contained HTML file: opens from disk in any browser, no build step, prints to PDF one slide per page. Start from `../assets/deck-template.html` (tokens → frame → patterns → navigation → motion → print, in that order) and change only tokens, patterns and content.

## 1. When HTML instead of PPTX
| Choose HTML when | Choose PPTX when |
|---|---|
| the deck is shown from a browser, shared as a link, or embedded in a site | the client will edit it in PowerPoint/Keynote/Google Slides |
| motion, live charts or web fonts matter | the organisation has a PowerPoint template |
| a PDF handout is the only other output | speaker view with notes in PowerPoint is required |
Both are possible: build HTML for the talk and a PPTX via `make-pptx.py` from the same outline.

## 2. Viewport fit — the hard rule
Every slide is exactly one screen. Content that does not fit goes to the next slide; it is never scrolled, clipped or shrunk below readable size.
- `.slide { height: 100vh; height: 100dvh; overflow: hidden; }` — `dvh` for mobile browser bars, `vh` as fallback.
- All type sizes and paddings are `clamp(min, fluid, max)` tokens; nothing in fixed px except hairlines.
- Breakpoints on **height** as well as width: tighten paddings at ≤ 720 px tall, reduce body size and hide navigation chrome at ≤ 520 px.
- Images: `max-height` in `vh`, `object-fit: contain`.
- Grids: `repeat(auto-fit, minmax(min(100%, 16rem), 1fr))` or an explicit 2-column grid that collapses to 1 column on narrow screens.
- Negative fluid values: write `calc(-1 * clamp(…))`; a bare `-clamp(…)` is invalid CSS and is silently ignored.

### Density limits per slide
| Slide | Maximum |
|---|---|
| Title | headline + subtitle + one meta line |
| Statement / content | headline + 3–5 points of ≤ 2 lines, or 2 short paragraphs |
| Key number | 1 figure + 1 caption + source |
| Cards / features | 6 cards |
| Code | 10 lines |
| Quote | 1 quote + attribution |
| Image | 1 image + caption |
| Table | 5 rows × 4 columns; more → appendix or XLSX |

### Check sizes
Desktop 1920×1080, 1440×900, 1280×720 · tablet 1024×768, 768×1024 · phone 390×844, 375×667 · phone landscape 844×390, 667×375. With a browser tool: resize, step through every slide, and evaluate `[...document.querySelectorAll('.slide')].filter(s => s.scrollHeight > s.clientHeight + 1).length` — must be `0` at every size.

## 3. Navigation and behaviour (template already has these)
- Keys: → ↓ PageDown Space Enter = next; ← ↑ PageUp Backspace = previous; Home/End.
- Wheel: one slide per gesture (debounced ~700 ms); touch: native `scroll-snap` gives one slide per swipe — do not add a second touch handler on top (it double-advances).
- Progress bar + «3 / 12» counter; URL hash `#3` deep-links a slide and survives reload.
- Active slide tracked with `IntersectionObserver` (threshold 0.6); it adds `.is-active`, which triggers that slide’s reveal animation.
- Speaker notes: `<aside class="notes">` inside each slide, never displayed; they travel with the file and can be extracted for a PPTX or a handout.
- Semantics: `<main class="deck">` + `<section class="slide" aria-label="Слайд N">`, real `h1`/`h2`, `lang="uk"` on `<html>`, alt text on images, contrast ≥ 4.5:1 for body text.
- Motion: one entrance style per deck; everything visible immediately under `prefers-reduced-motion: reduce`.

## 4. Fonts
Google Fonts via `<link>` with `display=swap` and only the weights used; Cyrillic-capable families only (`style-presets.md`). Offline delivery (no internet at the venue) → download the woff2 files into `assets/fonts/` next to the HTML and use `@font-face`; most Google Fonts families use the SIL Open Font License or Apache 2.0, both of which allow bundling — check the family’s licence page before shipping it.

## 5. PDF export
The template’s print block sets `@page { size: 1920px 1080px; margin: 0 }`, one `.slide` per page, backgrounds printed, motion off, chrome hidden, and no blank page after the last slide.
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/html-to-pdf.mjs" deck.html deliverables/docs/deck.pdf
```
Engine order: Playwright (when installed in the project), otherwise a local Chrome / Edge / Chromium in headless mode. No engine → the script prints how to get one (exit 3). Check the result: page count equals slide count (`python "${CLAUDE_PLUGIN_ROOT}/scripts/pdf-tools.py" info deck.pdf`), and look at 2–3 pages as images.

## 6. Converting an existing PPTX to HTML
1. Extract with python-pptx: for each slide, title (`slide.shapes.title`), text frames in order, tables, images (`shape.image.blob` → `assets/`), notes (`slide.notes_slide.notes_text_frame.text`).
2. Rebuild the story (one idea per slide) rather than copying the layout; keep the order and every number.
3. Apply a preset; carry notes into `<aside class="notes">`.
4. Report anything that could not be carried over (SmartArt, embedded video, animations).

## 7. Done when
- [ ] Zero overflowing slides at all check sizes.
- [ ] Keyboard, wheel and swipe each move exactly one slide; hash deep link works.
- [ ] Fonts render Cyrillic in the chosen face (no fallback glyphs).
- [ ] Reduced-motion mode shows everything.
- [ ] PDF has one page per slide, backgrounds included.
- [ ] Notes present for every content slide of a talk deck.
