---
name: asking-for-me-quiz
description: Use when the user asks for practice questions, a quiz, MC questions, multiple-choice questions, or multi-select questions on a topic, such as "出 10 題 OOP 的 MC", "quiz me on exceptions", or "做幾題多選". Produces one answer-me-with-html page with the questions, plus an answer key page section, and a PDF copy. Saves under "<course folder>/Gen-asking-for-me/Gen-asking-for-me-quiz/<Topic>/".
---

# Asking for me: quiz

The user asks for practice questions. You write the questions, the options, the answer key and short reasons. The page uses the `answer-me-with-html` style.

## When called by asking-for-me

If `asking-for-me` gives you a validated `run.json`, use its verified `quiz` items and skip step 3, writing the questions. Do not change an item's answer or options.

## Naming

Every page has a Topic: Title Case words with spaces, such as `Creating a Class`. Name the file `<Topic> - <Kind>.<ext>`, where Kind is `Exercise`, `Quiz` or `Study`. Use the same base name for the PDF. The kid markdown is `<Topic> - ELI5.md`. Add ` v2` when the same topic is made again. Do not use lowercase hyphenated names, and do not put dates in the file name.

## 1. Read the request

Set these values. Use the user's words when they give them. Otherwise use the defaults.

| Setting | Default | Notes |
|---|---|---|
| Topic | from the question | one topic per page |
| Count | 10 | 1 to 30 |
| Type | single-answer MC | `single`, `multi` (choose all that apply), or `mixed` |
| Options per question | 4 | 4 or 5 |
| Difficulty | medium | easy, medium or hard |
| Language | from the question | see step 2 |

For `mixed`, use about 70% single-answer and 30% multi-select.

## 2. Pick the language

There is no language folder. Write the questions in the language of the request, and keep the page in that language.

Folder: `<course folder>/Gen-asking-for-me/Gen-asking-for-me-quiz/<Topic>/`

`<course folder>` is the course the topic belongs to, such as `Java` or `Databases`. If the course is unclear, ask.

## 3. Write the questions

- Write every question yourself. Do not copy questions from the course slides, the sample papers or the solutions.
- Test one idea per question.
- Make the wrong options plausible. Use common mistakes, not silly answers.
- Keep the stem short: at most two sentences.
- Put code in a short Java or SQL block when the topic needs it. Use the code block form with `title="... · sketch"`.
- For a multi-select question, write `(select all that apply)` after the stem. Use 1 to 3 correct options.
- Do not show the answer in the question text.
- Vary the position of the correct answer. Do not put the answer at A every time.

## 4. Build the player (the style the user wants)

Use the standalone player as the template: `template.html` in this skill folder. It shows one question at a time, with progress, a hint, back and continue buttons, instant feedback with the reason, and a result page with a per-question review and a restart button.

1. Copy `template.html` to `<course folder>/Gen-asking-for-me/Gen-asking-for-me-quiz/<Topic>/<Topic> - Quiz.html`. Do not overwrite an existing file.
2. Replace the `QUESTIONS` array in its script. Each item has `q` (stem), `code` (optional: any Java code, shown in its own code block under the stem; put code here, not in `q`), `options` (array of 4 strings), `answer` (index 0 to 3), `hint` (one short nudge) and `why` (reason, under 25 words).
3. Update the `<h1>`, the `sub` line and the `source` line in the header to match the topic.
4. Check every `answer` index against `options` before you save. A wrong key is worse than no key.
5. Syntax-check the script: extract it with `awk` and run `node --check`.

The player supports single-answer questions only. For multi-select, say so and ask the user before adding checkboxes.

Do not render an answer table or a PDF for the player. The answers are shown in the feedback and the result review. The PDF copy only prints the current question, so skip it unless the user asks.

## 5. Check the player

Open the file in a browser, or run `node --check` on the script. Tell the user you have not run it in a browser, if that is the case.

## 6. Rules

- Do not overwrite an existing file. If the name is taken, add a suffix with the date.
- Do not commit unless the user asks.
- Do not reproduce long passages from the course material. Quote at most one short line when needed.
- Check every answer key line against the options before you render. A wrong key is worse than no key.

## 7. Reply

Reply in two or three lines in the user's language:

- The count and type: for example, "10 questions, 7 single-answer and 3 multi-select."
- The player link, as `[file:///abs/path.html](file:///abs/path.html)`.
