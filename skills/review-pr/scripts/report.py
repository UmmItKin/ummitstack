#!/usr/bin/env python3
"""Render a review-pr report (JSON on stdin) into one self-contained HTML page.

Every string from the JSON is HTML-escaped: PR titles, diffs and paths can be
attacker-controlled. Screenshots are embedded as base64 data URIs, so the page
is one file with no network requests. Material style, light or dark follows the
system.

Usage: report.py [-o out.html] < report.json   (prints the output path)

JSON shape:
{
  "repo": "owner/name", "pr": 123, "title": "...", "author": "login",
  "url": "https://github.com/owner/name/pull/123", "state": "OPEN",
  "draft": false, "base": "main", "head": "feat/x",
  "stats": {"files": 3, "additions": 40, "deletions": 5, "commits": 2},
  "verdict": "good|caution|blocked", "summary": "one line, why",
  "checks": [{"name": "CI", "status": "pass|fail|pending"}],
  "findings": [{"severity": "high|med|low|info", "file": "src/a.ts",
                "line": 12, "title": "...", "body": "..."}],
  "screenshots": [{"path": "/tmp/shot.png", "caption": "Home at 1440 px"}],
  "files": [{"path": "src/a.ts", "added": 10, "removed": 2, "diff": "@@ ..."}]
}
"""
import base64, datetime, html, json, os, sys

CSS = """
:root{--primary:#6750A4;--on-primary:#fff;--primary-container:#EADDFF;--on-primary-container:#21005D;
--surface:#FFFBFE;--surface-2:#F3EDF7;--on-surface:#1C1B1F;--on-surface-variant:#49454F;
--outline:#79747E;--outline-variant:#CAC4D0;--ok:#146C2E;--ok-bg:#E8F5E9;--warn:#7A5900;
--warn-bg:#FFF8E1;--err:#B3261E;--err-bg:#F9DEDC;--add:#E6F4EA;--del:#FCE8E6;
--shadow:0 1px 2px rgba(0,0,0,.3),0 1px 3px 1px rgba(0,0,0,.15)}
@media (prefers-color-scheme:dark){:root{--primary:#D0BCFF;--on-primary:#381E72;--primary-container:#4F378B;
--on-primary-container:#EADDFF;--surface:#1C1B1F;--surface-2:#2B2930;--on-surface:#E6E1E5;
--on-surface-variant:#CAC4D0;--outline:#938F99;--outline-variant:#49454F;--ok:#7BD88F;--ok-bg:#1B3323;
--warn:#F2C94C;--warn-bg:#352C12;--err:#F2B8B5;--err-bg:#3B1B19;--add:#1E3B2A;--del:#3B1E1C}}
*{box-sizing:border-box}body{margin:0;background:var(--surface-2);color:var(--on-surface);
font:15px/1.55 Roboto,"Roboto Flex",system-ui,-apple-system,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:1;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;
padding:14px 24px;background:var(--primary);color:var(--on-primary);box-shadow:var(--shadow)}
header h1{margin:0;font-size:20px;font-weight:500}header .repo{opacity:.85;font-size:14px}
header a{color:var(--on-primary);margin-left:auto;font-weight:500}
main{max-width:1080px;margin:0 auto;padding:24px 16px 56px;display:flex;flex-direction:column;gap:16px}
.card{background:var(--surface);border-radius:16px;padding:20px 24px;box-shadow:var(--shadow)}
h2{margin:0 0 12px;font-size:16px;font-weight:500;letter-spacing:.1px}
.verdict{border-left:6px solid var(--outline)}.verdict.ok{border-color:var(--ok);background:var(--ok-bg)}
.verdict.warn{border-color:var(--warn);background:var(--warn-bg)}
.verdict.err{border-color:var(--err);background:var(--err-bg)}
.verdict strong{display:block;font-size:22px;font-weight:600}.verdict.ok strong{color:var(--ok)}
.verdict.warn strong{color:var(--warn)}.verdict.err strong{color:var(--err)}
.verdict p{margin:6px 0 0;color:var(--on-surface-variant)}
.verdict code{background:var(--surface);border:1px solid var(--outline-variant);border-radius:6px;
padding:2px 6px;font:13px/1.4 ui-monospace,monospace}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;gap:6px;align-items:center;padding:6px 12px;border-radius:100px;
background:var(--surface-2);border:1px solid var(--outline-variant);font-size:13px}
.chip b{font-weight:600}.chip.add{color:var(--ok)}.chip.del{color:var(--err)}
.chip.pass{background:var(--ok-bg)}.chip.fail{background:var(--err-bg)}
.chip.pending{background:var(--warn-bg)}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{padding:8px 10px;border-bottom:1px solid var(--outline-variant);text-align:left;vertical-align:top}
th{color:var(--on-surface-variant);font-weight:500}
.sev{display:inline-block;padding:2px 8px;border-radius:100px;font-size:12px;font-weight:600}
.sev.high{background:var(--err-bg);color:var(--err)}.sev.med{background:var(--warn-bg);color:var(--warn)}
.sev.low{background:var(--ok-bg);color:var(--ok)}.sev.info{background:var(--surface-2);color:var(--on-surface-variant)}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.findings .file{font-size:12px;color:var(--on-surface-variant)}
.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
figure{margin:0;background:var(--surface-2);border:1px solid var(--outline-variant);border-radius:12px;overflow:hidden}
figure img{display:block;width:100%;height:auto}
figcaption{padding:8px 12px;font-size:13px;color:var(--on-surface-variant)}
details{border:1px solid var(--outline-variant);border-radius:12px;margin:10px 0;overflow:hidden}
summary{cursor:pointer;padding:10px 14px;background:var(--surface-2);font-weight:500;
display:flex;gap:10px;flex-wrap:wrap;align-items:baseline}
summary .stats{margin-left:auto;font:13px ui-monospace,monospace;color:var(--on-surface-variant)}
pre{margin:0;padding:12px 0;overflow:auto;background:var(--surface);font-size:12.5px;line-height:1.45}
.dl{display:block;padding:0 14px;white-space:pre-wrap;word-break:break-word}
.dl.add{background:var(--add)}.dl.del{background:var(--del)}.dl.hunk{color:var(--primary)}
footer{max-width:1080px;margin:0 auto;padding:0 16px 32px;font-size:12px;color:var(--on-surface-variant)}
"""

