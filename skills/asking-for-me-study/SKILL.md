---
name: asking-for-me-study
description: Use when the user asks what a concept is, in any course (for example Java or databases), such as "什麼是 OOP", "what is class", "what is inheritance", or "explain polymorphism". Produces two outputs in one turn, an answer-me-with-html page for adult readers, and a kid-friendly ELI5 (age 10) markdown file. Saves both under "<course folder>/Gen-asking-for-me/Gen-asking-for-me-study/<Topic>/".
---

# Asking for me: study

The user asks a short question. You produce two explanations without making the user write a long prompt.

## When called by asking-for-me

If `asking-for-me` gives you a validated `run.json`, write the pages from its verified `claims` items and add no claims of your own.

## Naming

Every page has a Topic: Title Case words with spaces, such as `Creating a Class`. Name the file `<Topic> - <Kind>.<ext>`, where Kind is `Exercise`, `Quiz` or `Study`. Use the same base name for the PDF. The kid markdown is `<Topic> - ELI5.md`. Add ` v2` when the same topic is made again. Do not use lowercase hyphenated names, and do not put dates in the file name.

`<course folder>` is the course the topic belongs to, such as `Java` or `Databases`. If the course is unclear, ask.

## 1. Pick the topic folder

There is no language folder. Put each topic's files in `<course folder>/Gen-asking-for-me/Gen-asking-for-me-study/<Topic>/`. Write the adult page and the kid page in the language of the question.

## 2. Adult page (answer-me-with-html)

Follow the `answer-me-with-html` skill. For a non-OOP topic, such as SQL or database keys, use these panels instead: **What it is**, **Example** (a small table or SQL statement you write yourself), **Rules** (a table of can / cannot), **Common mistakes**, and **Summary table**. For an OOP topic, write one draft with these panels, in order:

1. **What it is**: one or two sentences with the core answer.
2. **Class vs object**: a table or a `flow` diagram.
3. **Attributes and methods**: a short example in Java that you write yourself.
4. **Four core ideas**: inheritance, polymorphism, encapsulation, abstraction. One short panel each, or one table.
5. **Summary table**: term, plain meaning, short example.

Render with `--no-open`. Then copy the rendered file into the topic folder, named `<Topic> - Study.html`. The `✓` line gives the source path, usually under `~/.answer-me-with-html/pages/`.

Then make a PDF copy in the same folder. The page is a single self-contained HTML file, so headless Chromium can print it:

```bash
cd "<topic folder>" && chromium --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf="$PWD/<Topic> - Study.pdf" "file://$PWD/<Topic> - Study.html"
```

Check the PDF with `qpdf --show-npages`. Interactive parts (ask buttons, reply box) are not kept in the PDF; that is expected.

## 3. Kid page (ELI5, age 10)

Write for a ten-year-old. Write a markdown file, `<Topic> - ELI5.md`, in the same topic folder, in the language of the question:

- Short sentences and a playful tone.
- Original analogies only: cookie cutters, pets, toy robots, TV remotes. Do not use characters or examples from the course slides.
- End with a "So what?" line.

## 4. Rules

- Do not overwrite an existing file. If the name is taken, add a suffix with the date.
- Do not commit unless the user asks.
- Do not copy text from the course slides or the sample papers. Explain the idea in your own words.

## 5. Reply

Reply in two or three lines in the user's language:

- One line with the core answer.
- The page link, as `[file:///abs/path.html](file:///abs/path.html)`.
- The kid markdown path.
