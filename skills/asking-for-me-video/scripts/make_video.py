#!/usr/bin/env python3
"""Build an answer-me-with-html video whose narration is spoken by the Gemini TTS API.

Usage:
  python3 make_video.py draft.md --out page.html [--voice Kore] [--model gemini-3.8-flash-tts]

1. `am video` renders the draft with `--voice off` to get the scenes and one beat per `>` line.
2. Each beat's text goes to the Gemini TTS API as WAV.
3. The beat timings are rewritten to the real clip lengths, and the audio is replaced by the joined clips.
The API key is read from $GEMINI_API_KEY or ~/.config/watch/.env. It is never printed.
"""
import argparse, base64, json, os, pathlib, re, subprocess, sys, tempfile, time, urllib.request

AM = pathlib.Path.home() / ".claude/skills/answer-me-with-html/scripts/am.mjs"


CODE_CSS = """<style>
.amv-ln-hl { display: block; background: var(--accent-bg); box-shadow: inset 5px 0 0 var(--accent); }
.amv-ln-dim { opacity: .35; }
::highlight(amv-tok) { background-color: var(--accent); color: var(--bg, #fff); }
</style>"""
CODE_JS = """  function drawCode(t) {
    const cur = segs.findLastIndex((s) => t >= s.start);
    const b = cur >= 0 ? segs[cur].beats.find((x) => t >= x.start && t < x.end + 0.3) : null;
    // the caption HTML escapes " ' < > &; decode, or names such as getParameter("id") never match the code text
    const dec = document.createElement('textarea');
    const names = b ? [...b.html.matchAll(/<b>(.*?)<\\/b>/g)].map((m) => { dec.innerHTML = m[1]; return dec.value.toLowerCase(); }) : [];
    const ranges = [];
    scenes.forEach((sc, i) => {
      const lines = [...sc.querySelectorAll('.am-ln')];
      const hits = lines.map((l) => i === cur && names.some((n) => l.textContent.toLowerCase().includes(n)));
      lines.forEach((l, k) => {
        l.classList.toggle('amv-ln-hl', hits[k]);
        l.classList.toggle('amv-ln-dim', hits.some(Boolean) && !hits[k]);
        if (!hits[k]) return;
        const text = l.textContent.toLowerCase();
        for (const n of names) for (let at = text.indexOf(n); at >= 0; at = text.indexOf(n, at + n.length)) {
          const r = new Range();
          r.setStart(l.firstChild, at); r.setEnd(l.firstChild, at + n.length);
          ranges.push(r);
        }
      });
    });
    if (window.CSS && CSS.highlights) CSS.highlights.set('amv-tok', new Highlight(...ranges));
  }

"""


ERROR_CSS = """<style>
.amv-err-wrap { position: absolute; left: 0; right: 0; top: 170px; display: flex; justify-content: center; pointer-events: none; }
.amv-err { min-width: 900px; max-width: 1500px; padding: 22px 30px; border-radius: var(--radius); background: var(--paper, #fff);
  border: 4px solid var(--danger, #c62828); box-shadow: 0 10px 30px rgba(0, 0, 0, .18); opacity: 0; visibility: hidden; }
.amv-err-head { font: 700 30px var(--font-sans); color: var(--danger, #c62828); margin-bottom: 12px; }
.amv-err-body { margin: 0; font: 500 34px/1.45 ui-monospace, Menlo, monospace; color: var(--ink, #111); white-space: pre-wrap; min-height: 1.45em; }
</style>"""
ERROR_JS = """  const errWrap = document.createElement('div');
  errWrap.className = 'amv-err-wrap';
  errWrap.innerHTML = '<div class="amv-err"><div class="amv-err-head">&#10006; 編譯錯誤 Compile error</div><pre class="amv-err-body"></pre></div>';
  stage.append(errWrap);
  const errCard = errWrap.firstElementChild;
  const errBody = errCard.querySelector('.amv-err-body');
  function drawError(t) {
    const cur = segs.findLastIndex((s) => t >= s.start);
    const b = cur >= 0 ? segs[cur].beats.findLast((x) => x.error && t >= x.start) : null;
    if (!b || t >= segs[cur].end) { errCard.style.opacity = 0; errCard.style.visibility = 'hidden'; return; }
    const since = t - b.start;
    const p = ease(since / 0.4);
    const shake = since > 0.4 ? 10 * Math.exp(-(since - 0.4) * 6) * Math.sin((since - 0.4) * 60) : 0;
    errCard.style.opacity = p;
    errCard.style.visibility = 'visible';
    errCard.style.transform = `translate(${shake}px, ${(1 - p) * 40}px)`;
    const n = Math.min(b.error.length, Math.max(0, Math.floor((since - 0.4) / 0.03)));
    errBody.textContent = b.error.slice(0, n);
  }

"""


