---
name: pdf
description: "Shortcut for PDF work — create from HTML or DOCX, fill a form, merge, split, extract text or tables. Loads the office entry skill of perfect-docs."
disable-model-invocation: true
argument-hint: "[what PDF work]"
---

# /pdf

Shortcut. Load the `office` skill and follow it fully for this request, treating it as a PDF task (route to `docs-pdf`):

$ARGUMENTS

- Claude Code: invoke the Skill tool with `perfect-docs-plugin:office`. If Anthropic's own `pdf` skill is also listed, `office` tells you how to combine them.
- Antigravity / other harnesses: read `../office/SKILL.md` (relative to this file) with the file-read tool and follow it.
