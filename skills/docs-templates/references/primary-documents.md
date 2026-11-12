# Invoice, act, waybill — fields, layout, JSON for `make-docx.py`

Sources: rows 1, 2, 10–13 of `legal-basis.md`. Field → requisite mapping below is how this plugin satisfies Law 996-XIV ст. 9; the law fixes the requisites, not a form, so the layout is a house standard.

## 1. Which document
| Document | Role | Primary document? | Signed by |
|---|---|---|---|
| Рахунок на оплату | asks for payment; carries bank details | No (payment document) — see `legal-basis.md` row 11 | supplier (practice; not required) |
| Акт приймання-передачі наданих послуг / здачі-приймання виконаних робіт | confirms services/works were delivered and accepted | Yes | both parties |
| Видаткова накладна | confirms goods were handed over | Yes | both parties (shipped by / received by) |

Rule: every completed sale needs a primary document (act for services/works, waybill for goods). An invoice alone is not enough evidence of the operation.

## 2. Field map (all three)
| Field (JSON key) | Requisite it covers | Notes |
|---|---|---|
| `type`, `number`, title | назва документа | Numbering: continuous per year or per counterparty; never reuse a number |
| `date` (YYYY-MM-DD) | дата складання | Printed word-numeric: «31 жовтня 2026 р.» (KMU 55 п. 32 practice for financial content) |
| `supplier.name`, `buyer.name` | назва підприємства | ТОВ: full name with legal form «ТОВ «Приклад Трейд»»; ФОП: «Фізична особа — підприємець Іваненко Олена Петрівна» |
| `supplier.code`, `buyer.code` | additional requisite (identification code) | 8 digits → «код ЄДРПОУ»; 10 digits → «РНОКПП»; other identifiers → set `code_label` |
| `items[]` name, unit, qty, price | зміст та обсяг операції, одиниця виміру | Name specific enough to identify the service/good; units: послуга, год, шт, пач., кг, м², міс. |
| `signer_position`, `signer` | посади відповідальних осіб, підпис / ідентифікація | «Директор», «Петро ПЕТРЕНКО» (Власне ім’я ПРІЗВИЩЕ); for ФОП position «Фізична особа — підприємець» |
| `basis` | additional | «Договором про надання послуг № 7 від 01.09.2026» (act, in instrumental case after «згідно з»); «Договір поставки № 15/26 від 02.02.2026» (invoice/waybill) |
| `supplier.iban`, `bank` | payment details | Required on invoices; validated UA + 27 digits, mod-97 |
| `tax_status` | — | «Платник ПДВ» / «Платник єдиного податку 3 групи, неплатник ПДВ» — confirm with perfect-business or the client; never guess |
| `vat.mode`, `vat.rate` | — | `none` (prints «без ПДВ»), `on_top` (VAT added to the line sum), `included` (VAT = total × rate / (100 + rate)); rounding ROUND_HALF_UP to kopiyky |
| `place` | additional (act, waybill) | «м. Київ» |
| `period` | act | «жовтень 2026 р.» |
| `electronic` | act | true → «складено в електронній формі та підписано КЕП сторін»; else «у двох примірниках» |
| `represented_by` | act preamble | «в особі директора Петренка Петра Петровича, що діє на підставі Статуту» — genitive forms are typed by a person, never auto-generated |
| `due_date`, `payment_purpose` | invoice | Purpose default: «Оплата за рахунком № 104 від 12.11.2026, у тому числі ПДВ 1 891,00 грн» |
| `seal` | — | true prints «М. П.»; печатка is optional for most businesses — include only if the client uses one |
| `total_words` | — | Optional; if given it must equal the computed words or the script stops |

## 3. Layout (house standard, A4)
1. Title centred, bold 14 pt: «Рахунок на оплату № 104 від 12 листопада 2026 р.» / «АКТ № 27» + subtitle / «Видаткова накладна № 88 від …».
2. Parties block (two-column, borderless): label in bold, details on separate lines: name, code, address, IBAN + bank, tax status.
3. Items table: № · Найменування · Од. · Кількість · Ціна, грн · Сума, грн. Header row repeats on every page; rows never split; numbers right-aligned with no-break thousands spaces and decimal comma «15 000,00».
4. Totals right-aligned: VAT lines per mode.
5. «Усього найменувань 3, на суму 27 345,56 грн.» then «Сума прописом: Двадцять сім тисяч триста сорок п’ять гривень 56 копійок, без ПДВ.»
6. Act: closing statement (no claims), copies line. Invoice: validity date, payment purpose.
7. Signatures side by side: heading («Від Виконавця:» / «Від Замовника:»; «Від постачальника:» / «Від покупця:»), position, action for waybills («Відвантажив(ла)», «Отримав(ла)»), line + name.
Margins default 20/10/20/30 mm (top/right/bottom/left) — the KMU 55 blank margins, so a document can be filed in a binder.

## 4. Generate
```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/make-docx.py" data.json deliverables/docs/akt-27-2026-10-31.docx
```
Examples to copy: `${CLAUDE_PLUGIN_ROOT}/scripts/examples/act.json`, `invoice.json`, `waybill.json`. The script prints a JSON summary — quote its `total`, `vat` and `words` in the reply; never retype them.
Errors stop the script (exit 1): missing code/name/items, bad IBAN, missing signer on an act or waybill, `total_words` mismatch. Warnings (missing positions, basis, buyer code) are listed in the summary — resolve or report each one.
Without python-docx: the script prints `pip install python-docx`. In Claude Code with Anthropic's `docx` skill, build the same layout through that skill and still take totals from `make-docx.py`-equivalent arithmetic: run `node "${CLAUDE_PLUGIN_ROOT}/scripts/uah-words.mjs" <total>` for words.

## 5. Ready-to-use wording (Ukrainian)
- Act preamble (services): «… (далі — Виконавець), з однієї сторони, та … (далі — Замовник), з іншої сторони, склали цей акт про те, що Виконавець надав, а Замовник прийняв такі послуги згідно з Договором … за жовтень 2026 р.:»
- Act closing: «Послуги надано в повному обсязі, у встановлені строки та належної якості. Замовник претензій щодо обсягу, якості та строків не має.»
- Act with remarks (do not force «претензій не має» when the client has remarks): «Замовник має такі зауваження: … Сторони домовилися усунути їх до …»
- Invoice footer: «Рахунок дійсний до 19 листопада 2026 р.»
- Electronic: «Документ складено в електронній формі та підписано кваліфікованими електронними підписами сторін.»

## 6. Errors that make a document bad
- Total in words ≠ figures; VAT line inconsistent with the VAT status in the parties block.
- A non-VAT payer shows «ПДВ 20 %» — or a VAT payer prints «без ПДВ» for a taxable supply → perfect-business.
- Act dated before the services period ends; waybill dated before the goods left; act number reused.
- Signer name in a different form in the act and in the contract; position missing.
- Unit «послуга» with qty 12.5 (fractional services) — use «год».
- Corrections in a signed paper document without «виправлено» and both signatures (Положення № 88 п. 4.7).
