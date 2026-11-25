---
name: asking-for-me-video
description: Use when the user asks for an animated video lesson, "asking-for-me-video", or an explainer video with human-sounding narration on any topic, in any course. Produces one standalone HTML video page whose narration is spoken by the Gemini TTS API, using the same scenes and beats as the answer-me-with-html video mode. Saves under "<course folder>/Gen-asking-for-me/Gen-asking-for-me-video/<Topic>/".
---

# Asking for me: video

The user asks for an animated video lesson. You write a short video draft, and a script makes the narration with the Gemini API (a real voice, not espeak). The output is one HTML page: animated scenes, with the narration timed to the real audio.

## When called by asking-for-me

If `asking-for-me` gives you a validated `run.json`, write the video draft from its verified `claims` items and add no claims of your own.

## Naming

Name the file `<Topic> - Video.html`. Put it in `<course folder>/Gen-asking-for-me/Gen-asking-for-me-video/<Topic>/`, where `<course folder>` is the course the topic belongs to, such as `Java` or `Databases`. If the course is unclear, ask. Use Title Case topic names, no dates, and ` v2` for a repeat. Do not overwrite an existing file.

## 1. Read the request

| Setting | Default | Notes |
|---|---|---|
| Topic | from the question | one topic per video |
| Scenes | 3 | 3 to 6 |
| Voice | Kore | any Gemini prebuilt voice name |
| Language | from the question | Traditional Chinese for Chinese questions |

## 2. Write the draft

Write the draft in answer-me-with-html video format, in a temporary file such as `/tmp/<topic>-video.md`:

- Frontmatter: `title`, `subtitle`, `lang`.
- Each `## ` heading is one scene. Put one component under it: a `flow`, `tree` or `er` block works best.
- When the topic is about code or a query language, put the code itself in the scene as a fenced block in that language, such as ```` ```java ````, ```` ```sql ````, or ```` ```python ```` (the video shows it). Use real, short code (under 15 lines) with `//` comments that mark what is right or wrong. Prefer a code block over a `flow` diagram for code questions.
- Each line that starts with `>` is one narration beat. One beat is one or two short sentences, spoken aloud.
- Write `[name]` in narration to highlight a node. The name must match the node text.
- Keep 3 to 6 scenes and about 9 to 14 beats in total.
- A scene can hold a code block instead of a diagram. The script then shows the block from the scene's first beat and, on each beat, lights the lines that contain the `[name]`s, dims the rest and marks the names. Write `[name]` exactly as it appears in the code, and keep the block to 3 to 8 lines.
- To show a compiler error, add one `@error <message>` line under the scene's `## ` heading, and write the beat that reports it as `>! <narration>` (note the `!`). The script shows an error card with that message on that beat, typed out with a shake, and keeps it until the scene ends. Use it for "this does not compile" or "this query fails" moments, with the real wording from the compiler, interpreter or database. The card is always labelled 編譯錯誤 Compile error, so do not use it for runtime exceptions such as NullPointerException; say those in the narration instead.
- A full program answer (for example a whole test answer) is too small to read in one scene. Split the tested source into consecutive scenes of at most 12 lines that together cover every line, then add one last scene with the whole program to pause on. Up to about 40 lines stays readable at 1920×1080.
- Teaching flow, not a list of facts: each scene shows the bad code first, then the reason, then the fix. Use 2 to 3 beats per scene so each idea gets time on screen.
- Write every line yourself. Do not copy text from the course slides or the sample papers.

Example:

```markdown
---
title: Abstract Class
lang: zh-TW
---
> 我們用三個小場景，理解 abstract class。

## 箱子的型別
```flow LR
Animal -> Dog: Animal a = new Dog();
```
> 先看 [Animal]。這是箱子上寫的型別。
> 再看 [Dog]。這是真正放進箱子的東西。
```

## 3. Build the video

Run the bundled script. It reads the API key from `GEMINI_API_KEY` or `~/.config/watch/.env`, and it never prints the key:

```bash
python3 "<skill folder>/scripts/make_video.py" /tmp/<topic>-video.md --out "<folder>/<Topic> - Video.html" --voice Kore
```

The script renders the scenes with `am video --voice off`, makes one Gemini clip for each beat, measures each clip, rewrites the beat times to match the real audio, and embeds the joined WAV into the page. Each beat is then shown while its own clip plays.

If the script fails with a 404 or a model error, run the model check first and pick a TTS model that the key can use, such as `gemini-3.8-flash-tts`, then pass it with `--model`.

## 4. Check the video

- Sample frames: open a copy of the page with agent-browser, run `agent-browser eval "render(<seconds>)"`, then `agent-browser screenshot`. (Headless Chromium with an appended `render()` script stays on frame 0:00.) Pick times inside the flagged beats to check the error card.

- Open the page in a browser if you can. If you cannot, say so in the reply.
- Check the duration printed by the script. It should be close to the total length of the narration.
- Confirm that the scenes change with the narration. If a scene is wrong, fix the draft and run the script again with a new `--out` name.

## 5. Rules

- Do not overwrite an existing file. If the name is taken, add ` v2`.
- Do not commit unless the user asks.
- Do not reproduce long passages from the course material or other sites.
- Never print or store the API key.

## 6. Reply

Reply in two or three lines in the user's language:

- The topic, the number of scenes and beats, and the total duration.
- The page link, as `[file:///abs/path.html](file:///abs/path.html)`.
- Whether you have opened it in a browser.
