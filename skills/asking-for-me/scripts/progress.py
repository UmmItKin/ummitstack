#!/usr/bin/env python3
"""Usage:
  progress.py FILE record CONCEPT right|wrong
  progress.py FILE weak [N]        prints the N weakest concepts (default 3), one per line
"""
import json, os, sys


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def main():
    a = sys.argv[1:]
    if len(a) >= 4 and a[1] == "record" and a[3] in ("right", "wrong"):
        data = load(a[0])
        c = data.setdefault(a[2].strip(), {"right": 0, "wrong": 0})
        c[a[3]] += 1
        tmp = a[0] + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, a[0])
    elif len(a) >= 2 and a[1] == "weak":
        n = int(a[2]) if len(a) > 2 else 3
        data = load(a[0])
        weak = [(k, v) for k, v in data.items() if v["wrong"] > 0]
        weak.sort(key=lambda kv: (-kv[1]["wrong"] / (kv[1]["right"] + kv[1]["wrong"]), -kv[1]["wrong"], kv[0]))
        for k, _ in weak[:n]:
            print(k)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
