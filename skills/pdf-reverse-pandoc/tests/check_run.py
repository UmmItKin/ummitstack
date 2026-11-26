#!/usr/bin/env python3
"""Usage: check_run.py scripts-dir temp-dir
Checks that run.py validate rejects the ways a run was once called complete without proof, and accepts a proper one.
Prints one PASS or FAIL line per case."""
import json, os, subprocess, sys

scripts, temp = sys.argv[1], sys.argv[2]
PHASES = json.load(open(os.path.join(scripts, "phases.json")))


def run(*args):
    return subprocess.run([sys.executable, os.path.join(scripts, "run.py"), *args], capture_output=True, text=True)


def check(name, folder, want_ok):
    print(("PASS " if (run("validate", folder).returncode == 0) == want_ok else "FAIL ") + name)


def edit(folder, **changes):
    data = json.load(open(f"{folder}/run.json"))
    data.update(changes)
    json.dump(data, open(f"{folder}/run.json", "w"))


d = f"{temp}/run1"
run("init", d, "--input", "x.pdf")
run("phase", d, "extract", "done")
check("a phase marked done without its artifact is an error", d, False)
d = f"{temp}/run2"
run("init", d, "--input", "x.pdf")
edit(d, run_status="complete")
check("a complete run with pending phases and no gates is an error", d, False)
d = f"{temp}/run3"
run("init", d, "--input", "x.pdf")
run("agents", d, "3")
check("more subagents than the budget is an error", d, False)
d = f"{temp}/run4"
run("init", d, "--input", "x.pdf")
for p in PHASES:
    for a in p["artifacts"]:
        if a != "run.json":
            open(f"{d}/{a}", "w").write("x")
for p in PHASES:
    run("phase", d, p["id"], "skipped" if p["id"] == "fix" else "done", "no findings" if p["id"] == "fix" else "")
edit(d, run_status="complete", gates={g: {"result": "pass"} for g in ("fonts", "structure", "fidelity", "look")})
check("a complete run with every phase, artifact and gate is valid", d, True)
run("finding", d, "add", "verify-look", "high", "tables", "x")
check("and becomes invalid when a high finding is open", d, False)
