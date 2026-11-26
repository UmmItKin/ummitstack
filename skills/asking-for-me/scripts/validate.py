#!/usr/bin/env python3
"""Usage: validate.py run.json [--solver solver.json]
Exit 0 when valid, 1 on errors or solver disagreements.
"""
import json, re, sys

PROFILES = {"quick", "standard", "deep"}
STATES = {"planned", "covered", "deferred"}
STATUS = {"in_progress", "complete", "incomplete"}
KINDS = {"quiz", "blank", "claims"}


def text(v):
    return isinstance(v, str) and v.strip() != ""


def options_ok(opts):
    return isinstance(opts, list) and 3 <= len(opts) <= 5 and all(text(o) for o in opts) and len(set(opts)) == len(opts)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def check_item(it, err):
    i = it.get("id", "?")
    kind = it.get("kind")
    if not text(it.get("concept")):
        err.append(f"{i}: concept missing")
    if kind == "quiz":
        for f in ("q", "hint", "why"):
            if not text(it.get(f)):
                err.append(f"{i}: {f} missing")
        opts = it.get("options")
        if not options_ok(opts):
            err.append(f"{i}: options must be 3 to 5 unique non-empty strings")
        else:
            a = it.get("answer")
            ans = a if isinstance(a, list) else [a]
            if not ans or not all(is_int(x) and 0 <= x < len(opts) for x in ans) or len(set(ans)) != len(ans):
                err.append(f"{i}: answer must be an index, or a list of unique indexes, into options")
        if text(it.get("why")) and len(it["why"].split()) > 25:
            err.append(f"{i}: why is over 25 words")
    elif kind == "blank":
        for f in ("title", "prompt", "code", "typePrompt", "why"):
            if not text(it.get(f)):
                err.append(f"{i}: {f} missing")
        if text(it.get("code")) and it["code"].count("___") != 1:
            err.append(f"{i}: code must contain exactly one ___")
        opts = it.get("options")
        if not options_ok(opts):
            err.append(f"{i}: options must be 3 to 5 unique non-empty strings")
        elif it.get("answer") not in opts:
            err.append(f"{i}: answer must be exactly one of options")
        if text(it.get("why")) and len(it["why"].split()) > 25:
            err.append(f"{i}: why is over 25 words")
    elif kind == "claims":
        c = it.get("claims")
        if not (isinstance(c, list) and c and all(text(x) for x in c)):
            err.append(f"{i}: claims must be a non-empty list of strings")
    else:
        err.append(f"{i}: kind must be one of {sorted(KINDS)}")


def validate(run):
    err, warn = [], []
    for f in ("topic", "profile", "budget", "agents_used", "run_status", "units", "items"):
        if f not in run:
            err.append(f"run: {f} missing")
    if err:
        return err, warn
    if run["profile"] not in PROFILES:
        err.append(f"run: profile must be one of {sorted(PROFILES)}")
    if not (is_int(run["budget"]) and is_int(run["agents_used"]) and 0 <= run["agents_used"] <= run["budget"]):
        err.append("run: agents_used must be an integer from 0 to budget")
    if run["run_status"] not in STATUS:
        err.append(f"run: run_status must be one of {sorted(STATUS)}")
    if run["run_status"] == "incomplete" and not text(run.get("incomplete_reason")):
        err.append("run: incomplete needs incomplete_reason")

    seen = set()
    for it in run["items"]:
        if it.get("id") in seen:
            err.append(f"{it.get('id')}: duplicate id")
        seen.add(it.get("id"))
        check_item(it, err)

    have = {(it.get("concept"), it.get("kind")) for it in run["items"]}
    uids = set()
    for u in run["units"]:
        uid = u.get("id")
        if uid in uids:
            err.append(f"unit {uid}: duplicate id")
        uids.add(uid)
        if u.get("state") not in STATES:
            err.append(f"unit {uid}: state must be one of {sorted(STATES)}")
        if u.get("state") == "covered" and (u.get("concept"), u.get("kind")) not in have:
            err.append(f"unit {uid}: covered but has no item")
        if u.get("state") == "deferred" and not text(u.get("reason")):
            err.append(f"unit {uid}: deferred needs a reason")
        if run["run_status"] == "complete" and u.get("state") == "planned":
            err.append(f"unit {uid}: still planned in a complete run")
    unit_keys = {(u.get("concept"), u.get("kind")) for u in run["units"]}
    for k in have - unit_keys:
        warn.append(f"items for {k[0]} / {k[1]} have no unit")

    quiz = [it for it in run["items"] if it.get("kind") == "quiz" and is_int(it.get("answer"))]
    if len(quiz) >= 4 and len({it["answer"] for it in quiz}) == 1:
        warn.append("every single-answer quiz item has the same answer position")
    stems = [re.sub(r"\W+", " ", str(it.get("q", it.get("prompt", "")))).strip().lower() for it in run["items"] if it.get("kind") != "claims"]
    if len(stems) != len(set(stems)):
        warn.append("two items have the same question text")
    return err, warn


def compare(run, solver):
    answers = solver.get("answers", {})
    bad = []
    for it in run["items"]:
        if it.get("kind") not in ("quiz", "blank"):
            continue
        got = answers.get(it["id"], "<none>")
        want = it["answer"]
        if isinstance(want, list):
            same = isinstance(got, list) and sorted(got) == sorted(want)
        elif isinstance(want, str):
            same = isinstance(got, str) and got.strip() == want.strip()
        else:
            same = got == want
        if not same:
            bad.append(f"{it['id']}: key {want!r}, solver {got!r}")
    for i in solver.get("ambiguous", []):
        bad.append(f"{i}: solver called it ambiguous")
    return bad


def main():
    args = sys.argv[1:]
    solver_path = None
    if "--solver" in args:
        k = args.index("--solver")
        solver_path = args[k + 1] if k + 1 < len(args) else None
        args = args[:k] + args[k + 2:]
    if len(args) != 1 or ("--solver" in sys.argv and not solver_path):
        sys.exit("usage: validate.py run.json [--solver solver.json]")
    try:
        run = json.load(open(args[0], encoding="utf-8"))
        solver = json.load(open(solver_path, encoding="utf-8")) if solver_path else None
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: {e}")
    err, warn = validate(run)
    if solver is not None and not err:
        err += compare(run, solver)
    for e in err:
        print("error:", e)
    for w in warn:
        print("warning:", w)
    print(f"errors: {len(err)}, warnings: {len(warn)}")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
