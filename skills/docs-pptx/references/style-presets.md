# HTML deck style presets (Cyrillic-safe)

Twelve directions for HTML slide decks. Every font below includes Cyrillic (checked 2026-11-12 against `https://fonts.google.com/metadata/fonts`, field `subsets`). Contrast ratios are WCAG 2.x values computed for the listed hex pairs: ink and muted are safe for body text (≥ 4.5:1); accents are for headings, figures, rules and shapes.

Many popular presentation fonts have **no Cyrillic** — Space Grotesk, Syne, Outfit, Fraunces, DM Sans, Work Sans, Plus Jakarta Sans, Bodoni Moda, Archivo (same metadata check). Ukrainian text set in them falls back to a system face letter by letter. Never use them for Ukrainian decks.

A preset is one token block (`:root { --bg … --font-body }`) dropped into `../assets/deck-template.html`, plus its signature move. Pick by the feeling the audience should leave with:

| Feeling | Presets |
|---|---|
| Confidence, «we mean business» | Signal, Studio Cobalt, Nocturne |
| Energy, novelty | Voltage, Neon Grid, Duo Tone |
| Calm focus, trust in numbers | Ledger, Swiss, Manuscript |
| Warmth, approachability | Soft Geometry, Magazine, Duo Tone |
| Engineering credibility | Terminal, Neon Grid, Swiss |

## Catalogue
| # | Preset | Best for | Display / body font | bg · ink · muted · accent | Contrast ink / muted / accent | Signature move |
|---|---|---|---|---|---|---|
| 1 | **Signal** | pitches, launches, keynotes | Unbounded 700 / Onest 400 | `#16181d` · `#f3f1ec` · `#a3a7b0` · `#ff5a1f` | 15.7 / 7.4 / 5.7 | huge section numerals; one bright orange card per slide on the dark field |
| 2 | **Studio Cobalt** | client presentations, strategy reviews | Manrope 800 / Manrope 400 | `#ffffff` · `#111111` · `#5b6170` · `#1f4fff` | 18.9 / 6.2 / 5.8 | two-panel split (statement left, evidence right), hairline rules, sharp left alignment |
| 3 | **Voltage** | creative studios, product stories | Montserrat Alternates 700 / Onest 400; labels JetBrains Mono | `#0b1530` · `#f5f7ff` · `#a9b4d6` · `#e8ff3a` | 16.9 / 8.7 / 16.1 | badge labels in mono caps, halftone dots from `radial-gradient`, punchy yellow on navy |
| 4 | **Nocturne** | premium brands, considered narratives | Cormorant Garamond 600 / IBM Plex Sans 400 | `#121110` · `#efe8dc` · `#a39d92` · `#c9a45c` | 15.5 / 7.0 / 8.0 | blurred soft circles (`filter: blur`), thin gold rules, slow fades |
| 5 | **Ledger** | reports, reviews, structured stories | Literata 700 / Source Sans 3 400 | `#f6f1e7` · `#22211f` · `#6b665d` · `#a24a24` | 14.3 / 5.1 / 5.3 | paper sheet on a charcoal frame with coloured index tabs per section |
| 6 | **Soft Geometry** | onboarding, product overviews, training | Nunito 800 / Nunito 400 | `#eef4fc` · `#1d2a3a` · `#56657a` · `#2f62c9` | 13.1 / 5.4 / 5.1 | rounded cream cards, pill tags, soft shadows, pastel mint/pink side accents |
| 7 | **Duo Tone** | workshops, agency intros, portfolios | Jost 700 / Jost 400 | `#fff4ee` · `#2a2233` · `#6b6075` · `#5f3fd6` | 14.1 / 5.5 / 6.1 | split background (peach `#ffd9c7` / lavender `#ddd4ff`, ink stays ≥ 10.9:1 on both), mint tags |
| 8 | **Magazine** | opinionated talks, personal brands | Playfair Display 800 / Golos Text 400 | `#f7f2ea` · `#1f1c1a` · `#6e665e` · `#b0413e` | 15.2 / 5.1 / 5.1 | big serif headlines, bordered call-out boxes, drop-cap first slide |
| 9 | **Neon Grid** | AI, infrastructure, future-of-X | Tektur 700 / Inter 400 | `#0a0e1f` · `#e8ecff` · `#8d96c2` · `#22d3ee` | 16.3 / 6.6 / 10.6 | background grid lines, cyan glow on key numbers (secondary accent `#f0abfc`) |
| 10 | **Terminal** | APIs, CLI tools, engineering demos | JetBrains Mono 700 / JetBrains Mono 400 | `#0d1117` · `#e6edf3` · `#8b949e` · `#3fb950` | 16.0 / 6.2 / 7.4 | prompt-style headings (`$ deploy --prod`), monospaced rhythm, subtle scan lines |
| 11 | **Swiss** | corporate, analytics, product strategy | Inter Tight 800 / Inter 400 | `#ffffff` · `#0f0f0f` · `#5f5f5f` · `#e30613` | 19.2 / 6.4 / 4.9 | visible 12-column grid, asymmetric placement, red used once per slide |
| 12 | **Manuscript** | essays, manifestos, keynote narratives | EB Garamond 600 / Source Serif 4 400 | `#f8f4ec` · `#1e1b18` · `#6a625a` · `#9b1c31` | 15.6 / 5.5 / 7.4 | pull quotes, drop caps, elegant rules, generous margins |

Default when the user has no preference and no brand: **Ledger** for reports and internal decks, **Signal** for pitches, **Swiss** for numbers-heavy reviews. With a brand: take the brand’s colours and fonts (check their Cyrillic) and keep only the preset’s layout move.

## Motion by feeling
| Feeling | Motion |
|---|---|
| Professional | 200–300 ms fades and 12–16 px rises; nothing else |
| Dramatic | slower fades (500–700 ms), large scale-in on the key figure only |
| Playful | spring-like easing, small rotations on tags |
| Technical | text that types or scrambles once on the title; grid shimmer |
| Calm | almost none; whitespace does the work |
Every motion sits behind `prefers-reduced-motion: no-preference`; with reduced motion, content is simply visible.

## Showing options without a questionnaire
When the user cannot name a style, build **three single-slide previews** (title slide of their actual deck in three presets that fit the feeling) as separate HTML files in `.planning/deck-previews/`, show them (screenshots via the browser tool, or open locally) and let the user pick or mix («шрифти з 2, кольори з 5»). Delete previews after the choice unless asked to keep them.
