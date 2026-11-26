#!/usr/bin/env python3
"""Usage: migrate.py OLD [--to NEW_PATH] [--claude-dir DIR] [--with-sessions] [--apply]
       migrate.py --list-orphans [--claude-dir DIR]
Exit 0: done or nothing to do. Exit 1: an error. Exit 2: there were conflicts left for you to resolve.
"""
import filecmp, json, os, re, shutil, sys, time


def key(path):
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def files(root):
    for base, _, names in os.walk(root):
        for n in names:
            yield os.path.relpath(os.path.join(base, n), root)


def recorded_cwd(project_dir):
    for name in sorted(f for f in os.listdir(project_dir) if f.endswith(".jsonl")):
        with open(os.path.join(project_dir, name), encoding="utf-8", errors="ignore") as f:
            for _, line in zip(range(200), f):
                try:
                    cwd = json.loads(line).get("cwd")
                except ValueError:
                    continue
                if cwd:
                    return cwd
    return None


def orphans(projects):
    out = []
    for d in sorted(os.listdir(projects)) if os.path.isdir(projects) else []:
        p = os.path.join(projects, d)
        cwd = recorded_cwd(p) if os.path.isdir(p) else None
        if cwd and not os.path.isdir(cwd):
            mem = os.path.join(p, "memory")
            out.append((d, cwd, sum(1 for _ in files(mem)) if os.path.isdir(mem) else 0, os.path.getmtime(p)))
    return out


def resolve_old(arg, projects):
    if os.sep in arg or arg.startswith("~"):
        return key(os.path.expanduser(arg)), os.path.abspath(os.path.expanduser(arg))
    suffix = re.sub(r"[^A-Za-z0-9]", "-", arg).lower()
    names = sorted(d for d in os.listdir(projects) if os.path.isdir(os.path.join(projects, d))) if os.path.isdir(projects) else []
    hits = [d for d in names if d.lower().endswith("-" + suffix) or d.lower() == suffix]
    if len(hits) == 1:
        return hits[0], recorded_cwd(os.path.join(projects, hits[0])) or ""
    if not hits:
        sys.exit(f"error: no project folder ends with '{suffix}' in {projects}; give the full old path, or run --list-orphans")
    sys.exit("error: more than one project matches '" + arg + "': " + ", ".join(hits[:8]) + "; give the full old path")


def main():
    a = sys.argv[1:]
    opts = {"--to": os.getcwd(), "--claude-dir": os.path.expanduser("~/.claude")}
    flags = {"--with-sessions": False, "--apply": False, "--list-orphans": False}
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
    projects = os.path.join(opts["--claude-dir"], "projects")
    if flags["--list-orphans"]:
        found = orphans(projects)
        for d, cwd, n, t in sorted(found, key=lambda x: -x[3]):
            print(f"{time.strftime('%Y-%m-%d', time.localtime(t))}  {cwd}  ({n} memory files, key {d})")
        print(f"{len(found)} projects whose recorded folder no longer exists")
        sys.exit(0)
    if len(pos) != 1:
        sys.exit(__doc__)
    new = os.path.abspath(os.path.expanduser(opts["--to"]))
    if not os.path.isdir(new):
        sys.exit(f"error: {new} is not a directory")
    old_key, old_text = resolve_old(pos[0], projects)
    new_key = key(new)
    if old_key == new_key:
        sys.exit("error: the old and the new path give the same key; nothing to do")
    src, dst = os.path.join(projects, old_key), os.path.join(projects, new_key)
    if not os.path.isdir(src):
        sys.exit(f"error: no project folder {old_key} in {projects}; run --list-orphans to see what is there")

    plan = []
    parts = [("memory", os.path.join(src, "memory"), os.path.join(dst, "memory"))]
    sessions = [f for f in os.listdir(src) if f.endswith(".jsonl")]
    if flags["--with-sessions"]:
        parts.append(("sessions", src, dst))
    for label, s, d in parts:
        for rel in sorted(files(s)) if os.path.isdir(s) else []:
            if label == "sessions" and rel.split(os.sep)[0] == "memory":
                continue
            sf, df = os.path.join(s, rel), os.path.join(d, rel)
            if not os.path.exists(df):
                plan.append(("copy", label, rel, sf, df))
            elif filecmp.cmp(sf, df, shallow=False):
                plan.append(("same", label, rel, sf, df))
            elif label == "memory" and rel == "MEMORY.md":
                have = open(df, encoding="utf-8").read().split("\n")
                lines = [l for l in open(sf, encoding="utf-8").read().split("\n") if l.strip() and l not in have]
                plan.append(("merge" if lines else "same", label, rel, sf, df))
            else:
                plan.append(("conflict", label, rel, sf, df))

    print(f"old {old_text or '(path not recorded)'}  key {old_key}\nnew {new}  key {new_key}")
    print(f"memory files: {sum(1 for p in plan if p[1] == 'memory')}; old session transcripts: {len(sessions)}" + ("" if flags["--with-sessions"] else " (not copied; add --with-sessions)"))
    for kind, label, rel, _, _ in plan:
        print(f"  {kind:8s} {label}/{rel}")
    conflicts = [p for p in plan if p[0] == "conflict"]
    if not flags["--apply"]:
        print("dry run: nothing changed. Add --apply to do it.")
        sys.exit(2 if conflicts else 0)

    for kind, label, rel, sf, df in plan:
        if kind == "copy":
            os.makedirs(os.path.dirname(df), exist_ok=True)
            shutil.copy2(sf, df)
        elif kind == "merge":
            have = open(df, encoding="utf-8").read().split("\n")
            add = [l for l in open(sf, encoding="utf-8").read().split("\n") if l.strip() and l not in have]
            with open(df, "a", encoding="utf-8") as f:
                f.write(("" if open(df, encoding="utf-8").read().endswith("\n") else "\n") + "\n".join(add) + "\n")
    if old_text:
        mentions = []
        mem = os.path.join(dst, "memory")
        for rel in sorted(files(mem)) if os.path.isdir(mem) else []:
            for n, line in enumerate(open(os.path.join(mem, rel), encoding="utf-8", errors="ignore"), 1):
                if old_text in line:
                    mentions.append(f"{rel}:{n}")
        if mentions:
            print("memory lines that still mention the old path (not edited, check them): " + ", ".join(mentions[:10]))
    for p in conflicts:
        print(f"conflict kept as it was: {p[1]}/{p[2]} differs in the new folder; compare it with the old one by hand")
    print("done. The old folder was not changed.")
    sys.exit(2 if conflicts else 0)


if __name__ == "__main__":
    main()