def add_code_highlight(html):
    # Limit: assumes each code line is one text node (true while the renderer does no syntax colouring)
    html, n = re.subn(r"(  function render\(time\) \{)", lambda m: CODE_JS + m.group(1), html, count=1)
    assert n == 1, "render() not found; the renderer changed"
    # the renderer shows one step on the last beat; a code block must be there from the first, or early mentions hit a blank scene
    carried = "  const carried = new Set(morphs.map((m) => m.to));"
    assert carried in html, "renderer changed"
    html = html.replace(carried, carried + "\n  for (const it of items) if (it.el.matches('.am-codeblock')) it.at = segs[it.scene].beats[0].start;", 1)
    html = html.replace("    drawCaption(t);\n    updateUi(t);", "    drawCaption(t);\n    drawCode(t);\n    drawError(t);\n    updateUi(t);", 1)
    html, n = re.subn(r"(  function render\(time\) \{)", lambda m: ERROR_JS + m.group(1), html, count=1)
    assert n == 1, "render() not found; the renderer changed"
    return html.replace("</head>", CODE_CSS + ERROR_CSS + "</head>", 1)


def rehash_csp(html):
    """The page's CSP allows inline scripts by hash; recompute them after the scripts were edited, or the browser blocks the player."""
    import hashlib
    hashes = [base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()
              for s in re.findall(r"<script>(.*?)</script>", html, re.S)]
    html, n = re.subn(r"script-src [^;\"]*", lambda _: "script-src " + " ".join(f"'sha256-{h}'" for h in hashes), html, count=1)
    assert n == 1, "CSP script-src not found; the renderer changed"
    return html


def prepare_draft(text):
    """Strip the video-only directives and tag each flagged beat with its scene's error text.

    `>! text`   a narration beat that also shows the error card
    `@error ...` the card text for the scene it sits in (one per scene)
    Returns the clean draft, the error text per scene, and (beat index, scene) for each flagged beat.
    The beat index counts `>` lines in order, which is the order the renderer makes beats in.
    """
    out, errors, flagged, scene, beat = [], {}, [], 0, 0
    for line in text.splitlines():
        if line.startswith("## "):
            scene += 1
        if line.startswith("@error "):
            errors[scene] = line[len("@error "):].strip()
            continue
        if line.startswith(">"):
            if line.startswith(">!"):
                flagged.append((beat, scene))
                line = ">" + line[2:]
            beat += 1
        out.append(line)
    return "\n".join(out) + "\n", errors, flagged


def api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env = pathlib.Path.home() / ".config/watch/.env"
        m = re.search(r"^GEMINI_API_KEY=(.+)$", env.read_text(encoding="utf-8"), re.M)
        if not m:
            sys.exit("GEMINI_API_KEY not found in environment or ~/.config/watch/.env")
        key = m.group(1).strip().strip("\"'")
    return key


def tts(text, voice, model, key):
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            return base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(3)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="Kore")
    ap.add_argument("--model", default="gemini-3.8-flash-tts")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; choose another name")

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="amv-"))
    clean, errors, flagged = prepare_draft(pathlib.Path(a.draft).read_text(encoding="utf-8"))
    draft = tmp / "draft.md"
    draft.write_text(clean, encoding="utf-8")
    silent = tmp / "silent.html"
    subprocess.run(["node", str(AM), "video", str(draft), "--voice", "off", "--no-open", "-o", str(silent)], check=True)
    html = silent.read_text(encoding="utf-8")
    m = re.search(r'(<script type="application/json" id="amv-data">)(.*?)(</script>)', html, re.S)
    data = json.loads(m.group(2))
    beats = [b for seg in data["segments"] for b in seg["beats"]]
    for k, sc in flagged:
        if sc not in errors:
            sys.exit(f"beat {k} is marked >! but its scene has no @error line")
        beats[k]["error"] = errors[sc]

    key = api_key()
    clips = []
    for i, b in enumerate(beats, 1):
        raw = tmp / f"raw-{i:02d}.wav"
        raw.write_bytes(tts(b["text"], a.voice, a.model, key))
        clip = tmp / f"clip-{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ar", "24000", "-ac", "1", str(clip)], check=True)
        clips.append(clip)
        print(f"voice {i}/{len(beats)}", file=sys.stderr)

    listing = tmp / "list.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    joined = tmp / "narration.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)], check=True)

    t = 0.0
    for b, c in zip(beats, clips):
        d = duration(c)
        b["start"], b["end"] = round(t, 3), round(t + d - 0.05, 3)
        t += d
    for seg in data["segments"]:
        seg["start"], seg["end"] = seg["beats"][0]["start"], seg["beats"][-1]["end"]
    data["duration"] = round(t, 3)

    html = html[:m.start(2)] + json.dumps(data, ensure_ascii=False) + html[m.end(2):]
    b64 = base64.b64encode(joined.read_bytes()).decode()
    audio_tag = f'<audio id="amv-audio" preload="auto" src="data:audio/wav;base64,{b64}"></audio>'
    if '<audio id="amv-audio"' in html:
        html, n = re.subn(r'<audio id="amv-audio"[^>]*></audio>', lambda _: audio_tag, html, count=1)
        assert n == 1
    else:
        html = html.replace('<textarea id="am-source"', audio_tag + '<textarea id="am-source"', 1)
    out.write_text(rehash_csp(add_code_highlight(html)), encoding="utf-8")
    print(f"wrote {out}  beats={len(beats)}  duration={t:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
