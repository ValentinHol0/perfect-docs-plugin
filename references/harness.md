# Harness Adapter — Claude Code ⇄ Antigravity

PPP skills are written once. Skill text names Claude Code tools; this table gives the Antigravity equivalent. Detect the harness from your tool list: `Read` / `Agent` / `Skill` → **Claude Code**; `view_file` / `invoke_subagent` / `run_command` → **Antigravity**.

## Paths
| Placeholder in skill text | Claude Code | Antigravity |
|---|---|---|
| `${CLAUDE_SKILL_DIR}` | substituted automatically | the folder containing the SKILL.md you are following |
| `${CLAUDE_PLUGIN_ROOT}` | substituted in a SKILL.md the harness loaded | the plugin root = two folders above any `skills/<name>/SKILL.md`; locate it (commonly under `~/.gemini/config/plugins/` or `<workspace>/.agents/plugins/`) — don't assume |
| `PLUGIN_ROOT=<path>` in subagent prompts | pass `${CLAUDE_PLUGIN_ROOT}` | pass the absolute plugin root resolved above |
Placeholders are substituted only in a SKILL.md body the harness loaded. Files you open yourself (references, templates, agent files) always show them literally — in either harness. Detect the harness from the tool list, never from placeholders. Before running a command copied from a file, replace `${CLAUDE_PLUGIN_ROOT}` with the PLUGIN_ROOT recorded in the Run header (`SESSION-STATE.md`); a literal placeholder expands to an empty string in a shell.

## Tools
| Action | Claude Code | Antigravity |
|---|---|---|
| Read a file | `Read` | `view_file` |
| Search file contents | `Grep` | `grep_search` (semantic: `codebase_search`) |
| Find files | `Glob` | `find_by_name`, `list_dir` |
| Edit a file | `Edit` | `replace_file_content` / `multi_replace_file_content` |
| Create a file | `Write` | `write_to_file` |
| Run a command | `Bash` | `run_command` |
| Long-running command | `Bash` with `run_in_background` (you are notified) | `run_command` in background + `command_status` / `read_terminal` |
| Fetch a URL | `WebFetch` (or the `web-fetch` agent) | `read_url_content` |
| Search the web | `WebSearch` | `search_web` |
| Drive a browser / screenshots | built-in browser pane `mcp__Claude_Browser__*` (navigate, resize_window, screenshot, read_console_messages, javascript_tool) or Claude in Chrome | `browser_subagent` |
| Generate an image | `gen-image.mjs` from a plugin that ships it (the core and perfect-brand): `node "<that plugin's root>/scripts/gen-image.mjs" --out <file> --prompt "…"` — Gemini through the user's Antigravity CLI when installed; else an image MCP; else a CSS/SVG composition | `generate_image` |
| Load a skill | `Skill` tool: `perfect-programming-plugin:<skill>` | `view_file <PLUGIN_ROOT>/skills/<skill>/SKILL.md` and follow it (slash commands are typed by the user, not the model) |
| Dispatch a subagent | `Agent` tool, `subagent_type: "perfect-programming-plugin:<agent>"`, optional `model`, `isolation: "worktree"` | `invoke_subagent` with the agent name (e.g. `absolute-reviewer`) when it is in your tool list. **Fallback:** run the role inline — `view_file <PLUGIN_ROOT>/agents/<agent>.md`, follow it using only the brief/package as input, write the report to `.planning/reports/`. No worktree isolation → run write tasks sequentially. |
| Parallel subagents | several `Agent` calls in one message | several `invoke_subagent` calls in one response |
| Continue a subagent | `SendMessage` to its id | re-dispatch with the previous report attached |
| Ask the user | `AskUserQuestion` (1–4 questions, options) | `notify_user`; if neither exists, ask in plain text and end the turn |
| Task list / progress | the app's plan tool (`update_plan`) or `TodoWrite` | a task artifact: `write_to_file` with `IsArtifact: true`, `ArtifactType: "task"`; keep it updated |
| Plan document | `.planning/ROADMAP.md` | `.planning/ROADMAP.md`, mirrored as an implementation-plan artifact (`ArtifactType: "implementation_plan"`) so the user can review it |
| Final report | chat message | a walkthrough artifact (`ArtifactType: "walkthrough"`) + short chat summary |
| Destructive-command guard | the core's PreToolUse hook (`guard.js`) turns broad deletes, history rewrites, DB drops, teardown, publish/deploy and pipe-to-shell into an approval prompt | no hooks — the always-on rule says: ask before any destructive or outward command |
| State after compaction | SessionStart hook re-injects `SESSION-STATE.md`, `memory/working-buffer.md`, `.planning/STATE.md` | `rules/AGENTS.md` tells you to read those files before continuing |

## Models
| Tier | Claude Code `model` | Antigravity model |
|---|---|---|
| Cheap / mechanical | `haiku` | `flash_lite` |
| Standard | `sonnet` | `flash` |
| Strongest (fix rounds 4–5, hard architecture) | `opus` | `pro` |
| Same as session | `inherit` | `inherit` |
Agent files declare `model: inherit` (valid in both). Choose tiers at dispatch time when the harness lets you; precedence and per-role defaults: `pipelines.md` 0.7. [Unverified] Whether Antigravity's `invoke_subagent` accepts a per-call model — if not, the agent runs on the session model.

## Differences to remember
- Antigravity loads only the first 24,000 bytes of a SKILL.md body — keep long material in `references/`.
- Antigravity has no plugin slash commands; PPP shortcuts (`/design`, `/scout`, …) are skills with `disable-model-invocation: true`, so users can type them as `/name` in both.
- Claude Code reads `.claude-plugin/plugin.json` (hooks inline); Antigravity reads `.antigravity-plugin/plugin.json` and `rules/AGENTS.md`.
- Git, Node scripts (`scripts/*.mjs|js`) and file layouts are identical in both.
