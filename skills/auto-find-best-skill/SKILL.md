---
name: auto-find-best-skill
description: Turn on or off a session hook that makes Claude Code check the installed skills for the best match before every task, and search with find-skills only when none fits. Use when the user types /auto-find-best-skill or asks to pick skills automatically in every session.
---

# Auto find best skill

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/auto-find-best-skill on|off|status`. With no argument, treat it as `on`.

This works in Claude Code only, because it uses a session hook. In another agent, say that and stop.

## Steps
1. Run `python3 <skill-dir>/scripts/toggle.py <on|off|status>`. It edits only the SessionStart hook in `~/.claude/settings.json`, keeps every other setting and hook, and keeps a one-time copy of the original file next to it.
2. If it exits with an error (for example the settings file is not valid JSON), tell the user in one line and stop. Do not edit the file by hand.
3. Reply with the line it printed, for example `auto-find-best-skill: on`. After `on`, add that it applies from the next session, and follow the rule below for the rest of this one.

## The rule while it is on
- Before starting a task, look at the available skills list and pick the one whose description fits best. Prefer the most specific skill, and invoke it with the Skill tool before doing the work yourself.
- If none fits, run `npx skills find <short query>` (the find-skills skill describes it) and show the user the best candidates.
- Never install a skill without asking first. A skill runs with full agent permissions, so name the source and ask.
- Do not search the remote list when an installed skill already fits.
