#!/usr/bin/env python3
"""Usage: prove-catches.py
Breaks a copy of toggle.py in each way listed in ../mutants.json and checks that check.py reports a new violation of the
property the break should trip. CAUGHT means the check can fail on that kind of break. MISSED means the check is blind to it.
STALE means the text to break no longer exists in toggle.py, so the code moved and the list needs another look.
Exit 1 on any MISSED or STALE. The real toggle.py is never changed."""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "../../../../skills/auto-find-best-skill/scripts/toggle.py"))


def main():
    text = open(SRC, encoding="utf-8").read()
    bad = 0
    for m in json.load(open(os.path.join(HERE, "..", "mutants.json"), encoding="utf-8")):
        if text.count(m["old"]) != 1:
            print(f"STALE  {m['name']}: the text to break occurs {text.count(m['old'])} times in toggle.py")
            bad = 1
            continue
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "toggle.py")
            open(path, "w", encoding="utf-8").write(text.replace(m["old"], m["new"]))
            r = subprocess.run([sys.executable, os.path.join(HERE, "check.py"), "--toggle", path], capture_output=True, text=True)
        caught = r.returncode == 1 and any(l.startswith("NEW") and m["expect"] in l for l in r.stdout.splitlines())
        print(("CAUGHT " if caught else "MISSED ") + f"{m['name']} (expected {m['expect']})")
        bad |= 0 if caught else 1
    sys.exit(bad)


if __name__ == "__main__":
    main()
