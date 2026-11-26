---
name: list-claude-projects
description: List every Claude Code project on this machine with its folder path and the title of each session, in two separate groups, titles you set yourself and titles Claude made from what the session was doing. Use when the user types /list-claude-projects or asks what Claude Code projects and sessions they have.
---

# List Claude Code projects

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/list-claude-projects [filter]`. The optional filter keeps only projects whose path contains it. It works in Claude Code only, because it reads `~/.claude/projects`.

## Steps
1. Run `python3 <skill-dir>/scripts/list_titles.py [filter]`. Add `--all` if the user wants every title, or `--limit N`. The default shows 20 titles per group per project and says how many more there are.
2. Show the result as it is: one overview line, then each project path with its two groups.
   - **Named**: the title the user set with `/rename`. These are the clear titles.
   - **Auto**: the title Claude made from what the session was doing, for sessions the user did not rename.
   - Sessions with neither are only counted.
3. Say which project folders no longer exist (the script marks them), and offer `/update-repo-directory-path` if one of them was renamed.
4. Add no commentary or grouping of your own unless the user asks. The request is the paths and the titles.

## Rules
- Read only. Do not open or quote a session file yourself, and never show conversation text; the script reads only the title fields and the working directory.
- The output lists the user's private project names. Show it to the user in this chat only, and do not copy it into any file, commit or message to a service.
- If there is no `~/.claude/projects`, say so in one line and stop.
