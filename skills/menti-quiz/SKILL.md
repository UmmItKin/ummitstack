---
name: menti-quiz
description: Use when the user types /menti-quiz or asks to join, follow or answer a live Mentimeter quiz (menti.com with a join code). Opens the quiz in agent-browser, waits for each question, answers it, screenshots it, saves one .md per question and commits.
---

# Menti quiz runner

## Start

```sh
agent-browser --headed --executable-path /usr/bin/chromium --profile ~/.agent-browser-profile open "https://www.menti.com"
agent-browser fill "input[name=id]" "<join code>"
agent-browser click "button[type=submit]"
agent-browser get title
```

Codes are 8 digits, typed with a space (`1234 5678`). Report the quiz title and URL in one line.

## Watch for questions

Run one poller only. Two loops calling agent-browser at once contend and silently drop polls. Use a Monitor (one notification per question), 15 min timeout, re-arm when it expires:

```sh
prev=""
while true; do
  q=$(agent-browser get text h1 2>/dev/null)
  case "$q" in *"respond in time"*|*results*|*"Respond quickly"*|*Correct*|*"Loading result"*|*"Let's see"*|"") q="";; esac
  if [ -n "$q" ] && [ "$q" != "$prev" ]; then
    opts=$(agent-browser snapshot 2>/dev/null | grep 'button "' | grep -v -e 'Open Q&A' -e 'Share code' -e 'Change appearance' | sed -n 's/^ *- button "\([^"]*\)".*/\1/p' | paste -sd '|' -)
    echo "QUESTION: $q"
    echo "OPTIONS: $opts"
  fi
  prev="$q"
  sleep 1
done
```

The OPTIONS line can come back empty when the snapshot runs before the buttons render, so the loop retries the snapshot four times before giving up. When it is still empty, read the options with a fresh snapshot on arrival.

## Answer

1. Read the options:
   ```sh
   agent-browser snapshot 2>/dev/null | grep 'button "' | grep -v -e 'Open Q&A' -e 'Share code' -e 'Change appearance'
   ```
2. Pick the correct option. Distractors are usually absurd, but read all four.
3. Do not add a sleep. The agent's own latency between the notification and the click already takes 5 to 10 seconds, which is the delay the user wants. Adding `sleep 8` pushed one answer to 27 seconds and others past the timer.
4. Click in one command: fresh snapshot, match the option text to its ref, click. Refs go stale the moment the question ends, and each extra call costs seconds the timer does not have. The question screenshot is already taken by the watcher, so do not repeat it here:
   ```sh
   ref=$(agent-browser snapshot 2>/dev/null | grep 'button "<option text>"' | sed -n 's/.*\[ref=\([^]]*\)\].*/\1/p' | head -1)
   agent-browser click "@$ref"
   ```
5. Capture the result screen. It shows the response time Menti recorded:
   ```sh
   agent-browser screenshot "<Course folder>/Menti Quiz/<YYYY-MM-DD> <slug> result.png"
   agent-browser read | head -6
   ```
   Put the seconds into `response time` in the frontmatter and the result image path in `screenshot result`.

The question window is usually about 20 seconds, and some questions close sooner. Missing it shows "You didn't respond in time"; record that entry as missed and move on.

## Record

One `.md` per question in `<Course folder>/Menti Quiz/`, plus its screenshot.

Frontmatter: `date`, `time` (YYYY-MM-DD HH:MM:SS, seconds taken from the screenshot's `stat -c %y`), `course`, `quiz`, `platform: Mentimeter`, `join code`, `question`, `answer`, `points`, `response time` when Menti shows one, `result`, `screenshot`, `sources`.

Body: question, the four options, the answer, a short why, references. Plain prose, checked with `unslop-writing`: no em dashes, no "not X but Y", no bold labels, no three-item padding.

Missed questions still get a full entry, with `result: missed, <reason>` and the correct answer. If the options were never captured, say so in the entry.

## Commit

One commit per question:

```
<Course>: add Menti quiz answer on <topic>

Question: <full question text>
```

## Pitfalls

- agent-browser commands only. No `eval` and no injected JS; the user asked for plain agent-browser.
- Do not screenshot the moment the heading appears. Options render a second or two later; a too-early screenshot misses them.
- A snapshot taken before the wait has stale refs by click time. Always re-snapshot right before clicking, or the click fails with "Could not locate element".
- A background clicker that picks answers by keyword rules misses most topics. Have the agent read the question and choose.
- Keep `~/.agent-browser-profile`; it holds the saved Menti login.
