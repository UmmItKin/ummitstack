#!/usr/bin/env python3
"""Scan prose for common AI-writing tells.

Usage: scan.py [--strong] [FILE ...]      (reads stdin when no file is given)

Skips YAML front matter, fenced code, inline code and URLs, so only prose is
checked. A file containing the marker <!-- unslop-ignore --> is skipped; use it
on files that list the tells themselves.

Each hit prints as  path:line:col strength id message: "text".
strong = act on one sighting. weak = act only when several share a passage.
Exit status is 1 when any strong tell is found, otherwise 0.
Patterns, causes and fixes are in references/patterns.md.
"""
import re, sys
from collections import namedtuple

I = re.I
ARROWS = "←↑→↓⇒⟶➜➡"
EMOJI = "[\U0001F300-\U0001FAFF✅❌✨⚠⭐]"

Rule = namedtuple("Rule", "id strength regex message")
RULES = [Rule(*r) for r in [
    ("contrast", "strong", re.compile(r"\bnot\s+(?:just|only|merely|simply)\b[^.\n]{0,100}?\bbut\b", I),
     "not X but Y: state the point directly"),
    ("contrast", "strong", re.compile(r"\b(?:it|this|that)(?:'s| is| isn't| is not)\s+not\b[^.\n;]{1,80}[,;]\s*(?:it|this|that)(?:'s| is)\b", I),
     "it's not X, it's Y: state the point directly"),
    ("contrast", "strong", re.compile(r"\b(?:it|this|that)(?:'s| is| isn't| is not)\s+not\b[^.\n]{1,80}\.\s+(?:It|This|That)(?:'s| is)\b"),
     "contrast split over two sentences: state the point directly"),
    ("closer", "strong", re.compile(r"^\W*(?:that(?:'s| is) the real (?:win|point|magic|lesson)|read that again|let that sink in|and that(?:'s| is) the point)\W*$", I),
     "one-line closer: cut it or merge its fact into the paragraph"),
    ("deep", "strong", re.compile(r"\b(?:the real question is|at its core|what really matters|the heart of the matter|the deeper issue)\b", I),
     "saying that sounds deep: replace it with the specific claim"),
    ("deep", "weak", re.compile(r"\b(?:fundamentally|in reality),", I), "sounds deep: check it adds a fact"),
    ("runup", "strong", re.compile(r"\b(?:let'?s dive|let'?s explore|let'?s break (?:this|it) down|here'?s what you need to know|without further ado|here'?s the thing|the thing is|let'?s be honest|real talk)\b", I),
     "run-up before the point: start with the point"),
    ("strawman", "strong", re.compile(r"\b(?:to be clear|don'?t get me wrong|i'?m not saying|this isn'?t (?:mainly )?about|a tempting approach|one might be tempted|you might think|it would be easy to just)\b", I),
     "arguing with no one: drop it or state the real claim"),
    ("dash", "strong", re.compile("[—–]|\\s--\\s"),
     "em dash, en dash or double hyphen: use a period, comma, colon or parentheses"),
    ("arrow", "strong", re.compile("[" + ARROWS + "]|(?<!-)(?:->|=>)|[-=]&gt;"),
     "arrow character in prose: write the word, or draw the arrow in a diagram"),
    ("emoji", "strong", re.compile(EMOJI), "emoji used as decoration: remove it"),
    ("chatbot", "strong", re.compile(r"\b(?:i hope this helps|certainly!|of course!|great question|you'?re absolutely right|let me know if|would you like me to|want me to\b|as an ai|as of my last|up to my last training)", I),
     "chatbot residue: remove the wrapper, keep the content"),
    ("words", "weak", re.compile(r"\b(?:delv(?:e|es|ed|ing)|tapestry|testament|pivotal|crucial|intricate|intricacies|vibrant|enduring|interplay|bolstered?|underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|fostering|garner(?:s|ed)?|meticulous(?:ly)?|align with)\b", I),
     "word models overuse: use a plainer one"),
    ("puff", "weak", re.compile(r"\b(?:plays? an? (?:key|crucial|vital|pivotal|significant) role|stands? as|serves? as|a testament to|nestled|boasts?|in the heart of|setting the stage|marking a|indelible mark|continues to thrive|future looks bright|exciting times|(?:evolving|changing|digital) landscape)\b", I),
     "inflated or roundabout phrase: say the fact, use is/are/has"),
    ("hedge", "weak", re.compile(r"\b(?:could potentially|might possibly|may potentially|might arguably|could possibly)\b", I),
     "stacked qualifiers: keep one, or none"),
    ("summary", "weak", re.compile(r"^\W*(?:in summary|in conclusion|overall|to summarize),", I),
     "summary opener: end on the last concrete fact"),
    ("limits", "weak", re.compile(r"\b(?:not publicly available|not widely documented|based on available information|in the provided sources|specific details are (?:limited|scarce))\b", I),
     "knowledge-limit wording: say what the source does not show, or cut it"),
    ("quotes", "weak", re.compile("[“”]"), "curly double quotes: use straight quotes unless the format needs them"),
    ("bold", "weak", re.compile(r"^\s*(?:[-*]|\d+\.)\s+\*\*[^*\n]+\*\*"), "bold lead-in on a list item: keep only if the label carries information"),
]]

