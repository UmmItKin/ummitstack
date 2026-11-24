#!/usr/bin/env python3
"""Render a review-pr report (JSON on stdin) into one self-contained HTML page.

Every string from the JSON is HTML-escaped: PR titles, diffs and paths can be
attacker-controlled. Screenshots are embedded as base64 data URIs, so the page
is one file with no network requests. Dark style follows ummit.dev:#0d1117
background, dot grid, Google Sans fonts when installed, roboto/system fallbacks.

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
:root{color-scheme:dark;--bg:#0d1117;--panel:#161b22;--text:#bbbbbb;--dim:#9ca3af;--faint:#6b7280;
--line:rgba(125,125,125,.3);--line-strong:rgba(82,82,82,.7);--link:#fff;
--ok:#34d399;--warn:#eab308;--err:#f87171;
--sans:"Google Sans Flex","Google Sans",Roboto,"Noto Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
--mono:"Google Sans Code","Google Sans Mono","JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;min-height:100vh;position:relative;background:var(--bg);color:var(--text);
font:16px/1.7 var(--sans);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
background:linear-gradient(90deg,#0d1117 22px,transparent 1%) 50%,
linear-gradient(#0d1117 22px,transparent 1%) 50%,#2f353c;
background-position:center center;background-size:24px 24px;
mask-image:linear-gradient(0deg,transparent 5%,#000)}
a{color:var(--link);text-decoration:none;border-bottom:1px solid var(--line);transition:border-color .2s}
a:hover{border-color:rgba(125,125,125,.8)}
:focus-visible{outline:2px solid var(--link);outline-offset:2px}
header,main,footer{max-width:48rem;margin:0 auto;padding-left:1.5rem;padding-right:1.5rem}
header{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1rem;padding-top:1.5rem;padding-bottom:1.5rem}
header .brand{font-weight:700;font-size:1.25rem;color:var(--link)}
header .repo{opacity:.5}
header a{margin-left:auto;opacity:.7;border-bottom:none;transition:opacity .2s}
header a:hover{opacity:1}
main{padding-bottom:4rem}
h1{margin:2rem 0 1.5rem;font-size:2.25rem;font-weight:800;line-height:1.11;color:inherit}
section{margin:2.5rem 0 0;padding-top:1.5rem;border-top:1px solid var(--line)}
section h2{margin:0 0 1rem;font-size:1.5rem;font-weight:700;line-height:1.33}
.verdict{margin-top:1rem;padding-top:0;border-top:0;border-left:3px solid var(--line-strong);
padding-left:1rem}
.verdict.ok{border-left-color:var(--ok)}.verdict.warn{border-left-color:var(--warn)}
.verdict.err{border-left-color:var(--err)}
.verdict strong{display:block;font-size:1.5rem;font-weight:800;line-height:1.2}
.verdict.ok strong{color:var(--ok)}.verdict.warn strong{color:var(--warn)}
.verdict.err strong{color:var(--err)}
.verdict p{margin:.35rem 0 0;color:var(--dim)}
.verdict code{font:13px var(--mono);background:rgba(115,115,115,.15);border-radius:.25rem;padding:.15em .4em}
.chips{display:flex;flex-wrap:wrap;gap:.5rem}
.chip{display:inline-flex;align-items:center;gap:.35rem;padding:.25rem .6rem;border-radius:.25rem;
background:rgba(115,115,115,.15);font-size:.8125rem;line-height:1;white-space:nowrap}
.chip b{font-weight:600}
.chip.add,.chip.pass{color:var(--ok)}.chip.del,.chip.fail{color:var(--err)}
.chip.pending{color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:.875rem;line-height:1.7}
th,td{padding:.55rem .7rem;text-align:left;vertical-align:top;border-bottom:1px solid rgba(136,136,136,.13)}
th{padding-top:0;color:var(--dim);font-weight:600}
.sev{display:inline-block;padding:.15rem .8rem;border-radius:.25rem;font-size:.75rem;font-weight:600}
.sev.high{background:rgba(248,81,73,.15);color:var(--err)}
.sev.med{background:rgba(234,179,8,.15);color:var(--warn)}
.sev.low{background:rgba(52,211,153,.15);color:var(--ok)}
.sev.info{background:rgba(115,115,115,.15);color:var(--dim)}
code,pre{font-family:var(--mono)}
.findings .file{font:12px var(--mono);color:var(--faint);margin:.15rem 0}
.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}
figure{margin:0;border:1px solid var(--line);border-radius:.375rem;overflow:hidden;background:var(--panel)}
figure img{display:block;width:100%;height:auto}
figcaption{padding:.5rem .75rem;font-size:.8125rem;color:var(--dim)}
details{border:1px solid var(--line);border-radius:.375rem;margin:.75rem 0;overflow:hidden}
summary{cursor:pointer;display:flex;flex-wrap:wrap;align-items:baseline;gap:.6rem;
padding:.55rem .8rem;background:rgba(115,115,115,.08);font-weight:500}
summary .stats{margin-left:auto;font:12px var(--mono);color:var(--faint)}
pre{margin:0;overflow:auto;background:var(--panel);font-size:12.5px;line-height:1.6}
.dl{display:block;padding:0 .9rem;white-space:pre-wrap;word-break:break-word}
.dl.add{background:rgba(52,211,153,.09);color:#7ee2b8}
.dl.del{background:rgba(248,81,73,.09);color:#f0a3a0}
.dl.hunk{color:#8b949e;padding-top:.25rem}
footer{border-top:1px solid rgba(82,82,82,.5);padding-top:1rem;padding-bottom:2rem;font-size:.8125rem}
footer .meta{font:12px var(--mono);opacity:.5;margin-top:.35rem}
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
    repo = report.get("repo")
    pr = report.get("pr")

    parts = []
    parts.append('<!doctype html><html lang="en"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append("<title>Review %s #%s</title><style>%s</style></head><body>"
                 % (esc(repo), esc(pr), CSS))

    url = str(report.get("url") or "")
    link = ('<a href="%s">Open on GitHub</a>' % esc(url)
            if url.startswith(("http://", "https://")) else "")
    parts.append('<header><span class="brand">PR review</span><span class="repo">%s #%s</span>%s</header><main>'
                 % (esc(repo), esc(pr), link))
    parts.append("<h1>%s</h1>" % (esc(report.get("title")) or "(no title)"))

    parts.append('<section class="verdict %s"><strong>%s</strong><p>%s</p>'
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
        parts.append('<section><h2>At a glance</h2><div class="chips">%s</div></section>'
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
        parts.append('<section class="findings"><h2>Findings</h2>'
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
        parts.append('<section><h2>Result</h2><div class="shots">%s</div></section>'
                     % "".join(figs))

    if files:
        blocks = []
        for f in files:
            stats_txt = "+%s −%s" % (esc(f.get("added", 0)), esc(f.get("removed", 0)))
            lines = (f.get("diff") or "").count("\n") + 1
            opened = " open" if lines <= 80 else ""
            blocks.append('<details%s><summary>%s<span class="stats">%s</span></summary>'
                          '<pre>%s</pre></details>'
                          % (opened, esc(f.get("path")), stats_txt, diff_html(f.get("diff"))))
        parts.append('<section><h2>Diff</h2>%s</section>' % "".join(blocks))

    parts.append('</main><footer><div>Read-only review of %s #%s</div>'
                 '<div class="meta">generated %s</div></footer></body></html>'
                 % (esc(repo), esc(pr), esc(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))))
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
