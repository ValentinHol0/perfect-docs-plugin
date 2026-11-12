# Contract skeletons — договір про надання послуг, договір поставки

These are **structures with placeholders**, not legal advice. The docs plugin owns layout, numbering, requisites and consistency; the wording of obligations, liability, penalties, force majeure and disputes belongs to **perfect-legal** (`/legal`) when installed, and to a lawyer in every case. Every contract deliverable ends with the verify line from `legal-basis.md`.

Never cite the Господарський кодекс in a new contract — it lost force on 28.08.2025 (`legal-basis.md` row 9). Cite the Цивільний кодекс articles listed there, and only by number and title unless you have checked the current text.

## 1. Essential terms first (ЦК ст. 638)
A contract is concluded only when the parties agree on all essential terms: the subject, the terms the law makes essential or necessary for that type, and any term either party insists on. Before drafting, fill this checklist; a blank row is a question to the user, not a placeholder to hide.

| Term | Services | Supply |
|---|---|---|
| Subject | which services, result or activity, volume | goods: name, assortment, quantity, quality/standard |
| Price | rate or fixed price, currency, with/without VAT | unit prices or specification, with/without VAT |
| Payment | prepayment %, term in banking days after act/invoice | prepayment / deferral, term after the waybill |
| Term | start, end, stages | delivery dates or schedule |
| Acceptance | act within N working days; silence rule | acceptance by quantity and quality, the waybill, defects procedure |
| Delivery | — | place, who pays carriage (e.g. Nova Poshta at the buyer’s expense), transfer of ownership and risk |
| Liability | → perfect-legal | → perfect-legal |

## 2. Numbering and form rules (docs-docx applies)
- Sections «1. ПРЕДМЕТ ДОГОВОРУ» (caps or bold, consistent), clauses «1.1.», sub-clauses «1.1.1.»; cross-references by number («п. 4.2 Договору»), checked after every insertion.
- Defined terms once, in the preamble or section 1: «(далі — Договір)», «(далі — Виконавець)»; then always capitalised the same way.
- Money: figures and words — «15 000,00 грн (п’ятнадцять тисяч гривень 00 копійок), без ПДВ» — words from `uah-words.mjs`.
- Dates word-numeric in the text («01 вересня 2026 р.»); term end stated as a date, not «через рік».
- Last section «Реквізити та підписи сторін» as a two-column borderless table: name, address, code, IBAN, bank, tax status, signer position, «__________ Власне ім’я ПРІЗВИЩЕ».
- Page numbers «Сторінка X з Y»; a paper contract longer than one page: initials of both signers on each page (practice).

## 3. Договір про надання послуг — skeleton
```
ДОГОВІР № [номер]
про надання послуг

м. [місто]                                                    [дата словами] р.

[Повне найменування Замовника], в особі [посада, ПІБ у родовому відмінку], що діє на підставі [Статуту / довіреності № … від …] (далі — Замовник), з однієї сторони, та [ФОП ПІБ / найменування Виконавця] (далі — Виконавець), з іншої сторони (далі разом — Сторони), уклали цей договір (далі — Договір) про таке:

1. ПРЕДМЕТ ДОГОВОРУ
1.1. Виконавець зобов’язується за завданням Замовника надати послуги з [опис], а Замовник зобов’язується прийняти та оплатити ці послуги.
1.2. Обсяг, строки та вартість послуг визначаються [у цьому Договорі / у Додатку № 1 — Технічне завдання].
2. ВАРТІСТЬ ПОСЛУГ І ПОРЯДОК РОЗРАХУНКІВ
2.1. Вартість послуг становить [сума цифрами] грн ([сума словами]), [без ПДВ / у тому числі ПДВ …].
2.2. Оплата: [передоплата …% протягом … банківських днів з дати рахунку; решта — протягом … банківських днів з дати підписання акта].
3. ПОРЯДОК НАДАННЯ ТА ПРИЙМАННЯ ПОСЛУГ
3.1. Строк надання послуг: з [дата] до [дата].
3.2. Факт надання послуг підтверджується актом приймання-передачі наданих послуг. Замовник протягом [N] робочих днів підписує акт або надає мотивовані зауваження.
4. ПРАВА ТА ОБОВ’ЯЗКИ СТОРІН            [зміст — perfect-legal / юрист]
5. ВІДПОВІДАЛЬНІСТЬ СТОРІН             [зміст — perfect-legal / юрист]
6. ФОРС-МАЖОР                          [зміст — perfect-legal / юрист]
7. ВИРІШЕННЯ СПОРІВ                    [зміст — perfect-legal / юрист]
8. СТРОК ДІЇ ДОГОВОРУ
8.1. Договір набирає чинності з моменту підписання і діє до [дата], а в частині розрахунків — до їх повного виконання.
9. ІНШІ УМОВИ
9.1. Договір складено [у двох примірниках, що мають однакову юридичну силу / в електронній формі та підписано КЕП Сторін].
10. РЕКВІЗИТИ ТА ПІДПИСИ СТОРІН
```

## 4. Договір поставки — skeleton (differences only)
```
1. ПРЕДМЕТ ДОГОВОРУ
1.1. Постачальник зобов’язується передати у власність Покупця товар (далі — Товар), а Покупець — прийняти та оплатити його на умовах цього Договору.
1.2. Найменування, асортимент, кількість і ціна Товару визначаються у Специфікаціях або видаткових накладних, які є невід’ємною частиною Договору.
2. ЯКІСТЬ ТОВАРУ                       [стандарт / ТУ / сертифікати; порядок претензій — юрист]
3. ЦІНА ТА ПОРЯДОК РОЗРАХУНКІВ
4. ПОСТАВКА ТА ПРИЙМАННЯ
4.1. Поставка здійснюється [самовивозом зі складу … / перевізником (Нова пошта) за рахунок …] протягом [N] днів з [дати оплати / замовлення].
4.2. Право власності та ризик випадкового знищення переходять до Покупця з моменту [підписання видаткової накладної / передачі перевізнику — юрист].
4.3. Приймання за кількістю — під час отримання; за якістю — протягом [N] днів.
5–8. ВІДПОВІДАЛЬНІСТЬ / ФОРС-МАЖОР / СПОРИ / СТРОК ДІЇ   [зміст — perfect-legal / юрист]
9. РЕКВІЗИТИ ТА ПІДПИСИ СТОРІН
```
Specification (Додаток № 1): table № · Товар · Од. · Кількість · Ціна без ПДВ · Сума; totals and VAT exactly as in `primary-documents.md`; signed by both parties.

## 5. Consistency checks before delivery
- Party names, codes and signers identical in preamble, requisites, acts and invoices.
- Every number that appears twice (price, term, %, days) is the same everywhere; figures match words.
- Every «Додаток № N» mentioned exists and is titled the same way.
- No clause cites ГК; every ЦК citation matches `legal-basis.md`.
- Placeholders `[…]` left → listed in the reply as open items, never silently delivered.
