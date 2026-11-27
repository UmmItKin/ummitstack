# ummitstack verification map

This directory is the maintained source for verifying what a user gets from ummitstack. Read this index, then use the matching feature file as the recipe.

## Baseline preconditions

- Run from the repo root. `sh .claude/skills/verify-ummitstack/scripts/doctor.sh` must print `ok`.
- Evidence goes to `${TMPDIR:-/tmp}/verify-ummitstack/<time>-<name>/`.
- Use a scratch folder (`mktemp -d`) for every output a recipe writes.
- Anything that edits `~/.claude` runs against a temporary settings file or Claude folder, never the real one.
- Never run `npx skills add` with the real `HOME`. `prove-install.sh` sets a throwaway one.

## Driving conventions

- Prefer a skill's own documented commands. Read its `SKILL.md` for the exact flags.
- Treat every command as literal; keep flags and quoted names unchanged.
- Generated fixtures only. Never feed a recipe a document that belongs to the user.
- A skill that stops on purpose (a missing font, a scanned PDF, an invalid settings file) is a result to record, not a failure to work around.

## Proof and skip reporting

- Capture the command, stdout, stderr and exit code.
- Add a second, read-only view of the result: a diff, a gate file, or a second command.
- Report a path you could not reach with the command tried and the unmet precondition, for example a missing tool.
- A `skip:` line in a test run is a skip, not a pass.

## Features

- [install-a-skill](install-a-skill.md): `npx skills add` puts a working copy where an agent loads it.
- [pdf-reverse-pandoc](pdf-reverse-pandoc.md): reverse a text PDF, rebuild it, and pass four gates.
- [docx-reverse-pandoc](docx-reverse-pandoc.md): reverse a DOCX, rebuild it, and pass four gates.
- [verify-skill](verify-skill.md): static checks that catch an invalid skill before it is published.
- [auto-find-best-skill](auto-find-best-skill.md): a settings toggle that never damages the user's file.
