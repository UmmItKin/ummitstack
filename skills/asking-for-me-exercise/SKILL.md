---
name: asking-for-me-exercise
description: Use when the user asks for fill-in-the-blank practice, coding exercises, "drag the correct word into the blank", or a single-page exercise set on a topic, such as "做 3 條 Java 填空題" or "exercise on inheritance". Produces one self-contained interactive HTML page with fill-in-the-blank exercises (click or drag a word into the blank, then check). Saves under "<course folder>/Gen-asking-for-me/Gen-asking-for-me-exercise/<Topic>/".
---

# Asking for me: exercise

The user asks for fill-in-the-blank exercises. You write the code lines, the word choices, the answer and a short reason. The page is one standalone HTML file with the same dark card style as the quiz player.

## When called by asking-for-me

If `asking-for-me` gives you a validated `run.json`, use its verified `blank` items and skip step 3, writing the exercises. Do not change an item's answer or options.

## Naming

Every page has a Topic: Title Case words with spaces, such as `Creating a Class`. Name the file `<Topic> - <Kind>.<ext>`, where Kind is `Exercise`, `Quiz` or `Study`. Put the HTML and PDF of one topic in a folder named after the Topic, for example `Java Expect/Java Expect - Exercise.html`. There are no language folders. Use the same base name for the PDF. The kid markdown is `<Topic> - ELI5.md`. Add ` v2` when the same topic is made again. Do not use lowercase hyphenated names, and do not put dates in the file name.

## 1. Read the request

| Setting | Default | Notes |
|---|---|---|
| Topic | from the question | one topic per page |
| Count | 3 | 1 to 10 exercises on one page |
| Choices per blank | 4 | 3 to 5 |
| Difficulty | easy | easy, medium or hard |
| Language | from the question | see step 2 |

## 2. Pick the language

There is no language folder. Every exercise page is bilingual: write each text field in both English and Traditional Chinese, so one HTML file serves both. The 語言 dropdown picks which one shows.

Folder: `<course folder>/Gen-asking-for-me/Gen-asking-for-me-exercise/<Topic>/`

`<course folder>` is the course the topic belongs to, such as `Java` or `Databases`. If the course is unclear, ask.

## 3. Write the exercises

- Write every exercise yourself. Do not copy exercises from tutorials, the course slides, the sample papers or the solutions. Do not copy another site's layout or wording.
- One blank per exercise. Mark it with `___` in the `code` string.
- The `code` string is one short Java or SQL line, or a few lines joined with `\n`. Keep it under 3 lines.
- The `options` list has one correct answer and plausible wrong choices. Make the wrong choices common mistakes.
- Vary the position of the correct answer across exercises.
- Keep the `prompt` to one sentence.

## 4. Build the page

1. Copy `template.html` from this skill folder to `<course folder>/Gen-asking-for-me/Gen-asking-for-me-exercise/<Topic>/<Topic> - Exercise.html`. Do not overwrite an existing file.
2. Replace the `PAGE` object (title, sub, source) with the topic's text. For exam-style questions that share tables (for example SQL questions on a set of relations), add `PAGE.schema`: a multi-line string that lists the relations, primary keys and foreign keys. The page shows it once, as a block above all the exercises.
3. Replace the `EXERCISES` array. Each item has:
   - `title`: short name of the exercise, bilingual `{en, zh}`
   - `prompt`: one sentence telling the reader what to fill in
   - `code`: the line with `___` for the blank
   - `options`: array of choices, including the correct one
   - `answer`: the correct choice, which must be exactly one of the `options`
   - `typePrompt`: the prompt shown in 打字 mode, with the expected format
   - `why`: one short reason, under 25 words
   - `explain`: a detailed explanation shown when the reader clicks 詳解. Write 120 to 250 words in short plain sentences. Explain why the answer is right, why each wrong choice is wrong, and the Java idea behind it. Use `\n` for a new paragraph.
4. Check every `answer` against its `options` list before you save. A wrong key is worse than no key.
5. Syntax-check the script: extract it with `awk` and run `node --check`.

The template has a dropdown at the top right, labelled 輸入方式, with three modes: 打字 (type the word), 拖曳 (drag a word into the blank), and 點擊 (click a word to fill). The default is 點擊. Do not change the switch when you fill in the exercises. A second dropdown next to it, labelled 語言, switches the page's own labels between 繁中 and English (buttons, feedback text, placeholders). The exercise text is bilingual: write each text field (`PAGE.title`, `PAGE.sub`, `PAGE.source`, and each exercise's `title`, `prompt`, `typePrompt`, `why`, `explain`) as an object with both languages, for example `{"en": "Start a condition", "zh": "開始一個條件"}`. The page shows the one matching the 語言 choice. `code` and `options` are code, so write them once. A plain string still works, but then the page shows it in both languages. Only change the `PAGE` and `EXERCISES` values.

Each exercise also needs a `typePrompt`. In 打字 mode there are no choices shown, so the reader must recall the answer. Write a `typePrompt` that says the expected format, for example "Type the class name. Capital letters count." The check is exact, so say so when capitalization matters. When `typePrompt` is missing, the page falls back to `prompt`. Switching modes clears all answers.

Each exercise panel has a 詳解 button. Clicking it opens the `explain` text below the answer, and clicking again closes it. The `explain` field is optional: when it is missing, the page shows `why`. Always write `explain` so that the reader can learn from it even after getting the answer right.

## 4b. SQL query-writing practice (step-by-step builder)

For questions that ask the reader to write a whole SQL statement on a set of relations, use `sql-builder-template.html` from this skill folder instead of `template.html`. One blank is hard to learn SQL from, so this builder walks through the clauses one at a time.

- Each question shows the tables it uses, with a few sample rows, right next to the steps.
- The SQL is built clause by clause: `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`. Each step has a question, 3 option chips and a text box; the next step opens only when the current one is right. A wrong answer shows the step's hint.
- When all steps are right, the page shows the full SQL and the query result table.

Copy the template to `<course folder>/Gen-asking-for-me/Gen-asking-for-me-exercise/<Topic>/<Topic> - Exercise.html`, then edit only `PAGE`, `TABLES` and `QUESTIONS`:

- `TABLES`: each table's `cols` and 3 to 4 sample `rows`. Write your own data; do not copy the paper's tables.
- `QUESTIONS`: `title`, `use` (table names to show), `steps` (each with `kw`, `q`, `options`, `answers`, `hint`, `why`), and `result` (the rows the full SQL returns on the sample data).
- Work out every `result` by hand from the sample rows, and check that `answers[0]` is one of the `options`. Answers are compared without spaces and case.

## 4a. Make the PDF copy

After the HTML is saved, print it to PDF in the same folder with headless Chromium, the same command as `asking-for-me-quiz`. The 詳解 panels and the buttons do not work in the PDF, which is expected. Check the page count with `qpdf --show-npages`.

## 5. Check the page

Open the file in a browser if you can. If you cannot, say so in the reply. The page works offline and has no build step.

## 6. Rules

- Do not overwrite an existing file. If the name is taken, add a suffix with the date.
- Do not commit unless the user asks.
- Do not reproduce long passages from the course material or other sites.

## 7. Reply

Reply in two or three lines in the user's language:

- The count and topic, for example "3 fill-in-the-blank exercises on inheritance."
- The page link, as `[file:///abs/path.html](file:///abs/path.html)`.
- Whether you have opened it in a browser.
