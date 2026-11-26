#!/usr/bin/env python3
"""Usage: static_check.py skill-dir
Checks one skill folder without running it: the frontmatter, the files it points to, the scripts and the text.
Prints ERROR and WARN lines. Exit 1 when there is any ERROR.
Errors: frontmatter missing or not valid YAML, name different from the folder, description empty or over 1024
characters, a script that does not compile, an em dash, an arrow or an emoji in the text,
a home directory path or an email address in any file.
Warnings: a script with no Usage line, a symbol such as a check mark, a script or reference that no other file mentions, a description without a "Use when" cue."""
import os, re, subprocess, sys

DASHES_ARROWS_EMOJI = re.compile("[\u2014\u2192\u2190\u21d2\u27a1\u2b05\U0001f300-\U0001faff]")
DINGBATS = re.compile("[\u2600-\u27bf]")
HOME_PATH = re.compile(r"(?<![\w.~$])/home/(?!user\b|you\b|name\b|username\b)[A-Za-z0-9_-]+|C:\\Users\\(?!user\b|you\b|name\b|username\b|Public\b|Default\b)[A-Za-z0-9_-]+|/Users/(?!user\b|you\b|name\b|username\b)[A-Za-z0-9_-]+")
EMAIL = re.compile(r"[\w.+-]+@(?!example\.)[\w-]+\.[\w.-]+")


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, ["SKILL.md has no frontmatter between --- lines"]
    errs, data = [], {}
    for line in m.group(1).split("\n"):
        k = re.match(r"([A-Za-z_-]+):\s*(.*)$", line)
        if not k:
            if line.strip() and not line.startswith(" "):
                errs.append(f"frontmatter line is not key: value: {line[:50]}")
            continue
        key, value = k.groups()
        if value and value[0] not in "\"'|>[{" and (": " in value or value.endswith(":") or " #" in value):
            errs.append(f"frontmatter {key}: an unquoted value with ': ' or ' #' is invalid YAML, reword it or quote it")
        data[key] = value.strip("\"'")
    try:
        import yaml
        yaml.safe_load(m.group(1))
    except ImportError:
        pass
    except Exception as e:
        errs.append(f"frontmatter is not valid YAML: {str(e).splitlines()[0]}")
    return data, errs


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = os.path.abspath(sys.argv[1])
    errors, warns = [], []
    skill_md = os.path.join(root, "SKILL.md")
    if not os.path.exists(skill_md):
        sys.exit(f"ERROR {root}: no SKILL.md")
    text = open(skill_md, encoding="utf-8").read()
    data, errs = frontmatter(text)
    errors += [f"SKILL.md: {e}" for e in errs]
    if data is not None:
        if data.get("name") != os.path.basename(root):
            errors.append(f"SKILL.md: name '{data.get('name')}' is not the folder name '{os.path.basename(root)}'")
        d = data.get("description", "")
        if not d or len(d) > 1024:
            errors.append(f"SKILL.md: description must be 1 to 1024 characters, it is {len(d)}")
        if d and not re.search(r"\b[Uu]se (when|for|whenever)\b|\bwhen the user\b", d):
            warns.append("SKILL.md: the description has no 'Use when' cue, so an agent may not pick the skill")

    files = []
    for base, _, names in os.walk(root):
        for n in names:
            files.append(os.path.join(base, n))
    rel = lambda p: os.path.relpath(p, root)
    texts = {}
    for p in files:
        if p.endswith((".md", ".py", ".sh", ".lua", ".json", ".txt", ".typ", ".tla", ".cfg")) and "__pycache__" not in p:
            texts[p] = open(p, encoding="utf-8", errors="replace").read()
    for p, t in texts.items():
        if DINGBATS.search(t):
            warns.append(f"{rel(p)}: contains a symbol character such as a check mark: {DINGBATS.search(t).group(0)!r}")
        for what, rx in (("an em dash, arrow or emoji", DASHES_ARROWS_EMOJI), ("a home directory path", HOME_PATH), ("an email address", EMAIL)):
            m = rx.search(t)
            if m:
                errors.append(f"{rel(p)}: contains {what}: {m.group(0)!r}")

    for p in files:
        if "__pycache__" in p:
            continue
        if p.endswith(".py"):
            try:
                compile(texts[p], p, "exec")
            except SyntaxError as e:
                errors.append(f"{rel(p)}: does not compile: {e.msg} on line {e.lineno}")
            if "Usage" not in "\n".join(texts[p].split("\n")[:25]) and "scripts" in rel(p).split(os.sep)[0:1]:
                warns.append(f"{rel(p)}: no Usage line in the first 25 lines")
        elif p.endswith(".sh"):
            r = subprocess.run(["sh", "-n", p], capture_output=True, text=True)
            if r.returncode:
                errors.append(f"{rel(p)}: sh -n failed: {r.stderr.strip()[:100]}")
            if "scripts" in rel(p).split(os.sep)[0:1] and "Usage" not in "\n".join(texts.get(p, "").split("\n")[:25]):
                warns.append(f"{rel(p)}: no Usage line in the first 25 lines")

    others = {p: t for p, t in texts.items()}
    for p in files:
        parts = rel(p).split(os.sep)
        if parts[0] in ("scripts", "references") and "__pycache__" not in p:
            name = os.path.basename(p)
            stem = os.path.splitext(name)[0]
            if not any(name in t or f"import {stem}" in t or f"from {stem} import" in t for q, t in others.items() if q != p):
                warns.append(f"{rel(p)}: no other file mentions it, so an agent will not know to use it")

    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    print(f"{os.path.basename(root)}: {len(errors)} errors, {len(warns)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
