---
name: answer-pdf
description: Use when the user asks to make, build, set up or fix an answer PDF, submission PDF, or assignment/lab write-up with screenshots, such as "make the PDF like lab01", "做份 PDF 交", "same PDF style", or "set up the answer file". Builds one PDF from answer.md with pandoc + xelatex in the house style, with a title page with name and SID, contents, list of figures, one page per part, full question text as headings, captioned full-width screenshots. The style has one slate accent colour, code blocks in boxes with a file-name title bar, file trees with folder and file icons, zebra-striped tables with a bold header, framed screenshots. Also use it when the user asks to change or match this style (code box, table style, file tree, colours).
---

# Answer PDF

Every submission PDF built with this skill looks the same. Copy the templates, write `answer.md`, run `make`. Do not invent a new layout.

## 1. Set up the folder

Put the files next to the work being submitted (one folder per assignment):

```sh
T="<skill-dir>/templates"
cp "$T/header.tex" "$T/style.tex" "$T/codetitle.lua" "$T/Makefile" "$T/answer.md" .
cp "$T/gitignore" .gitignore
cp "$T/private.example.tex" private.tex   # then set the real name and SID
mkdir -p screenshots
```

- If an earlier assignment folder already has a filled-in `private.tex`, copy that one instead of the example.
- In `Makefile`, set `NAME` to the file name the assignment asks for. The output is `<SID>_<NAME>.pdf`, e.g. `NAME := exe03` gives `12345678_exe03.pdf`.
- Never change `header.tex`, `style.tex` or `codetitle.lua`. They are the style.

## 2. Write answer.md

Keep the template's YAML front matter exactly, except `title`. Then follow these rules.

| Element | Rule |
|---|---|
| Title | `"<Course code> <Assignment name>, <Part>"` |
| Author | Leave as `Name \\StudentName \\quad SID \\SID`. It reads `private.tex`. |
| First line after front matter | `\newpage` so the title, contents and list of figures sit on page 1. |
| Task heading | `# Task N (M marks)` |
| Part heading | `## a. [M marks] <question text copied word for word from the paper>`. Keep the paper's typos and bold. Never reword or shorten it. If the question continues with a list, put that list as normal text right under the heading. No quote blocks. |
| Sub-question | `### 1) <exact sub-question text from the paper>`, same rules. |
| One part, one answer | Never leave a part heading empty or merge two parts under one answer. Each part gets its own commands and text, even a one-line `mkdir`. When one screenshot covers several parts, put it under the last of them and name all of them in the caption, e.g. "The folder (a) and all project files (b)". |
| Page breaks | `\newpage` before each part that has a screenshot, and between screenshots that each need a full page. Short text-only parts can share a page. |
| Commands | ```` ```{.sh title="Terminal"} ```` with only the commands that were actually run. |
| Files | One titled block per file with its full content: ```` ```{.js title="<SID>_<name>/task2/server.js"} ````. Show a file this way instead of `touch`/`echo`/`cat >` commands. |
| Changes to a given file | When a question says "modify X", show a ```` ```{.diff title="<path>"} ```` block with a real `@@ -old,n +new,n @@` header taken from the actual file, next to the complete code if the question asks for it. Then say in prose which lines the change goes between and why there. Added lines render green, removed lines red. Add `.numbered` (```` ```{.diff .numbered title="..."} ````) to show old and new line numbers in two grey columns, counted from the `@@` header. |
| Folder layout | A ```` ```{.tree} ```` block: one entry per line, two spaces per level, folders end in `/`, optional note after ` # `, one root line. It renders as a file tree with folder/file icons and guide lines. |
| Screenshots | `![<caption>](jpg/<id>.jpg){width=100%}`. Source PNG goes in `screenshots/<id>.png`. Name ids after the part: `2ab`, `3c`, `2e_jan`. |
| Captions | Say what the screenshot proves, e.g. "updateMany matches 3 documents and modifies 1". Not "Screenshot of terminal". |
| Underscores in headings and captions | Escape them: `exe02\_task3`. |
| Tables | Pipe tables for values, requirement-to-code mappings, or test results. When a row is long, the dashes in the separator line set the column widths: give short columns few dashes and code columns many, e.g. `|----------|--|------------|`, or the table runs past the margin. |
| Paths | Code block titles and the tree root use the full path where the work really lives, e.g. `~/12345678_exe02/task2/server.js`, matching the prompt in the screenshots. Commands show exactly what was typed. Question text copied from the paper stays as it is. |
| Secrets | Never write a password into answer.md. Mention it was left out. |

`style.tex` sets the look, all in one accent colour (`#3B4252`). Headings are bold in that colour. Each code block sits in a light grey `tcolorbox` that can break across pages, with its `title` in a dark bar on top. Tables get accent rules, zebra rows and a bold header row. Captions are small with a bold "Figure N:" label, and screenshots get a thin frame so a white window does not blend into the page.

`codetitle.lua` does the work `style.tex` cannot: it wraps code blocks in the box, bolds table headers, and turns each `{.tree}` block into a `forest` folder tree with Font Awesome icons. Give every code block a title except `{.tree}`: a path for files, `Terminal` for commands.

Pass `style.tex` with `-H`, as the Makefile does. Pandoc's `-H` replaces `header-includes`, so the filter cannot add preamble code.

Write only what the question asks for. A "do the coding" or "run it" part gets the code, the commands and the screenshot, with no explanation, requirement table or line-by-line walkthrough. Add prose only when the question asks a written question (describe, explain, why, what is).

Answer prose is plain and short, written as the student. Run the `unslop-writing` skill on long written answers before building.

Screenshots for these submissions are usually required to be full-screen (taskbar, date and time visible). The user takes them. If they do not exist yet, create grey placeholders with the final file names so the PDF still builds, and tell the user which file to overwrite with what:

```sh
magick -size 2560x1440 xc:'#dddddd' -gravity center -pointsize 120 -annotate 0 "PLACEHOLDER 2ab.png" screenshots/2ab.png
```

## 3. Build and check

```sh
make
```

`make` converts each `screenshots/*.png` to `jpg/*.jpg` (xelatex takes minutes on full-size PNGs) and then runs pandoc. `jpg/` is ignored by git. The files worth keeping are `screenshots/`, `answer.md`, `Makefile`, `header.tex`, `style.tex`, `codetitle.lua` and the PDF. Keep `private.tex` out of any public repository.

Check the result before reporting done. Render the first pages and look at them:

```sh
pdftoppm -r 40 -png -f 1 -l 4 <SID>_<NAME>.pdf /tmp/pg && magick /tmp/pg-*.png +append /tmp/preview.png
```

Page 1 must show the title, the name and SID line, Contents, and List of Figures. Every figure must have a caption and a number. No heading should be stranded at the bottom of a page.
