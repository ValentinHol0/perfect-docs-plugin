---
name: xlsx
description: "Shortcut for an Excel (XLSX) spreadsheet with live formulas, UAH formats, validation and charts. Loads the office entry skill of perfect-docs."
disable-model-invocation: true
argument-hint: "[what spreadsheet]"
---

# /xlsx

Shortcut. Load the `office` skill and follow it fully for this request, treating it as an Excel (XLSX) task (route to `docs-xlsx`):

$ARGUMENTS

- Claude Code: invoke the Skill tool with `perfect-docs-plugin:office`. If Anthropic's own `xlsx` skill is also listed, `office` tells you how to combine them.
- Antigravity / other harnesses: read `../office/SKILL.md` (relative to this file) with the file-read tool and follow it.
