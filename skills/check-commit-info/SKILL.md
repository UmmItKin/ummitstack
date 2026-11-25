---
name: check-commit-info
description: Check a commit before it is made. Git's own name and email must be set and are used as they are, and the staged changes and the message must hold no personal information such as emails, home paths, tokens, key files or the user's own name. Use before any commit, when commit-regular is on, or when the user types /check-commit-info.
---

# Check commit info

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

The argument is optional: the planned commit message, which is checked too. The repository may be public, so nothing personal goes into a commit, its message or its author line.

## Rules
- **Read-only.** Never stage, unstage, amend, reset or rewrite history, and never change git settings, except the one case below where the user gives a missing name or email.
- **Use git's defaults.** The author is whatever `git config user.name` and `git config user.email` resolve to. Never pass `--author`, `-c user.name=...`, `-c user.email=...` or `GIT_AUTHOR_*` and `GIT_COMMITTER_*`.
- A missing name or email is the user's to give. Never guess it from the system user name, the hostname, a remote URL or an earlier commit.
- Never print a secret or an email address in your reply. Report the kind and the `file:line` only.

## Workflow
1. The caller stages the files first. Something must be staged.
2. Run `sh <skill-dir>/scripts/check.sh "<commit message>"`. It prints one line per finding and exits 0 (clean), 1 (blocks the commit) or 2 (needs one confirmation from the user).
3. Read the output:
   - `stop identity ...`: the name or email is not set. Ask the user for the value and do not commit until it is set. When they give it, set it for this repository only (`git config user.name "<value>"`, `git config user.email "<value>"`). Use `--global` only if the user asks.
   - `stop secret-file`, `stop token`, `stop email`, `stop home-path`, `stop own-name`, `stop own-login`, `stop own-home`: do not commit. Replace the text with a placeholder (`/home/user`, `you@example.com`, `<token>`) or unstage the file, then run the check again. If the match is public information the project means to publish, such as the author's contact in a `LICENSE` or `README`, name the file and ask the user once before committing.
   - `stop message`: reword the commit message and run the check again.
   - `ask identity free-mailbox-email-in-public-history`: the email is on a common free mailbox and the repository has a remote. Ask the user once per session whether they want it in public history, and wait.
4. The script cannot find phone numbers, private hostnames, or the names of a school, an employer or a private project. Read `git diff --cached` once for those before the first commit of a session.
5. Reply with one line, `check-commit-info: ok`, or the findings as kind and `file:line`.

## Limits
The check covers what is about to be committed. If you find personal information in earlier commits that are not pushed, tell the user. Never amend, reset or rewrite history to remove it yourself.
