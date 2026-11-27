#!/usr/bin/env python3
"""Usage: check.py [--toggle PATH] [--known FILE]
Runs the real toggle.py on every settings file in a stated space and checks what it promises: it never loses or
changes anything of the user's except its own entry, and it never damages a file it cannot read.
Exit 0 when every violation is in the known findings; exit 1 on a new violation or on a known finding that no longer
occurs. --toggle tests another copy of toggle.py, --known another findings file."""
import contextlib, copy, importlib.util, io, itertools, json, os, sys, tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))


def load(path):
    spec = importlib.util.spec_from_file_location("toggle_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, path, op):
    argv, out = sys.argv, io.StringIO()
    sys.argv = ["toggle.py", op, "--settings", path]
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            mod.main()
        return "ok", out.getvalue().strip()
    except SystemExit as e:
        return ("ok" if e.code in (None, 0) else "error"), out.getvalue().strip()
    except Exception as e:
        return "crash", f"{type(e).__name__}: {e}"
    finally:
        sys.argv = argv


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read(path):
    return json.load(open(path, encoding="utf-8"))


def norm(s):
    s = copy.deepcopy(s)
    hooks = s.get("hooks")
    if isinstance(hooks, dict):
        if hooks.get("SessionStart") == []:
            del hooks["SessionStart"]
        if not hooks:
            del s["hooks"]
    return s


def build_cases(canon):
    ours_hook = canon["hooks"][0]
    items = {
        "other": {"matcher": "startup", "hooks": [{"type": "command", "command": "echo other"}]},
        "empty": {"matcher": "x", "hooks": []},
        "ours": canon,
        "mixed": {"matcher": "y", "hooks": [{"type": "command", "command": "echo keep"}, ours_hook]},
        "lookalike": {"matcher": "z", "hooks": [{"type": "command", "command": "notify about auto-find-best-skill"}]},
    }
    pre = {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "true"}]}]}
    bases = [{}, {"model": "x", "env": {"K": "v"}}]
    cases = []
    for base in bases:
        for n in range(0, 4):
            for seq in itertools.product(items, repeat=n):
                groups = [copy.deepcopy(items[k]) for k in seq]
                tags = set()
                if "mixed" in seq:
                    tags.add("group-shared-with-ours")
                if "lookalike" in seq:
                    tags.add("hook-mentioning-the-name")
                hooks_options = [({"SessionStart": groups}, tags), ({**pre, "SessionStart": groups}, tags)]
                if n == 0:
                    hooks_options += [(None, tags), ({}, tags | {"empty-hooks-key"}), (pre, tags), ({"SessionStart": []}, tags | {"empty-session-start-list"})]
                    hooks_options = hooks_options[2:]
                for hooks, t in hooks_options:
                    s = copy.deepcopy(base)
                    if hooks is not None:
                        s["hooks"] = copy.deepcopy(hooks)
                    cases.append((s, t))
    return cases


MALFORMED = [
    ("invalid-json", "{ nope"), ("empty-file", ""), ("not-an-object", "[1, 2]"), ("json-null", "null"),
    ("hooks-is-a-list", '{"hooks": []}'), ("hooks-is-null", '{"hooks": null}'),
    ("session-start-is-an-object", '{"hooks": {"SessionStart": {}}}'), ("session-start-has-null", '{"hooks": {"SessionStart": [null]}}'),
    ("group-hooks-is-null", '{"hooks": {"SessionStart": [{"hooks": null}]}}'), ("command-is-a-number", '{"hooks": {"SessionStart": [{"hooks": [{"command": 5}]}]}}'),
    ("hook-is-a-string", '{"hooks": {"SessionStart": [{"hooks": ["x"]}]}}'),
]

SENTENCE = {
    "on-changes-more-than-its-entry": "on changed or removed something of yours other than its own entry",
    "on-twice-differs": "running on twice gave a different file than running it once",
    "off-after-on-does-not-restore": "on then off did not give back your original file",
    "off-removes-more-than-its-entry": "off removed something of yours besides its own entry",
    "off-changes-a-file-without-its-entry": "off changed a file that has no entry of its own",
    "status-wrong": "status said on or off wrongly",
    "crash": "it crashed with a Python error instead of a clear message",
    "changed-an-unreadable-file": "it changed a file it could not understand",
    "accepted-a-bad-file": "it carried on with a file it should have refused",
}