SMALL = {"a", "an", "the", "and", "or", "of", "in", "on", "to", "for", "with", "at", "by", "from", "but", "as", "is"}


def mask(text):
    lines, out, fence, front = text.split("\n"), [], False, False
    for n, line in enumerate(lines):
        if n == 0 and line.strip() == "---":
            front = True
            out.append(" " * len(line)); continue
        if front:
            if line.strip() == "---":
                front = False
            out.append(" " * len(line)); continue
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            out.append(" " * len(line)); continue
        if fence:
            out.append(" " * len(line)); continue
        line = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group()), line)
        line = re.sub(r"https?://\S+", lambda m: " " * len(m.group()), line)
        line = re.sub(r"(\]\()[^)]*(\))", lambda m: m.group(1) + " " * (len(m.group()) - 2) + m.group(2), line)
        out.append(line)
    return out


def scan(path, text):
    if "<!-- unslop-ignore -->" in text:
        return []
    hits, lines = [], mask(text)
    for n, line in enumerate(lines, 1):
        for rule in RULES:
            rid, strength, rx, msg = rule.id, rule.strength, rule.regex, rule.message
            for m in rx.finditer(line):
                hits.append((n, m.start() + 1, strength, rid, msg, m.group().strip()))
        h = re.match(r"^(#{1,6})\s+(.*\S)", line)
        if h:
            words = re.findall(r"[A-Za-z][A-Za-z'-]*", h.group(2))
            body = [w for w in words if w.lower() not in SMALL]
            if len(words) >= 4 and body and all(w[0].isupper() for w in body):
                hits.append((n, 1, "weak", "titlecase", "title case heading: use sentence case", h.group(2)))
    para, start = [], 0
    for n, line in enumerate(lines + [""], 1):
        if line.strip() and not re.match(r"^\s*(?:[-*|>#]|\d+\.)", line):
            if not para:
                start = n
            para.append(line.strip())
            continue
        if para:
            sents = [s for s in re.split(r"(?<=[.!?])\s+", " ".join(para)) if s]
            firsts = [re.match(r"\W*(\w+)", s).group(1).lower() for s in sents if re.match(r"\W*(\w+)", s)]
            for i in range(len(firsts) - 2):
                if firsts[i] == firsts[i + 1] == firsts[i + 2]:
                    hits.append((start, 1, "weak", "openings", "three sentences in a row start the same way", firsts[i]))
                    break
        para = []
    hits.sort()
    return [(path,) + h for h in hits]


def main():
    args = sys.argv[1:]
    strong_only = "--strong" in args
    files = [a for a in args if a != "--strong"]
    sources = [(f, open(f, encoding="utf-8").read()) for f in files] or [("<stdin>", sys.stdin.read())]
    strong = weak = 0
    for path, text in sources:
        for p, n, c, strength, rid, msg, snippet in scan(path, text):
            if strength == "weak" and strong_only:
                continue
            strong += strength == "strong"
            weak += strength == "weak"
            print(f'{p}:{n}:{c} {strength} {rid} {msg}: "{snippet[:60]}"')
    print(f"strong: {strong}, weak: {weak}")
    sys.exit(1 if strong else 0)


if __name__ == "__main__":
    main()
