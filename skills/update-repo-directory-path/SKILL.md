---
name: update-repo-directory-path
description: After a repo was moved or renamed, copy this project's Claude Code memory from the old path to the new one so the memory is found again. Use when the user types /update-repo-directory-path or says that memory is missing after moving a project folder.
---

# Update repo directory path

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/update-repo-directory-path <new-path>`. The new path is where the repo is now. With no path, ask for it once.

Claude Code stores memory per project path (`~/.claude/projects/<key>/memory`). When a repo moves, a session at the new path has a different key and finds no memory. This skill copies the memory across. It works in Claude Code only.

## Steps
1. The old path is this session's primary working directory (shown in the environment). If the user names another old path, use that.
2. Preview: `python3 <skill-dir>/scripts/migrate.py <new-path> --from <old-path>`. It prints the old and new keys, each memory file as `copy`, `same`, `merge` (MEMORY.md lines to add) or `conflict`, and the number of old session transcripts. It changes nothing without `--apply`.
3. If it exits with an error, tell the user the line it printed and stop. Typical causes: the new path is not a directory yet, or the old project folder does not exist (it suggests similar names; pass `--from-key <name>`).
4. Show the user the plan in a few lines. If it lists conflicts, say which files differ and that they will be left as they are.
5. Run it again with `--apply`. Add `--with-sessions` only if the user also wants the old conversations to appear for the new path.
6. Report what was copied or merged, the conflicts left, and any memory lines that still mention the old path (the script lists them and does not edit them). Say that the memory applies from the next session at the new path, and that the old folder was not changed.

## Rules
- Never delete or move the old project folder and never overwrite a file that differs. The script only copies, and the user removes the old folder themselves.
- Never apply without showing the preview first.
- Edit nothing in the memory text yourself. If a memory mentions the old path, show the line and ask.
