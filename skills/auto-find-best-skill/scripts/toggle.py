#!/usr/bin/env python3
"""Usage: toggle.py on|off|status [--settings FILE]
Turns the session hook of auto-find-best-skill on or off in the Claude Code settings file (default ~/.claude/settings.json).
The hook is a SessionStart command that prints one reminder, so every new session starts with it in context.
It changes nothing else: other settings and other hooks are kept, and running it twice gives the same file.
A copy of the original file is kept once, next to it, as settings.json.before-auto-find-best-skill.
Exit 1 when the settings file is not valid JSON; the file is then left as it was."""
import json, os, shlex, shutil, sys

MARK = "auto-find-best-skill"
MESSAGE = (f"{MARK} is on. Before starting any task, check the available skills list and invoke the best match with the Skill tool. "
           "Only if none fits, use find-skills (npx skills find) to search, and ask before installing anything.")
MATCHER = "startup|resume|clear|compact"


def ours(group):
    return any(MARK in h.get("command", "") for h in group.get("hooks", []))


def load(path):
    if not os.path.exists(path):
        return {}
    try:
        data = json.load(open(path, encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"error: {path} is not valid JSON ({e}); not changed")
    if not isinstance(data, dict):
        sys.exit(f"error: {path} is not a JSON object; not changed")
    return data


def save(path, data):
    backup = path + ".before-" + MARK
    if os.path.exists(path) and not os.path.exists(backup):
        shutil.copy2(path, backup)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def groups(data):
    return data.get("hooks", {}).get("SessionStart", [])


def main():
    a = sys.argv[1:]
    path = os.path.expanduser("~/.claude/settings.json")
    if "--settings" in a:
        k = a.index("--settings")
        path = a[k + 1]
        a = a[:k] + a[k + 2:]
    if len(a) != 1 or a[0] not in ("on", "off", "status"):
        sys.exit(__doc__)
    data = load(path)
    on = any(ours(g) for g in groups(data))
    if a[0] == "status":
        print(f"{MARK}: {'on' if on else 'off'}")
        return
    rest = [g for g in groups(data) if not ours(g)]
    if a[0] == "on":
        rest.append({"matcher": MATCHER, "hooks": [{"type": "command", "command": "echo " + shlex.quote(MESSAGE)}]})
        data.setdefault("hooks", {})["SessionStart"] = rest
    else:
        if not on:
            print(f"{MARK}: off (nothing to remove)")
            return
        hooks = data.get("hooks", {})
        if rest:
            hooks["SessionStart"] = rest
        else:
            hooks.pop("SessionStart", None)
        if not hooks:
            data.pop("hooks", None)
    save(path, data)
    print(f"{MARK}: {a[0]}")


if __name__ == "__main__":
    main()
