#!/usr/bin/env python3
"""Usage: list_titles.py [FILTER] [--claude-dir DIR] [--limit N | --all] [--json]
Lists every Claude Code project under DIR/projects (default ~/.claude): the project path and the title of each session.
Each session appears once, in one of two groups: named (a title you set with /rename) or auto (the title Claude made
from what the session was doing). Sessions with neither are only counted. FILTER keeps projects whose path contains it.
It reads only the title fields and the working directory, never the conversation text. --limit N shows at most N titles
per group per project (default 20); --all shows every title. Exit 1 when there is no projects folder."""
import glob, json, os, sys


def scan(path):
    cwd = custom = auto = None
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if cwd is None and '"cwd"' in line:
                try:
                    cwd = json.loads(line).get("cwd") or None
                except ValueError:
                    pass
            if "itle" not in line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "custom-title" and (e.get("customTitle") or "").strip():
                custom = e["customTitle"].strip()
            elif e.get("type") == "ai-title" and (e.get("aiTitle") or "").strip():
                auto = e["aiTitle"].strip()
    return cwd, custom, auto


def decode_key(key):
    return "/" + key.lstrip("-").replace("-", "/") + "  (path guessed from the folder name)"


def main():
    a = sys.argv[1:]
    claude = os.path.expanduser("~/.claude")
    limit, as_json, flt = 20, False, None
    i = 0
    while i < len(a):
        if a[i] == "--claude-dir":
            claude = a[i + 1]; i += 2
        elif a[i] == "--limit":
            limit = int(a[i + 1]); i += 2
        elif a[i] == "--all":
            limit = None; i += 1
        elif a[i] == "--json":
            as_json = True; i += 1
        elif a[i].startswith("--"):
            sys.exit(__doc__)
        else:
            flt = a[i]; i += 1
    root = os.path.join(claude, "projects")
    if not os.path.isdir(root):
        sys.exit(f"error: no projects folder at {root}")
    projects = []
    for key in sorted(os.listdir(root)):
        folder = os.path.join(root, key)
        files = sorted(glob.glob(os.path.join(folder, "*.jsonl")), key=os.path.getmtime, reverse=True)
        if not os.path.isdir(folder) or not files:
            continue
        named, auto, untitled, path = [], [], 0, None
        for f in files:
            cwd, custom, ai = scan(f)
            path = path or cwd
            if custom:
                named.append(custom)
            elif ai:
                auto.append(ai)
            else:
                untitled += 1
        path = path or decode_key(key)
        if flt and flt not in path:
            continue
        projects.append({"path": path, "exists": os.path.isdir(path.split("  (")[0]), "sessions": len(files), "named": named, "auto": auto, "untitled": untitled, "latest": os.path.getmtime(files[0])})
    projects.sort(key=lambda p: -p["latest"])
    if as_json:
        print(json.dumps([{k: v for k, v in p.items() if k != "latest"} for p in projects], indent=1, ensure_ascii=False))
        return
    total = sum(p["sessions"] for p in projects)
    print(f"{len(projects)} projects, {total} sessions; named {sum(len(p['named']) for p in projects)}, auto-titled {sum(len(p['auto']) for p in projects)}, untitled {sum(p['untitled'] for p in projects)}")
    for p in projects:
        print(f"\n{p['path']}{'' if p['exists'] else '  [folder no longer exists]'}  ({p['sessions']} sessions)")
        for label, titles in (("Named (you set the title)", p["named"]), ("Auto (what the session was doing)", p["auto"])):
            if not titles:
                continue
            shown = titles if limit is None else titles[:limit]
            print(f"  {label}:")
            for t in shown:
                print(f"    - {t}")
            if len(shown) < len(titles):
                print(f"    ... and {len(titles) - len(shown)} more")
        if p["untitled"]:
            print(f"  {p['untitled']} sessions have no title")


if __name__ == "__main__":
    main()
