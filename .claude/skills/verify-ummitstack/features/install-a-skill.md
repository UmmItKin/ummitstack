# Install a skill

A user installs a skill from the repo with `npx skills add` and gets a working copy where the agent loads it. This is the path every other feature depends on.

## Sub-features

- `install-list` lists the skills the installer finds in the repo.
- `install-copy` copies one skill into `~/.claude/skills/<name>`.
- `install-lock` records the source in `~/.agents/.skill-lock.json`.

## How to get to it (user POV)

- Run `npx skills add UmmItKin/ummitstack -l` to list.
- Run `npx skills add UmmItKin/ummitstack --skill <name> -g -a claude-code -y` to install one skill for Claude Code.
- Run `npx skills update` later to follow the repo.

## Driving it with prove-install.sh

Preconditions:

- `doctor.sh` prints `ok`, which includes the installer finding as many skills as `skills/` has.
- The `npx` cache is warm, or the network is reachable.

- **List.** Run `sh .claude/skills/verify-ummitstack/scripts/doctor.sh`. It prints `skills in the repo: N` and `skills the installer finds: N` with the same N.
- **Install and check.** Run `sh .claude/skills/verify-ummitstack/scripts/prove-install.sh <skill> "$EV"`. It prints five PASS lines: SKILL.md present in the throwaway HOME, identical to `skills/<skill>`, static check passes, the installed copy's own tests pass, and the real `~/.claude/skills` is unchanged.
- **Proof.** `$EV/install.txt` contains `<skill> (copied)`, `$EV/diff.txt` is empty, and `$EV/summary.txt` has no FAIL line.

## Gotchas

- A skill whose frontmatter is invalid YAML (a `: ` inside `description`) is skipped without an error. The doctor catches it as a count mismatch.
- A local install records `sourceType: local` in the lock, so `npx skills update` will not follow GitHub for that skill until it is installed from GitHub again.
- A local install copies `__pycache__` folders. The diff check ignores them, but delete your own before installing.
- The throwaway HOME hides your real lock file and skills folder from the installer. That is what makes the check safe; do not pass the real `HOME`.
