# Perfect Docs (Perfect Suite addon) — always-on rule (Antigravity)

Office documents that look professional: DOCX, XLSX, PPTX and PDF, Ukrainian business templates (contracts, invoices, acts, commercial proposals, reports), spreadsheets with formulas and presentations. Entry: `/office` (shortcuts `/docx`, `/xlsx`, `/pptx`, `/pdf`).
- Skills: `office` (entry, routing) · `docs-docx` · `docs-xlsx` · `docs-pptx` · `docs-pdf` · `docs-templates`. Agent: `docs-proofreader`.
- Skills are written with Claude Code tool names; translate with `references/harness.md` (in this plugin's folder): Read→view_file · Grep→grep_search · Edit→replace_file_content · Write→write_to_file · Bash→run_command · WebFetch→read_url_content · WebSearch→search_web · Agent→invoke_subagent (fallback: follow agents/<name>.md inline) · Skill→view_file the SKILL.md.
- `${CLAUDE_PLUGIN_ROOT}` = this plugin's folder; `${CLAUDE_SKILL_DIR}` = the folder of the SKILL.md you follow. Not substituted here — resolve them yourself.
- Totals, VAT and amounts in words come from `scripts/` (uah-words.mjs, make-docx.py), never from mental arithmetic.
- Reply in the user's language; never invent facts, figures or legal provisions — cite or mark [Unverified].
- Code, sites and apps go to the core: write `.planning/handoff-docs.md` and run `/absolute` if perfect-programming-plugin is installed.
