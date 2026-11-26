#!/usr/bin/env python3
"""Usage:
  run.py init OUT-DIR --input FILE [--profile quick|standard|deep] [--budget N]
  run.py phase OUT-DIR PHASE pending|done|skipped|blocked|failed [note]
  run.py gates OUT-DIR            read gates.json (written by verify.py) into the run
  run.py finding OUT-DIR add PHASE high|med|low AREA EVIDENCE
  run.py finding OUT-DIR resolve ID fixed|accepted [reason]
  run.py agents OUT-DIR N         record that N subagents were used
  run.py validate OUT-DIR         check the run for consistency (exit 1 on any error)
  run.py report OUT-DIR           write REPORT.md from a valid run
The phase list and the artifact each phase must leave are in phases.json beside this file; this file is the same in
every skill that has one. Only this script writes run.json and findings.json. Phases, artifacts, gates and findings follow the same
discipline as a coverage-led audit: a phase is done only when its artifact exists, and a run is complete only
when every gate is recorded and no high or medium finding is open."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASES = [(p["id"], p["artifacts"]) for p in json.load(open(os.path.join(HERE, "phases.json"), encoding="utf-8"))]
STATES = {"pending", "done", "skipped", "blocked", "failed"}
BUDGET = {"quick": 0, "standard": 2, "deep": 6}
GATES = ("fonts", "structure", "fidelity", "look")


def load(out, name, default):
    p = os.path.join(out, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def save(out, name, data):
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


def validate(out):
    run, findings, errs = load(out, "run.json", None), load(out, "findings.json", []), []
    if run is None:
        return ["run.json is missing"]
    if run.get("profile") not in BUDGET:
        errs.append("profile must be quick, standard or deep")
    if not (isinstance(run.get("budget"), int) and isinstance(run.get("agents_used"), int) and 0 <= run["agents_used"] <= run["budget"]):
        errs.append("agents_used must be from 0 to budget")
    ids = [p["id"] for p in run.get("phases", [])]
    if ids != [p for p, _ in PHASES]:
        errs.append(f"phases must be exactly {[p for p, _ in PHASES]} in that order")
    seen_open = False
    for p, (pid, artifacts) in zip(run.get("phases", []), PHASES):
        if p["state"] not in STATES:
            errs.append(f"phase {pid}: state must be one of {sorted(STATES)}")
        if p["state"] in ("skipped", "blocked", "failed") and not p.get("note"):
            errs.append(f"phase {pid}: {p['state']} needs a note")
        if p["state"] == "done":
            for a in artifacts:
                if not os.path.exists(os.path.join(out, a)):
                    errs.append(f"phase {pid}: done but {a} does not exist")
            if seen_open:
                errs.append(f"phase {pid}: done after an earlier phase that is not done or skipped")
        elif p["state"] != "skipped":
            seen_open = True
    if run.get("rounds", 0) > 3:
        errs.append("more than 3 fix rounds")
    ids_f = set()
    for f in findings:
        if f.get("id") in ids_f:
            errs.append(f"finding {f.get('id')}: duplicate id")
        ids_f.add(f.get("id"))
        if f.get("severity") not in ("high", "med", "low") or f.get("state") not in ("open", "fixed", "accepted"):
            errs.append(f"finding {f.get('id')}: bad severity or state")
        if f.get("state") == "accepted" and not f.get("reason"):
            errs.append(f"finding {f.get('id')}: accepted needs a reason")
    if run.get("run_status") == "complete":
        for p in run.get("phases", []):
            if p["state"] not in ("done", "skipped"):
                errs.append(f"complete run but phase {p['id']} is {p['state']}")
        for g in GATES:
            if g not in run.get("gates", {}):
                errs.append(f"complete run but gate {g} is not recorded")
        for f in findings:
            if f.get("state") == "open" and f.get("severity") in ("high", "med"):
                errs.append(f"complete run but finding {f['id']} ({f['severity']}) is open")
    elif run.get("run_status") == "incomplete" and not run.get("incomplete_reason"):
        errs.append("incomplete needs incomplete_reason")
    return errs


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    cmd, out = a[0], a[1]
    if cmd == "init":
        opts = dict(zip(a[2::2], a[3::2]))
        profile = opts.get("--profile", "quick")
        if "--input" not in opts or profile not in BUDGET:
            sys.exit(__doc__)
        os.makedirs(out, exist_ok=True)
        save(out, "run.json", {"input": os.path.basename(opts["--input"]), "profile": profile, "budget": int(opts.get("--budget", BUDGET[profile])),
                               "agents_used": 0, "rounds": 0, "run_status": "in_progress", "incomplete_reason": None, "gates": {},
                               "phases": [{"id": p, "state": "pending", "note": ""} for p, _ in PHASES]})
        save(out, "findings.json", [])
        return
    run, findings = load(out, "run.json", None), load(out, "findings.json", [])
    if run is None:
        sys.exit("error: run.json is missing; run init first")
    if cmd == "phase" and len(a) >= 4:
        for p in run["phases"]:
            if p["id"] == a[2]:
                p["state"], p["note"] = a[3], " ".join(a[4:])
                if a[2] == "fix" and a[3] == "done":
                    run["rounds"] += 1
        save(out, "run.json", run)
    elif cmd == "gates":
        run["gates"] = load(out, "gates.json", {})
        save(out, "run.json", run)
    elif cmd == "finding" and len(a) >= 3 and a[2] == "add" and len(a) >= 7:
        findings.append({"id": f"F{len(findings) + 1}", "phase": a[3], "severity": a[4], "area": a[5], "evidence": " ".join(a[6:]), "state": "open", "reason": ""})
        save(out, "findings.json", findings)
    elif cmd == "finding" and len(a) >= 5 and a[2] == "resolve":
        for f in findings:
            if f["id"] == a[3]:
                f["state"], f["reason"] = a[4], " ".join(a[5:])
        save(out, "findings.json", findings)
    elif cmd == "agents" and len(a) == 3:
        run["agents_used"] = int(a[2])
        save(out, "run.json", run)
    elif cmd in ("validate", "report"):
        errs = validate(out)
        for e in errs:
            print("error:", e)
        print(f"errors: {len(errs)}")
        if cmd == "report" and not errs:
            write_report(out, run, findings)
        sys.exit(1 if errs else 0)
    else:
        sys.exit(__doc__)


def write_report(out, run, findings):
    g = run.get("gates", {})
    lines = [f"# Reverse report for {run['input']}", "", f"Profile {run['profile']}, subagents used {run['agents_used']} of {run['budget']}, fix rounds {run['rounds']}, status {run['run_status']}.", "", "## Phases", ""]
    lines += [f"- {p['id']}: {p['state']}" + (f" ({p['note']})" if p["note"] else "") for p in run["phases"]]
    lines += ["", "## Gates", ""]
    for name in GATES:
        v = g.get(name, {})
        lines.append(f"- {name}: {v.get('result', 'not recorded')}" + (f", {v['detail']}" if v.get("detail") else ""))
    lines += ["", "## Findings", ""]
    lines += [f"- {f['id']} {f['severity']} {f['area']}: {f['evidence']} [{f['state']}{': ' + f['reason'] if f['reason'] else ''}]" for f in findings] or ["none"]
    open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
