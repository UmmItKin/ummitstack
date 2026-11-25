#!/usr/bin/env python3
"""Usage: check_run.py scripts-dir temp-dir
Checks that run.py validate rejects the ways a run was once called complete without proof, and accepts a proper one.
Prints one PASS or FAIL line per case."""
import json, os, subprocess, sys

scripts, temp = sys.argv[1], sys.argv[2]


def run(*args):
    return subprocess.run([sys.executable, os.path.join(scripts, "run.py"), *args], capture_output=True, text=True)


def check(name, folder, want_ok):
    ok = run("validate", folder).returncode == 0
    print(("PASS " if ok == want_ok else "FAIL ") + name)


def edit(folder, **changes):
    data = json.load(open(f"{folder}/run.json"))
    data.update(changes)
    json.dump(data, open(f"{folder}/run.json", "w"))


d = f"{temp}/run1"
run("init", d, "--input", "x.docx")
run("phase", d, "reverse", "done")
check("a phase marked done without its artifact is an error", d, False)

d = f"{temp}/run2"
run("init", d, "--input", "x.docx")
edit(d, run_status="complete")
check("a complete run with pending phases and no gates is an error", d, False)

d = f"{temp}/run3"
run("init", d, "--input", "x.docx")
run("finding", d, "add", "verify-look", "high", "tables", "cell text outside the table")
run("finding", d, "resolve", "F1", "accepted")
check("accepting a finding without a reason is an error", d, False)
run("finding", d, "resolve", "F1", "accepted", "the renderer cannot lay it out")
check("accepting a finding with a reason is allowed", d, True)

d = f"{temp}/run4"
run("init", d, "--input", "x.docx")
run("agents", d, "3")
check("more subagents than the budget is an error", d, False)

d = f"{temp}/run5"
run("init", d, "--input", "x.docx")
for name in ("inventory-original.txt", "coverage.json", "doc.md", "reference.docx", "build.sh", "rebuilt.docx", "gates.json", "REPORT.md"):
    open(f"{d}/{name}", "w").write("x")
for phase in ("setup", "fonts", "coverage", "reverse", "rebuild", "verify-structure", "verify-look", "report"):
    run("phase", d, phase, "done")
run("phase", d, "fix", "skipped", "no findings")
edit(d, run_status="complete", gates={g: {"result": "pass"} for g in ("fonts", "structure", "fidelity", "look")})
check("a complete run with every phase, artifact and gate is valid", d, True)
run("finding", d, "add", "verify-look", "high", "tables", "x")
check("and becomes invalid when a high finding is open", d, False)
