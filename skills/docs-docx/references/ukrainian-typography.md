# Ukrainian typography for documents

Orthography follows the «Український правопис» (2019 norms; since 28.03.2026 issued as a standard of the Національна комісія зі стандартів державної мови — `docs-templates/references/legal-basis.md` row 16). The typographic rules below (no-break spaces, dash lengths) are established publishing practice, not law; apply them consistently.

## 1. Characters
| Need | Use | Unicode | Never |
|---|---|---|---|
| Quotes | «ялинки»; inner „лапки“ | « U+00AB » U+00BB „ U+201E “ U+201C | "straight", “English” as the outer pair |
| Apostrophe | п’ять, м’ята, Мар’яна | ’ U+2019 (default) | ' U+0027 in a finished document; ` or ´; mixing two kinds in one file |
| Dash (тире) | Київ — столиця; «далі — Договір» | — U+2014 with spaces (left one no-break) | hyphen or en dash as a sentence dash |
| Range | 2025–2026, 10–15 %, с. 4–7 | – U+2013, no spaces | hyphen |
| Hyphen | будь-який, північно-західний, ПДВ-накладна | - U+002D | dash |
| Number sign | № 27, №№ 3–5 | № U+2116 + no-break space | «N 27», «#27» |
| Minus | −5 °C | − U+2212 | hyphen |
| Ellipsis | … | U+2026 | three dots in display text |

The modifier-letter apostrophe ʼ (U+02BC) is preferred by some guides because software treats it as a letter; choose one apostrophe per document. Systems that only accept ASCII (some bank payment purposes, legacy accounting imports) get `'` — `uah-words.mjs --apostrophe ascii`.

## 2. No-break spaces (U+00A0)
Put a no-break space so these never split across lines:
- number + unit or currency: 15 000 грн, 37 %, 12,5 год, 20 мм, 1,8 млн ₴
- thousands groups: 1 234 567,89 (Ukrainian: space groups, decimal comma)
- № and §: № 27, § 5
- date parts: 31 жовтня 2026 р.; 12.11.2026 never breaks anyway
- abbreviations and what they belong to: м. Київ, вул. Хрещатик, буд. 1, кв. 5, ст. 9, п. 2.3, ч. 2, т. ч., ім. Шевченка
- initials and surname: О. П. Іваненко; name and surname in signatures: Олена ІВАНЕНКО
- before a dash: «Договір — це…»
- after one-letter words at a line start (optional in body text, required in headings): в, у, з, і, й, а, о
In Word: Ctrl+Shift+Space; in python-docx: the character `"\u00a0"`; in HTML: `&nbsp;` or the literal character.

## 3. Numbers, money, dates
- Decimal comma: 12,5; thousands with a no-break space from 10 000 (four-digit numbers may stay unspaced: 2026, 1500 — be consistent within a table).
- Money in text: «15 000,00 грн (п’ятнадцять тисяч гривень 00 копійок)»; in tables only figures with the unit in the header «Сума, грн». «₴» for marketing and slides; «грн» in documents.
- Abbreviations in common use: грн, тис., млн, млрд, коп., р. (рік), рр., ст., п., ч.; no period after грн, млн, млрд.
- Dates: numeric 12.11.2026 (day and month two digits) or word-numeric «12 листопада 2026 р.» / «року» (KMU 55 п. 32; word-numeric for financial content). Never 12/11/2026 or 2026-11-12 in a Ukrainian document body.
- Time: 09:30 or 9 год 30 хв.
- Percent: 37 %; percentage points: «на 3 в. п.» (відсоткові пункти).
- Ordinal with a number: 3-й квартал, 1-го числа, у 2026 році.

## 4. Words that business documents get wrong
| Write | Not | Why |
|---|---|---|
| згідно з договором / відповідно до договору | згідно договору | preposition required |
| у тому числі (у т. ч.) | в тому числі ПДВ as «в т.ч.» without spaces | spacing + abbreviation |
| Усього / Разом at the start of a line | Всього | у/в alternation before a consonant |
| наданих послуг, виконаних робіт | оказаних послуг | calque |
| рахунок на оплату, рахунок-фактура | счет | — |
| протягом 5 банківських днів | на протязі | calque |
| підписання акта | підписання акту | genitive -а for a document |
| найменування (організації, товару) | наіменування | spelling |
| ПІБ → «власне ім’я, прізвище, по батькові» in forms | ФІО | — |

## 5. Names and positions
- Signature blocks (ДСТУ 4163:2020 practice; KMU 55 п. 49): position on the first line, then signature line and «Власне ім’я ПРІЗВИЩЕ» — «Олена ІВАНЕНКО».
- In contract preambles names stay in full in the genitive: «в особі директора Петренка Петра Петровича». Never auto-decline names — ask or copy from an existing document.
- Positions with a lower-case letter inside a sentence: «директор», «головний бухгалтер»; capitalised only at the start of a signature line.
- Company names: legal form + name in quotes: ТОВ «Приклад Трейд»; nested quotes are not doubled: ТОВ «Компанія «Схід»».

## 6. Automated check (what the proofreader runs)
Search the document text for these patterns and fix each hit:
- `"` or `'` between letters → wrong quotes/apostrophe
- ` - ` (space-hyphen-space) → dash
- `\d \d{3}` with a normal space inside numbers → no-break space
- `\d(%|грн)` without a space, or with a normal space → no-break space
- `  ` (double space), space before `,` `.` `:` `;`
- `N\s?\d` used as a number sign → №
- Latin look-alikes inside Cyrillic words (a, c, e, i, o, p, x, y, B, H, K, M, T) → retype; they break search and spellcheck
