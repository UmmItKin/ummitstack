#!/usr/bin/env python3
"""Usage:
  run.py init OUT-DIR --input FILE [--profile quick|standard|deep] [--budget N]
  run.py phase OUT-DIR PHASE pending|done|skipped|blocked|failed [note]
  run.py gates OUT-DIR            read gates.json (written by verify.py) into the run and print each gate
  (phase done is refused until the phase artifact exists; report validates, writes REPORT.md, marks the report phase
  done and sets the run complete, so it is the only command that completes a run)
  run.py finding OUT-DIR add PHASE high|med|low AREA EVIDENCE
  run.py finding OUT-DIR resolve ID fixed|accepted [reason]
  run.py stop OUT-DIR REASON      end the run as incomplete (use when a gate fails and nobody can decide)
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


def failing_gates(run, findings):
    """Gates whose result is fail and that no accepted finding (area = gate name, with a reason) covers."""
    covered = {f["area"] for f in findings if f.get("state") == "accepted" and f.get("reason")}
    return [g for g, v in run.get("gates", {}).items() if v.get("result") == "fail" and g not in covered]


def validate(out, skip_artifacts=()):
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
            for a in ([] if pid in skip_artifacts else artifacts):
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
        errs += [f"complete run but gate {g} failed and no accepted finding covers it" for g in failing_gates(run, findings)]
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
    if cmd == "phase" or (cmd == "finding" and len(a) >= 3 and a[2] == "add"):
        run["run_status"] = "in_progress" if run.get("run_status") == "complete" else run.get("run_status")
    if cmd == "phase" and len(a) >= 4:
        spec = dict(PHASES)
        if a[2] not in spec or a[3] not in STATES:
            sys.exit(f"error: phase must be one of {[p for p, _ in PHASES]} and state one of {sorted(STATES)}")
        missing = [x for x in spec[a[2]] if not os.path.exists(os.path.join(out, x))] if a[3] == "done" and a[2] != "report" else []
        if missing:
            sys.exit(f"error: phase {a[2]} cannot be done yet, missing {', '.join(missing)}")
        if a[3] in ("skipped", "blocked", "failed") and not " ".join(a[4:]):
            sys.exit(f"error: {a[3]} needs a note")
        print(f"phase {a[2]}: {a[3]}")
        for p in run["phases"]:
            if p["id"] == a[2]:
                p["state"], p["note"] = a[3], " ".join(a[4:])
                if a[2] == "fix" and a[3] == "done":
                    run["rounds"] += 1
        save(out, "run.json", run)
    elif cmd == "gates":
        if not os.path.exists(os.path.join(out, "gates.json")):
            sys.exit("error: gates.json is missing; run verify.py first")
        run["gates"] = load(out, "gates.json", {})
        save(out, "run.json", run)
        for g in GATES:
            print(f"{g}: {run['gates'].get(g, {}).get('result', 'not recorded')}")
    elif cmd == "finding" and len(a) >= 3 and a[2] == "add" and len(a) >= 7:
        findings.append({"id": f"F{len(findings) + 1}", "phase": a[3], "severity": a[4], "area": a[5], "evidence": " ".join(a[6:]), "state": "open", "reason": ""})
        save(out, "findings.json", findings)
        save(out, "run.json", run)
    elif cmd == "finding" and len(a) >= 5 and a[2] == "resolve":
        for f in findings:
            if f["id"] == a[3]:
                f["state"], f["reason"] = a[4], " ".join(a[5:])
        save(out, "findings.json", findings)
    elif cmd == "stop" and len(a) >= 3:
        run["run_status"], run["incomplete_reason"] = "incomplete", " ".join(a[2:])
        save(out, "run.json", run)
        print(f"run stopped as incomplete: {run['incomplete_reason']}")
    elif cmd == "agents" and len(a) == 3:
        run["agents_used"] = int(a[2])
        save(out, "run.json", run)
    elif cmd == "validate":
        errs = validate(out)
        for e in errs:
            print("error:", e)
        print(f"errors: {len(errs)}")
        sys.exit(1 if errs else 0)
    elif cmd == "report":
        errs = validate(out, skip_artifacts=("report",))
        errs += [f"cannot close: phase {p['id']} is {p['state']}" for p in run["phases"] if p["id"] != "report" and p["state"] not in ("done", "skipped")]
        errs += [f"cannot close: gate {g} is not recorded (run: run.py gates)" for g in GATES if g not in run.get("gates", {})]
        errs += [f"cannot close: gate {g} failed; fix it, or accept it with: run.py finding {out} add <phase> med {g} <evidence> then resolve it as accepted with a reason" for g in failing_gates(run, findings)]
        errs += [f"cannot close: finding {f['id']} ({f['severity']}) is open" for f in findings if f["state"] == "open" and f["severity"] in ("high", "med")]
        for e in errs:
            print("error:", e)
        if errs:
            sys.exit(1)
        for p in run["phases"]:
            if p["id"] == "report":
                p["state"] = "done"
        run["run_status"] = "complete"
        save(out, "run.json", run)
        write_report(out, run, findings)
        print(f"complete: wrote {out}/REPORT.md")
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
