---
name: merge-pr-good-to-go
description: Merge a pull request that passed review. Checks gh, asks the user what comment to post, posts it, then merges. Use when the user types /merge-pr-good-to-go or asks to merge a PR that /review-pr marked good to go.
---

# Merge a reviewed pull request

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Accepted forms: a PR number, a PR URL, a branch, or nothing for the current branch. Default to the current branch's PR.

## Hard rules
- A merge is public and hard to undo. Merge only after `/review-pr` reported `good to go` in this session, and only after the user approves the comment and the merge itself.
- Check `gh` first, every time: `command -v gh` and `gh auth status`. If gh is missing, say how to install it (https://cli.github.com or the system package manager) and stop; never install it yourself. If not logged in, tell the user to run `gh auth login` and stop.
- Nothing else changes: no pushing, no force, no branch deletion, no `--admin`, no edits.

## Workflow

1. Inspect the PR:
   ```sh
   gh pr view <arg> --json number,title,url,state,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,baseRefName,headRefName,author
   ```
2. Stop unless all hold: state `OPEN`, not a draft, `mergeable` is `MERGEABLE`, and no failing checks. List what blocks it and stop. Never force a merge.
3. If this session has no `good to go` verdict from `/review-pr`, say so and stop. Do not merge unreviewed work.
4. Ask the user what the comment should say. Do not write it for them. Show the exact text back once they give it.
5. Post it:
   ```sh
   gh pr comment <number> --body "<text>"
   ```
6. Ask the user to confirm the merge and the method: merge commit, squash, or rebase. Use the flag they choose (`--merge`, `--squash`, `--rebase`); if they do not choose, use `--squash`. Then:
   ```sh
   gh pr merge <number> --squash
   ```
7. Reply with the merged PR URL and the comment URL, one line each.
