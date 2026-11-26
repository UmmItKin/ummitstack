#!/usr/bin/env python3
"""Usage: no-coauthor.py [settings.json]
"""
import json, os, sys

path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.claude/settings.json")
want = {"commit": "", "pr": ""}
try:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}
except json.JSONDecodeError as err:
    sys.exit(f"error: {path} is not valid JSON ({err}); left it unchanged")
if not isinstance(data, dict):
    sys.exit(f"error: {path} is not a JSON object; left it unchanged")

attr = data.get("attribution")
if isinstance(attr, dict) and all(attr.get(k) == v for k, v in want.items()):
    print("already set")
    sys.exit(0)
data["attribution"] = {**(attr if isinstance(attr, dict) else {}), **want}
os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
os.replace(tmp, path)
print("set")
