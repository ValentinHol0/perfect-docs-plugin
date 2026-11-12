---
name: pptx
description: "Shortcut for a presentation — PowerPoint (PPTX) or HTML slide deck with speaker notes. Loads the office entry skill of perfect-docs."
disable-model-invocation: true
argument-hint: "[what presentation]"
---

# /pptx

Shortcut. Load the `office` skill and follow it fully for this request, treating it as a presentation task (PPTX or HTML deck) (route to `docs-pptx`):

$ARGUMENTS

- Claude Code: invoke the Skill tool with `perfect-docs-plugin:office`. If Anthropic's own `pptx` skill is also listed, `office` tells you how to combine them.
- Antigravity / other harnesses: read `../office/SKILL.md` (relative to this file) with the file-read tool and follow it.
