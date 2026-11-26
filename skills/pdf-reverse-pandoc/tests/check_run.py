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
print(("PASS " if run("phase", d, "extract", "done").returncode != 0 else "FAIL ") + "a phase cannot be marked done without its artifact")
d = f"{temp}/run2"
run("init", d, "--input", "x.pdf")
edit(d, run_status="complete")
check("a complete run with pending phases and no gates is an error", d, False)
d = f"{temp}/run3"
run("init", d, "--input", "x.pdf")
run("agents", d, "3")
check("more subagents than the budget is an error", d, False)
d = f"{temp}/run5"
run("init", d, "--input", "x.pdf")
for p in PHASES:
    for name in p["artifacts"]:
        if name not in ("run.json", "REPORT.md", "gates.json"):
            open(f"{d}/{name}", "w").write("x")
json.dump({g: {"result": "pass"} for g in ("fonts", "structure", "fidelity", "look")}, open(f"{d}/gates.json", "w"))
print(("PASS " if run("report", d).returncode != 0 else "FAIL ") + "report refuses to close a run whose phases are not done and gates are not recorded")
for p in PHASES:
    if p["id"] not in ("report", "fix"):
        run("phase", d, p["id"], "done")
run("phase", d, "fix", "skipped", "no findings")
print(("PASS " if run("report", d).returncode != 0 else "FAIL ") + "report refuses until the gates are read into the run")
run("gates", d)
r = run("report", d)
print(("PASS " if r.returncode == 0 and json.load(open(f"{d}/run.json"))["run_status"] == "complete" and os.path.exists(f"{d}/REPORT.md") else "FAIL ") + "report closes a proper run, writes REPORT.md and marks it complete")
check("and the closed run validates", d, True)
run("finding", d, "add", "verify-look", "high", "tables", "x")
print(("PASS " if json.load(open(f"{d}/run.json"))["run_status"] == "in_progress" else "FAIL ") + "and a new finding reopens the complete run (found by the TLA+ model)")
edit(d, run_status="complete")
check("and forcing complete with a high finding open is an error", d, False)

d = f"{temp}/run6"
run("init", d, "--input", "x.pdf")
for p in PHASES:
    for name in p["artifacts"]:
        if name not in ("run.json", "REPORT.md", "gates.json"):
            open(f"{d}/{name}", "w").write("x")
json.dump({"fonts": {"result": "ok"}, "structure": {"result": "fail"}, "fidelity": {"result": "pass"}, "look": {"result": "pass"}}, open(f"{d}/gates.json", "w"))
for p in PHASES:
    if p["id"] not in ("report", "fix"):
        run("phase", d, p["id"], "done")
run("phase", d, "fix", "skipped", "nothing to fix")
run("gates", d)
print(("PASS " if run("report", d).returncode != 0 else "FAIL ") + "report refuses to close a run with a failed gate (found by a cold-start test)")
run("finding", d, "add", "verify-structure", "med", "structure", "one link is not kept")
run("finding", d, "resolve", "F1", "accepted", "the user accepted losing the link")
r = run("report", d)
print(("PASS " if r.returncode == 0 else "FAIL ") + "and closes once an accepted finding with a reason covers that gate")
d = f"{temp}/run7"
run("init", d, "--input", "x.pdf")
run("stop", d, "a gate failed and nobody could decide")
check("a stopped run is valid and says why", d, True)
print(("PASS " if os.path.exists(f"{d}/REPORT.md") else "FAIL ") + "and a stopped run still gets a REPORT.md")
edit(d, incomplete_reason=None)
check("and a stopped run without a reason is an error", d, False)