def shorten(obj, canon):
    if obj == canon:
        return "<OUR ENTRY>"
    if obj == canon["hooks"][0]:
        return "<OUR HOOK>"
    if isinstance(obj, dict):
        return {k: shorten(v, canon) for k, v in obj.items()}
    if isinstance(obj, list):
        return [shorten(v, canon) for v in obj]
    return obj


def check(mod):
    found = {}
    tmp = tempfile.mkdtemp()
    n = [0]

    def fresh(text):
        n[0] += 1
        p = os.path.join(tmp, f"s{n[0]}.json")
        write(p, text)
        return p

    def hit(prop, tags, example):
        example = shorten(example, canon)
        for tag in sorted(tags) or ["plain"]:
            rec = found.setdefault(prop + ":" + tag, {"count": 0, "example": example, "prop": prop})
            rec["count"] += 1
            if len(json.dumps(example)) < len(json.dumps(rec["example"])):
                rec["example"] = example

    p0 = fresh("{}")
    run(mod, p0, "on")
    canon = read(p0)["hooks"]["SessionStart"][0]
    cases = build_cases(canon)
    for s, tags in cases:
        def case_file(obj=s):
            return fresh(json.dumps(obj))
        has_ours = any(g == canon for g in s.get("hooks", {}).get("SessionStart", []))
        p = case_file()
        st, _ = run(mod, p, "on")
        after_on = read(p) if st == "ok" else None
        want = copy.deepcopy(s)
        keep = [g for g in want.get("hooks", {}).get("SessionStart", []) if g != canon]
        want.setdefault("hooks", {})["SessionStart"] = keep + [canon]
        if st != "ok" or after_on != want:
            hit("on-changes-more-than-its-entry", tags, {"start": s, "after_on": after_on})
        if st == "ok":
            run(mod, p, "on")
            if read(p) != after_on:
                hit("on-twice-differs", tags, {"start": s})
            run(mod, p, "off")
            if not has_ours and read(p) != s:
                hit("off-after-on-does-not-restore", tags, {"start": s, "after_on_then_off": read(p)})
        p = case_file()
        st, out = run(mod, p, "status")
        if st == "ok" and out.endswith(": on") != has_ours:
            hit("status-wrong", tags, {"start": s, "status": out})
        p = case_file()
        st, _ = run(mod, p, "off")
        got = read(p) if st == "ok" else None
        if has_ours:
            expect = copy.deepcopy(s)
            expect["hooks"]["SessionStart"] = [g for g in expect["hooks"]["SessionStart"] if g != canon]
            if got is None or norm(got) != norm(expect):
                hit("off-removes-more-than-its-entry", tags, {"start": s, "after_off": got})
        elif got != s:
            hit("off-changes-a-file-without-its-entry", tags, {"start": s, "after_off": got})
    for label, text in MALFORMED:
        for op in ("on", "off", "status"):
            p = fresh(text)
            st, out = run(mod, p, op)
            same = open(p, encoding="utf-8").read() == text
            tags = {label}
            if st == "crash":
                hit("crash", tags, {"file": text, "op": op, "error": out})
            elif not same:
                hit("changed-an-unreadable-file", tags, {"file": text, "op": op})
            elif st == "ok":
                hit("accepted-a-bad-file", tags, {"file": text, "op": op})
    return found, len(cases) + len(MALFORMED) * 3


def main():
    a = sys.argv[1:]
    toggle = os.path.join(ROOT, "skills/auto-find-best-skill/scripts/toggle.py")
    known = os.path.join(HERE, "..", "known-findings.txt")
    i = 0
    while i < len(a):
        if a[i] == "--toggle":
            toggle = a[i + 1]
        elif a[i] == "--known":
            known = a[i + 1]
        else:
            sys.exit(__doc__)
        i += 2
    found, total = check(load(toggle))
    known_ids = set()
    if os.path.exists(known):
        known_ids = {l.split("|")[0].strip() for l in open(known, encoding="utf-8") if l.strip() and not l.startswith("#")}
    new = {k: v for k, v in found.items() if k not in known_ids}
    gone = sorted(known_ids - set(found))
    print(f"{total} settings files tried; {len(found)} kinds of violation ({len(found) - len(new)} known, {len(new)} new)")
    for k in sorted(found):
        v = found[k]
        print(("KNOWN " if k in known_ids else "NEW   ") + f"{k} ({v['count']} files): {SENTENCE[v['prop']]}")
        print("      smallest example: " + json.dumps(v["example"]))
    for k in gone:
        print(f"FIXED {k} no longer occurs; remove it from known-findings.txt")
    sys.exit(1 if new or gone else 0)


if __name__ == "__main__":
    main()
