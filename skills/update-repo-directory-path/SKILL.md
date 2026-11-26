---
name: update-repo-directory-path
description: After the user renamed or moved a repo folder by hand and started a new session there, copy the project's Claude Code memory from the old path to the current folder so the memory is found again. Use when the user types /update-repo-directory-path or says that memory is missing after renaming or moving a project folder.
---

# Update repo directory path

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/update-repo-directory-path <old-path-or-name>`. The old path is where the repo used to be (it does not exist any more) or just its old folder name. The new place is this session's primary working directory, so run it from inside the moved repo.

Claude Code stores memory per project path (`~/.claude/projects/<key>/memory`). After the user renames or moves a folder by hand, a session in the new place has a different key and starts with no memory, and the old path is forgotten. This skill copies the old memory into the new key. It works in Claude Code only.

## Steps
1. If there is no argument, run `python3 <skill-dir>/scripts/migrate.py --list-orphans`. It lists projects whose recorded folder no longer exists, newest first, with the number of memory files. Show the best candidates (the same or a similar folder name as the current directory first) and ask the user which one is the old path. Use one menu or one plain-text question, and nothing else.
2. Preview: `python3 <skill-dir>/scripts/migrate.py <old-path-or-name>`. It prints the old and new paths, each memory file as `copy`, `same`, `merge` (MEMORY.md lines to add) or `conflict`, and the number of old session transcripts. It changes nothing without `--apply`.
3. If it exits with an error, tell the user the line it printed and stop. If a name matches more than one project it lists them; ask which, or ask for the full old path.
4. Show the user the plan in a few lines. If it lists conflicts, say which files differ and that they will be left as they are.
5. Run it again with `--apply`. Add `--with-sessions` only if the user also wants the old conversations to appear here.
6. Report what was copied or merged, the conflicts left, and any memory lines that still mention the old path (the script lists them and does not edit them). Say that the memory applies from the next session in this folder, and that the old project folder was not changed.

## Rules
- Never delete or move the old project folder and never overwrite a file that differs. The script only copies; the user removes the old folder themselves.
- Never apply without showing the preview first.
- Edit nothing in the memory text yourself. If a memory mentions the old path, show the line and ask.
