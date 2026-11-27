# Coverage

The verification covers one file, and runs it as it is. There is no separate model.

Covers:
- skills/auto-find-best-skill/scripts/toggle.py

What in that file each check reaches:
- `ours()`, `groups()`: which entry counts as the tool's own, and where it looks. Findings F1 and F2 come from here.
- `load()`: how a file it cannot read is refused. Finding F3.
- `save()`: not checked for failures of the disk. It writes through a temporary file and replaces the original; the checks read the result.
- `main()`: the `on`, `off` and `status` branches, and the default settings path (never used, every case passes `--settings`).

Sync commit: e3bd02d

The sync commit is the last commit at which someone confirmed that this verification describes the covered file. Run `sh scripts/sync.sh`. If the covered file changed after that commit, read the change, re-run the checks, and move the sync commit forward only when the checks and `mutants.json` still describe the code.