VERDICTS = {
    "good": ("ok", "Good to go"),
    "caution": ("warn", "Caution"),
    "blocked": ("err", "Blocked"),
}
CHECK_MARK = {"pass": "✓", "fail": "✗", "pending": "…"}


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def diff_html(text):
    out = []
    for line in (text or "").split("\n"):
        cls = ""
        if line.startswith("+") and not line.startswith("+++"):
            cls = "add"
        elif line.startswith("-") and not line.startswith("---"):
            cls = "del"
        elif line.startswith("@@"):
            cls = "hunk"
        out.append('<span class="dl %s">%s</span>' % (cls, esc(line) or "&nbsp;"))
    return "".join(out)


def image_data(path):
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    mime = "image/jpeg" if os.path.splitext(str(path))[1].lower() in (".jpg", ".jpeg") else "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def render(report):
    verdict = str(report.get("verdict", "caution"))
    vcls, vlabel = VERDICTS.get(verdict, VERDICTS["caution"])
    stats = report.get("stats") or {}
    checks = report.get("checks") or []
    findings = report.get("findings") or []
    screenshots = report.get("screenshots") or []
    files = report.get("files") or []

    parts = []
    parts.append('<!doctype html><html lang="en"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append("<title>Review %s #%s</title><style>%s</style></head><body>"
                 % (esc(report.get("repo")), esc(report.get("pr")), CSS))

    title = esc(report.get("title")) or "(no title)"
    url = str(report.get("url") or "")
    link = ('<a href="%s">Open on GitHub</a>' % esc(url)
            if url.startswith(("http://", "https://")) else "")
    parts.append('<header><h1>%s</h1><span class="repo">%s #%s</span>%s</header><main>'
                 % (title, esc(report.get("repo")), esc(report.get("pr")), link))

    parts.append('<section class="card verdict %s"><strong>%s</strong><p>%s</p>'
                 % (vcls, vlabel, esc(report.get("summary"))))
    if verdict == "good":
        parts.append('<p>Merge with <code>/merge-pr-good-to-go</code>.</p>')
    parts.append("</section>")

    chips = []
    for label, key in (("Files", "files"), ("Commits", "commits"), ("Additions", "additions"),
                       ("Deletions", "deletions")):
        if key in stats:
            cls = "add" if key == "additions" else "del" if key == "deletions" else ""
            sign = "+" if key == "additions" else "-" if key == "deletions" else ""
            chips.append('<span class="chip %s">%s <b>%s%s</b></span>'
                         % (cls, label, sign, esc(stats.get(key))))
    for c in checks:
        status = str(c.get("status", "pending"))
        chips.append('<span class="chip %s">%s %s</span>'
                     % (status, CHECK_MARK.get(status, "•"), esc(c.get("name"))))
    if report.get("state"):
        chips.append('<span class="chip">%s</span>' % esc(report.get("state")))
    if report.get("draft"):
        chips.append('<span class="chip pending">Draft</span>')
    if report.get("base") or report.get("head"):
        chips.append('<span class="chip">%s ← %s</span>'
                     % (esc(report.get("base")), esc(report.get("head"))))
    if chips:
        parts.append('<section class="card"><h2>At a glance</h2><div class="chips">%s</div></section>'
                     % "".join(chips))

    if findings:
        rows = []
        for f in findings:
            where = esc(f.get("file"))
            if f.get("line"):
                where += ":%s" % esc(f.get("line"))
            rows.append('<tr><td><span class="sev %s">%s</span></td><td><b>%s</b>'
                        '<div class="file">%s</div><div>%s</div></td></tr>'
                        % (esc(f.get("severity", "info")), esc(f.get("severity", "info")),
                           esc(f.get("title")), where, esc(f.get("body"))))
        parts.append('<section class="card findings"><h2>Findings</h2>'
                     '<table><thead><tr><th>Severity</th><th>Detail</th></tr></thead><tbody>%s</tbody></table></section>'
                     % "".join(rows))

    if screenshots:
        figs = []
        for s in screenshots:
            data = image_data(s.get("path"))
            if data:
                figs.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>'
                            % (esc(data), esc(s.get("caption")), esc(s.get("caption"))))
            else:
                figs.append('<figure><figcaption>Missing screenshot: %s</figcaption></figure>'
                            % esc(s.get("path")))
        parts.append('<section class="card"><h2>Result</h2><div class="shots">%s</div></section>'
                     % "".join(figs))

    if files:
        blocks = []
        for f in files:
            stats_txt = "+%s −%s" % (esc(f.get("added", 0)), esc(f.get("removed", 0)))
            blocks.append('<details><summary>%s<span class="stats">%s</span></summary>'
                          '<pre>%s</pre></details>'
                          % (esc(f.get("path")), stats_txt, diff_html(f.get("diff"))))
        parts.append('<section class="card"><h2>Diff</h2>%s</section>' % "".join(blocks))

    parts.append("</main><footer>Read-only review of %s #%s, generated %s.</footer></body></html>"
                 % (esc(report.get("repo")), esc(report.get("pr")),
                    esc(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))))
    return "".join(parts)


def main():
    out = None
    args = sys.argv[1:]
    if args[:1] == ["-o"] and len(args) > 1:
        out = args[1]
    try:
        report = json.load(sys.stdin)
    except json.JSONDecodeError as err:
        sys.exit("error: report is not valid JSON (%s)" % err)
    if not out:
        directory = os.path.expanduser("~/.review-pr")
        os.makedirs(directory, exist_ok=True)
        name = str(report.get("repo") or "repo").replace("/", "-")
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        out = os.path.join(directory, "%s-pr%s-%s.html" % (name, report.get("pr", 0), stamp))
    page = render(report)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(os.path.abspath(out))


if __name__ == "__main__":
    main()
