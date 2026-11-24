---
name: merge-pr-good-to-go
description: Merge a pull request that passed review. Checks gh, updates the branch if it is behind or conflicted, asks the user what comment to post, posts it, then merges. Use when the user types /merge-pr-good-to-go or asks to merge a PR that /review-pr marked good to go.
---

# Merge a reviewed pull request

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Accepted forms: a PR number, a PR URL, a branch, or nothing for the current branch. Default to the current branch's PR.

## Hard rules
- A merge is public and hard to undo. Merge only after `/review-pr` reported `good to go` in this session, and only after the user approves the comment and the merge itself.
- Check `gh` first, every time: `command -v gh` and `gh auth status`. If gh is missing, say how to install it (https://cli.github.com or the system package manager) and stop; never install it yourself. If not logged in, tell the user to run `gh auth login` and stop.
- The only push this skill makes is the explicit branch update below. Never force-merge, never use `--admin`, never delete branches, never touch the base branch, and never push anything except `<head-remote> <head-branch>`.

## Workflow

1. Inspect the PR:
   ```sh
   gh pr view <arg> --json number,title,url,state,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,baseRefName,headRefName,headRepository,headRepositoryOwner,maintainerCanModify,isCrossRepository,author
   ```

2. If the branch is behind the base branch or has conflicts, update it before merging:
   ```sh
   git status                       # must be clean, stop otherwise
   git fetch origin
   git switch <head-branch>
   git rebase origin/<base>         # or: git merge origin/<base>
   # resolve every conflict by hand, never take one side blindly
   git add <files>
   git rebase --continue
   ```
   - Push to the head branch only when you can: `maintainerCanModify` must be true, or the branch must live in a remote you own. Otherwise stop and ask the author, or the user, to update it.
   - Rebase rewrites history: use merge when the branch is shared or the repository forbids force-push. Abort with `git rebase --abort` (or `git merge --abort`) if resolving goes wrong.
   - Run the project's build and checks after resolving. Never push a failing branch.
   - Push: `git push --force-with-lease <head-remote> <head-branch>` after a rebase, plain `git push` after a merge. Never plain `--force`.
   - Re-read the PR state after the push.

3. Stop unless all hold: state `OPEN`, not a draft, `mergeable` is `MERGEABLE`, and no failing checks. List what blocks it and stop. Never force a merge.
4. If this session has no `good to go` verdict from `/review-pr`, say so and stop. Do not merge unreviewed work.
5. Ask the user what the comment should say. Do not write it for them. Show the exact text back once they give it.
6. Post it:
   ```sh
   gh pr comment <number> --body "<text>"
   ```
7. Ask the user to confirm the merge and the method: merge commit, squash, or rebase. Use the flag they choose (`--merge`, `--squash`, `--rebase`); if they do not choose, use `--squash`. Then:
   ```sh
   gh pr merge <number> --squash
   ```
8. Reply with the merged PR URL and the comment URL, one line each.
