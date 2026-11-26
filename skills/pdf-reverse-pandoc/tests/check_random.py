#!/usr/bin/env python3
"""Usage: check_random.py scripts-dir temp-dir
Runs random command sequences through run.py and compares run.py validate with a second, independent statement of
the same rules (the rules in specs/pipeline.tla). Prints one PASS or FAIL line."""
import json, os, random, subprocess, sys

scripts, temp = sys.argv[1], sys.argv[2]
PHASES = json.load(open(os.path.join(scripts, "phases.json")))
IDS = [p["id"] for p in PHASES]
random.seed(7)


def run(*args):
    return subprocess.run([sys.executable, os.path.join(scripts, "run.py"), *args], capture_output=True, text=True)


def model_ok(run_json, findings, folder):
    """Same rules, written again: complete needs every phase done or skipped with artifacts, all gates, no open high or med."""
    if run_json["agents_used"] > run_json["budget"] or run_json["rounds"] > 3:
        return False
    open_early = False
    for p, spec in zip(run_json["phases"], PHASES):
        if p["state"] in ("skipped", "blocked", "failed") and not p["note"]:
            return False
        if p["state"] == "done":
            if open_early or any(not os.path.exists(os.path.join(folder, a)) for a in spec["artifacts"]):
                return False
        elif p["state"] != "skipped":
            open_early = True
    for f in findings:
        if f["state"] == "accepted" and not f["reason"]:
            return False
    if run_json["run_status"] == "complete":
        if any(p["state"] not in ("done", "skipped") for p in run_json["phases"]):
            return False
        if any(g not in run_json["gates"] for g in ("fonts", "structure", "fidelity", "look")):
            return False
        if any(f["state"] == "open" and f["severity"] in ("high", "med") for f in findings):
            return False
    return True


bad = 0
for n in range(60):
    d = f"{temp}/rand{n}"
    run("init", d, "--input", "x.pdf", "--profile", random.choice(["quick", "standard"]))
    for _ in range(random.randint(1, 14)):
        pick = random.random()
        if pick < 0.45:
            ph = random.choice(IDS)
            if random.random() < 0.7:
                for a in next(p for p in PHASES if p["id"] == ph)["artifacts"]:
                    if a != "run.json":
                        open(f"{d}/{a}", "w").write("x")
            run("phase", d, ph, random.choice(["done", "done", "pending", "skipped", "failed"]), random.choice(["", "why"]))
        elif pick < 0.6:
            run("finding", d, "add", "verify-look", random.choice(["high", "med", "low"]), "area", "evidence")
        elif pick < 0.7:
            run("finding", d, "resolve", "F1", random.choice(["fixed", "accepted"]), random.choice(["", "reason"]))
        elif pick < 0.8:
            run("agents", d, str(random.randint(0, 3)))
        elif pick < 0.9:
            data = json.load(open(f"{d}/run.json"))
            data["run_status"] = "complete"
            data["gates"] = {g: {"result": "pass"} for g in random.sample(["fonts", "structure", "fidelity", "look"], random.randint(2, 4))}
            json.dump(data, open(f"{d}/run.json", "w"))
        else:
            data = json.load(open(f"{d}/run.json"))
            data["rounds"] = random.randint(0, 4)
            json.dump(data, open(f"{d}/run.json", "w"))
    data = json.load(open(f"{d}/run.json"))
    findings = json.load(open(f"{d}/findings.json"))
    if (run("validate", d).returncode == 0) != model_ok(data, findings, d):
        bad += 1
print(("PASS" if bad == 0 else "FAIL") + f" run.py validate agrees with the independent rules on 60 random runs ({bad} disagreements)")
