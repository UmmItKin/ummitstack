#!/usr/bin/env python3
"""Usage: leak_scan.py --source FILE [--source FILE ...] [--ignore PHRASE ...] (--staged | --history [REV-RANGE]) [--message TEXT]
Checks that nothing from private source files (a .docx, .pdf or text file the user gave you) ended up in a commit.
It reads every line of 14 or more characters (after collapsing spaces) from the sources, then searches the added lines of the staged diff
(--staged, plus --message for the commit message) or of every commit in a range (--history, default all of HEAD).
Lines are compared ignoring case and spacing, and only as whole words (a heading does not match inside a longer word). Prints the commit and the first 30 characters of each hit, never the
whole line. Exit 1 on any hit. --ignore skips a phrase that is generic, such as a heading every document has."""
import re, subprocess, sys, zipfile


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, errors="ignore").stdout


def norm(s):
    return re.sub(r"\s+", " ", s.strip()).lower()


def phrases(path):
    if path.lower().endswith(".docx"):
        z = zipfile.ZipFile(path)
        raw = "\n".join(re.sub(r"<[^>]+>", "\n", z.read(n).decode("utf-8", "ignore")) for n in z.namelist() if n.startswith("word/") and n.endswith(".xml"))
    elif path.lower().endswith(".pdf"):
        raw = sh("pdftotext", "-layout", path, "-")
    else:
        raw = open(path, encoding="utf-8", errors="ignore").read()
    return {n for n in (norm(l) for l in raw.split("\n")) if len(n) >= 14}


def main():
    a = sys.argv[1:]
    sources, ignore, message, mode, rng = [], [], "", None, "HEAD"
    i = 0
    while i < len(a):
        if a[i] == "--source":
            sources.append(a[i + 1]); i += 2
        elif a[i] == "--ignore":
            ignore.append(norm(a[i + 1])); i += 2
        elif a[i] == "--message":
            message = a[i + 1]; i += 2
        elif a[i] == "--staged":
            mode = "staged"; i += 1
        elif a[i] == "--history":
            mode = "history"; i += 1
            if i < len(a) and not a[i].startswith("--"):
                rng = a[i]; i += 1
        else:
            sys.exit(__doc__)
    if not sources or not mode:
        sys.exit(__doc__)
    bad = set()
    for s in sources:
        bad |= phrases(s)
    bad -= set(ignore)
    jobs = []
    if mode == "staged":
        jobs.append(("staged", sh("git", "diff", "--cached", "--no-color", "-U0"), message))
    else:
        for c in sh("git", "rev-list", "--reverse", rng).split():
            jobs.append((c[:7], sh("git", "show", "--no-color", "-U0", "--format=", c), sh("git", "log", "-1", "--format=%B", c)))
    hits = 0
    for name, diff, msg in jobs:
        added = norm("\n".join(l[1:] for l in diff.split("\n") if l.startswith("+") and not l.startswith("+++")) + "\n" + msg)
        found = sorted(p for p in bad if re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", added))
        for p in found:
            hits += 1
            print(f"HIT {name}: {p[:30]!r}...")
    print(f"{len(jobs)} {'diff' if mode == 'staged' else 'commits'} checked against {len(bad)} private lines, {hits} hits")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
