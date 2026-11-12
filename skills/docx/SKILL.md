---
name: docx
description: "Shortcut for a Word (DOCX) document — letter, order, contract, report, invoice or act — with Ukrainian typography and templates. Loads the office entry skill of perfect-docs."
disable-model-invocation: true
argument-hint: "[what document]"
---

# /docx

Shortcut. Load the `office` skill and follow it fully for this request, treating it as a Word (DOCX) task (route to `docs-docx`):

$ARGUMENTS

- Claude Code: invoke the Skill tool with `perfect-docs-plugin:office`. If Anthropic's own `docx` skill is also listed, `office` tells you how to combine them.
- Antigravity / other harnesses: read `../office/SKILL.md` (relative to this file) with the file-read tool and follow it.
