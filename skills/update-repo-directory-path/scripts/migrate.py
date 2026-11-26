#!/usr/bin/env python3
"""Usage: migrate.py NEW_PATH [--from OLD_PATH | --from-key KEY] [--claude-dir DIR] [--with-sessions] [--apply]
Claude Code keeps a project's memory under DIR/projects/<key>/memory, where the key is the project path with every
character that is not a letter or digit turned into a dash. When a repo moves to a new path, the new session has a new
key and finds no memory. This copies the memory of the old key into the new key.
Without --apply it only prints the plan. It never deletes, never overwrites a file that differs (it reports a conflict),
and merges MEMORY.md by adding the index lines that are missing. --with-sessions also copies the old session
transcripts so they show up for the new path. DIR defaults to ~/.claude, OLD_PATH to the current directory.
Exit 0: done or nothing to do. Exit 1: an error. Exit 2: there were conflicts left for you to resolve."""
import filecmp, os, re, shutil, sys


def key(path):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def files(root):
    for base, _, names in os.walk(root):
        for n in names:
            yield os.path.relpath(os.path.join(base, n), root)


def main():
    a = sys.argv[1:]
    opts = {"--from": None, "--from-key": None, "--claude-dir": os.path.expanduser("~/.claude")}
    flags = {"--with-sessions": False, "--apply": False}
    pos = []
    i = 0
    while i < len(a):
        if a[i] in opts:
            opts[a[i]] = a[i + 1] if i + 1 < len(a) else sys.exit(__doc__)
            i += 2
        elif a[i] in flags:
            flags[a[i]] = True
            i += 1
        else:
            pos.append(a[i])
            i += 1
    if len(pos) != 1:
        sys.exit(__doc__)
    new = os.path.abspath(os.path.expanduser(pos[0]))
    if not os.path.isdir(new):
        sys.exit(f"error: {new} is not a directory; move the repo there first")
    projects = os.path.join(opts["--claude-dir"], "projects")
    old_key = opts["--from-key"] or key(os.path.expanduser(opts["--from"] or os.getcwd()))
    new_key = key(new)
    if old_key == new_key:
        sys.exit("error: the old and the new path give the same key; nothing to do")
    src, dst = os.path.join(projects, old_key), os.path.join(projects, new_key)
    if not os.path.isdir(src):
        near = sorted(d for d in os.listdir(projects) if d.lower().startswith(old_key.lower()[:12])) if os.path.isdir(projects) else []
        sys.exit(f"error: no project folder {old_key} in {projects}" + (f"; similar: {', '.join(near[:6])}" if near else "") + "; pass --from-key with the right name")

    plan = []
    parts = [("memory", os.path.join(src, "memory"), os.path.join(dst, "memory"))]
    sessions = [f for f in os.listdir(src) if f.endswith(".jsonl")]
    if flags["--with-sessions"]:
        parts.append(("sessions", src, dst))
    for label, s, d in parts:
        for rel in sorted(files(s)) if os.path.isdir(s) else []:
            if label == "sessions" and (rel.split(os.sep)[0] == "memory"):
                continue
            sf, df = os.path.join(s, rel), os.path.join(d, rel)
            if not os.path.exists(df):
                plan.append(("copy", label, rel, sf, df))
            elif filecmp.cmp(sf, df, shallow=False):
                plan.append(("same", label, rel, sf, df))
            elif label == "memory" and rel == "MEMORY.md":
                have = open(df, encoding="utf-8").read().split("\n")
                lines = [l for l in open(sf, encoding="utf-8").read().split("\n") if l.strip() and l not in have]
                plan.append(("merge", label, rel, sf, df) if lines else ("same", label, rel, sf, df))
            else:
                plan.append(("conflict", label, rel, sf, df))

    print(f"from {old_key}\n  to {new_key}")
    print(f"memory files: {sum(1 for p in plan if p[1] == 'memory')}; old session transcripts: {len(sessions)}" + ("" if flags["--with-sessions"] else " (not copied; add --with-sessions)"))
    for kind, label, rel, _, _ in plan:
        print(f"  {kind:8s} {label}/{rel}")
    if not flags["--apply"]:
        print("dry run: nothing changed. Add --apply to do it.")
        sys.exit(2 if any(p[0] == "conflict" for p in plan) else 0)

    for kind, label, rel, sf, df in plan:
        if kind == "copy":
            os.makedirs(os.path.dirname(df), exist_ok=True)
            shutil.copy2(sf, df)
        elif kind == "merge":
            have = open(df, encoding="utf-8").read().split("\n")
            add = [l for l in open(sf, encoding="utf-8").read().split("\n") if l.strip() and l not in have]
            with open(df, "a", encoding="utf-8") as f:
                f.write(("" if open(df, encoding="utf-8").read().endswith("\n") else "\n") + "\n".join(add) + "\n")
    old_path_text = opts["--from"] or ""
    if old_path_text:
        mentions = []
        mem = os.path.join(dst, "memory")
        for rel in sorted(files(mem)) if os.path.isdir(mem) else []:
            for n, line in enumerate(open(os.path.join(mem, rel), encoding="utf-8", errors="ignore"), 1):
                if os.path.abspath(os.path.expanduser(old_path_text)) in line:
                    mentions.append(f"{rel}:{n}")
        if mentions:
            print("memory lines that still mention the old path (not edited, check them): " + ", ".join(mentions[:10]))
    conflicts = [p for p in plan if p[0] == "conflict"]
    for p in conflicts:
        print(f"conflict kept as it was: {p[1]}/{p[2]} differs in the new folder; compare it with the old one by hand")
    print("done. The old folder was not changed.")
    sys.exit(2 if conflicts else 0)


if __name__ == "__main__":
    main()
