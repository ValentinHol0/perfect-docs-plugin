---
name: docs-templates
description: "Ukrainian business document templates with required fields cited from zakon.rada.gov.ua — договір про надання послуг, договір поставки, рахунок на оплату, акт наданих послуг (виконаних робіт), видаткова накладна, комерційна пропозиція, звіт — with exact totals, VAT lines and amounts in words. Use when the user needs one of these documents filled in or a template for them; legal wording goes to perfect-legal, ФОП tax questions to perfect-business."
---

# Docs Templates — Ukrainian business documents

> **Harness:** written with Claude Code tool names. In Antigravity, translate with `${CLAUDE_PLUGIN_ROOT}/references/harness.md`.

This skill fills Ukrainian business documents correctly: every mandatory requisite present, every number computed by a script, every legal claim traceable to a source in `${CLAUDE_SKILL_DIR}/references/legal-basis.md`. It does not decide legal or tax questions.

| Reference | Use it for |
|---|---|
| `legal-basis.md` | Sources with status (verified / title verified / secondary / [Unverified]); the verify line |
| `primary-documents.md` | Invoice, act, waybill: field map to Law 996-XIV ст. 9, layout, JSON for `make-docx.py`, wording, typical errors |
| `contracts.md` | Services and supply contract skeletons, essential-terms checklist, numbering and consistency checks |
| `offer-and-report.md` | Commercial proposal and report structures |

## 1. Route the request
| Request | Output | How |
|---|---|---|
| «рахунок», invoice, «виставити рахунок» | DOCX (+ PDF on request) | `make-docx.py`, type `invoice` |
| «акт», «акт виконаних робіт», «акт наданих послуг» | DOCX | `make-docx.py`, type `act` (`act_kind`: `services` / `works`) |
| «видаткова накладна», «накладна» | DOCX | `make-docx.py`, type `waybill` |
| «договір надання послуг», «договір поставки» | DOCX | perfect-legal installed → its text, built into DOCX here; otherwise the skeleton from `contracts.md` + a brief for the legal sections |
| «комерційна пропозиція», «КП» | DOCX/PDF | `offer-and-report.md` + docs-docx (or docs-pdf for HTML → PDF) |
| «звіт» | DOCX (+ XLSX data) | `offer-and-report.md` + docs-docx; numbers via docs-xlsx |
| Податкова накладна, ПРРО receipt, tax return, ЄСВ | — | not this plugin → perfect-business |
| Public offer, privacy policy, terms for a site | — | perfect-legal |

## 2. Intake — collect before generating
Arriving from a sibling with prepared content (perfect-business drafts ФОП invoices and acts, perfect-legal drafts contract text): do not re-ask for what the brief contains — check its requisites against §4, compute the numbers here, build the file.
Otherwise ask in one message, only for what is missing; offer to read requisites from an existing contract, invoice or company card the user already has.
1. Document type, number, date (and period for an act).
2. Supplier/executor: full name with legal form, ЄДРПОУ or РНОКПП, address, IBAN and bank (invoice), tax status, signer’s position and «Власне ім’я ПРІЗВИЩЕ».
3. Buyer/customer: the same; for an act or contract also «в особі … що діє на підставі …» in the genitive.
4. Basis: contract number and date, or order.
5. Items: name, unit, quantity, price; currency (default UAH).
6. VAT: is the supplier a VAT payer, and are prices with or without VAT. **Always ask** — it changes the totals; never infer from the company type.
Rulings when the user does not answer: missing requisites become visible placeholders `[ЄДРПОУ покупця]` listed in the reply; never invent codes, IBANs, addresses, names or prices; date defaults to today only for invoices; numbering is the user’s, never guessed.

## 3. Build
1. Put the data into JSON following `primary-documents.md` §2 (examples: `${CLAUDE_PLUGIN_ROOT}/scripts/examples/*.json`). Save it next to the deliverable — it is the audit trail for the numbers.
2. Generate:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/make-docx.py" data.json "deliverables/docs/akt-27-2026-10-31.docx"
   ```
   The script validates requisites and the IBAN checksum, computes line sums, VAT and totals with Decimal, and gets the amount in words from `uah-words.mjs`. Report its `total`, `vat`, `words` and every warning.
3. Contracts, proposals, reports: build with docs-docx (or Anthropic’s `docx` skill in Claude Code) from the skeletons; any amount in the text → `node "${CLAUDE_PLUGIN_ROOT}/scripts/uah-words.mjs" <amount>`; tables of money → docs-xlsx or computed by a script.
4. PDF copy on request → docs-pdf (Word/LibreOffice export, or HTML → PDF).
5. Dispatch `docs-proofreader` (agent) for every document with money or legal effect before delivery; fix what it reports.

## 4. Rules that are not negotiable
- Mandatory requisites of a primary document (Law 996-XIV ст. 9): name of the document, date, name of the enterprise, content and volume of the operation with unit, positions of responsible persons, signature or other identification. Missing one → the script stops; do not work around it.
- Amount in words always produced by `uah-words.mjs`; it is a practice that protects against altered figures, not a requisite (Положення № 88 has no such rule — `legal-basis.md` row 2). Kopiyky as two digits («56 копійок») unless the user wants words.
- VAT wording matches the status: non-payer → «без ПДВ» everywhere; payer → «у тому числі ПДВ 20 %: …» or «ПДВ 20 %: …» + «Усього з ПДВ». Rates other than 20 % only when the user states the legal basis; check `legal-basis.md` row 10.
- Never cite the Господарський кодекс (lost force 28.08.2025). Contracts cite ЦК by article number and title.
- Electronic documents: signed with qualified electronic signatures (КЕП, e.g. via Дія.Підпис or a bank’s service); print the electronic-form line instead of «у двох примірниках».
- Language: documents for Ukrainian counterparties in Ukrainian; bilingual (UA/EN) contracts as a two-column table, Ukrainian prevails clause → perfect-legal confirms.
- File names: `<type>-<number>-<YYYY-MM-DD>.<ext>` in Latin (`rakhunok-104-2026-11-12.docx`, `akt-27-2026-10-31.docx`); deliverables in `deliverables/docs/` unless the user names a folder.

## 5. Handoffs
- Clause wording, penalties, jurisdiction, contract review, risk of a ФОП contract looking like employment → perfect-legal: Claude Code skill `perfect-legal-plugin:legal` / Antigravity skill `legal`. Not installed → write `.planning/handoff-docs-to-legal.md` (document, parties, purpose, the clauses needing wording, deadline) and tell the user.
- ФОП group and limits, VAT registration, податкова накладна, ПРРО, bookkeeping → perfect-business (`perfect-business-plugin:business` / `business`). Not installed → `.planning/handoff-docs-to-business.md`.
- Automatic generation from a CRM, a web form or a site → the core (`/absolute`) via `.planning/handoff-docs.md`.

## 6. Output
Reply in the user’s language:
```
Файл: deliverables/docs/akt-27-2026-10-31.docx (+ data: akt-27-2026-10-31.json)
Сума: 27 345,56 грн, без ПДВ — «Двадцять сім тисяч триста сорок п’ять гривень 56 копійок»
Перевірено: реквізити (ст. 9 Закону № 996-XIV), підсумки, сума прописом, типографіка — docs-proofreader: OK
Відкриті пункти: [ЄДРПОУ замовника] — потрібне значення
Перевірте з юристом / бухгалтером перед використанням: норми змінюються, а цей документ не є юридичною чи податковою консультацією.
```
