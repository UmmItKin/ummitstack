# ummitstack

The agent skills I use, packaged so anyone can install them. They work in Claude Code, Codex, and the other agents that `npx skills` supports.

## Install

```sh
npx skills add UmmItKin/ummitstack                    # pick skills from a list
npx skills add UmmItKin/ummitstack --skill soc-me     # one skill
```

## Skills

<details>
<summary><b>soc-me</b>: read-only security check of this machine, with an HTML report</summary>

| Agent | Linux | Windows |
|---|---|---|
| Claude Code | `/soc-me linux` | `/soc-me windows` |
| Codex | `$soc-me linux` | `$soc-me windows` |

Without `linux` or `windows`, the agent detects the system it runs on. From WSL, `/soc-me windows` checks the Windows host. Add `recheck` (for example `/soc-me linux recheck`) to see what changed since the last report in the same session.

It never changes the system, runs only when you call it, and the agent never starts it on its own.

On both systems it checks processes running from temp or user-writable folders, processes that pretend to be system processes, listening ports and outbound connections, persistence, extra admin accounts, recently added executables, long-running orphaned processes, and heavy CPU or memory use.

**Linux** also checks `/etc/ld.so.preload` and `LD_PRELOAD`, systemd units, timers, cron, autostart and shell startup files, SSH `authorized_keys`, files no package owns, SUID/SGID files, kernel taint and zombies.

**Windows** also checks encoded or download-and-run PowerShell, Office or script hosts starting a shell, running programs without a valid signature, Run keys, the Startup folder, Winlogon and IFEO hijacks, scheduled tasks, services in user-writable folders, WMI event subscriptions, Defender status and exclusions, and firewall, SMB1, LLMNR and RDP settings.

The full lists, with what counts as a red flag, are in [`references/linux.md`](skills/soc-me/references/linux.md) and [`references/windows.md`](skills/soc-me/references/windows.md). Suspicious findings get the matching MITRE ATT&CK technique ID, such as T1574.006 for `LD_PRELOAD` hijacking.

</details>

<details>
<summary><b>council</b>: code review by Claude Opus, Sonnet and Haiku</summary>

Say "council" after a change. The agent asks Claude Opus, Sonnet and Haiku to review it read-only, checks each finding against the code, fixes the ones it agrees with, and asks again until all three are satisfied. Each review gives a score out of 10, and the final reply (or PR description) has a score table per round.

In Claude Code the three seats are subagents. From Codex or another agent, it calls `claude -p --model <opus|sonnet|haiku>`. Either way you only need a Claude subscription.

Name your preferred members in `CLAUDE.md` or `AGENTS.md`, so you can update the skill without losing them.

</details>

<details>
<summary><b>conventional-commit</b>: one-line Conventional Commits messages</summary>

Used whenever the agent commits, for example when you say "commit". Each message is one short line, such as `fix: exclude nobody from orphan list`, following [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). No body and no `Co-Authored-By` trailer.

In Claude Code, the first commit of a session sets `"attribution": {"commit": "", "pr": ""}` in `~/.claude/settings.json`, so Claude Code stops adding a co-author line. Your other settings are kept.

</details>

<details>
<summary><b>commit-regular</b>: commit after every finished change, on or off</summary>

`/commit-regular on` (or no argument) and `/commit-regular off`. While on, the agent commits after each finished, working change without being asked, with a `conventional-commit` message. It runs the project's checks first, runs `check-commit-info` on what it staged, stages only the files it changed, and never pushes.

</details>

<details>
<summary><b>check-commit-info</b>: check a commit for personal information before it is made</summary>

`/check-commit-info ["commit message"]` runs `scripts/check.sh` on the staged files and the message. It requires git's own `user.name` and `user.email` to be set and uses them as they are (never `--author`); if one is missing it asks you for it. It then looks for key and `.env` files, email addresses, home paths, common token formats and your own name or login, and prints only the kind and `file:line`, never the secret. Placeholders such as `/home/user` and `you@example.com` pass. `commit-regular` runs it before every commit.

</details>

<details>
<summary><b>open-ag</b>: open a visible Chromium, Chrome or Brave window with a saved profile</summary>

`/open-ag <url> [--browser chromium|chrome|brave|testing]` opens the URL in a visible window through `agent-browser`, then prints the page URL. It looks for Chromium, Chrome, Brave and agent-browser's own Chrome for Testing. With one installed it uses it; with two or more it asks you to pick from a menu, and remembers the choice for the session. Chromium, Chrome and Chrome for Testing share the profile at `~/.agent-browser-profile`; Brave has its own at `~/.agent-browser-profile-brave`. In Codex: `$open-ag <url>`. Needs `agent-browser`.

</details>

<details>
<summary><b>presentation-deck</b>: build a PowerPoint from SVG slides with ppt-master</summary>

A build helper for ppt-master projects. `scripts/build.sh <project-dir>` runs the final quality gate, note split, SVG preview, PPTX and PDF export, then checks the counts. `references/build.md` has the manual commands, export flags, source layout and known traps.

</details>

<details>
<summary><b>unslop-powerpoint-style</b>: make a ppt-master deck look designed, not generated</summary>

Makes ppt-master slides look designed. The style pass picks a structure for each slide (equal zones with a numbered kicker, a tinted system boundary, a sequence diagram with dashed dividers, chevron steps, a code panel with one highlighted line) and draws it by hand with jittered frames, curved lines and open chevron arrowheads. The template step copies the closest file from `templates/` and replaces its content, and `scripts/sequence.py` draws a sequence diagram from a JSON spec. Arrows are always drawn and never typed as characters, slide text has no em dashes, and the deck's own fonts are checked and installed first. Both steps end by rendering every touched slide and looking at it.

</details>

<details>
<summary><b>review-pr</b>: read-only PR review, one HTML page with screenshots</summary>

`/review-pr <number|url>` reviews a pull request read-only with `gh`: reads the diff, clones and checks out the branch in a temp directory, runs the project's quick checks, and for UI changes reproduces the app and screenshots the result with `agent-browser`. It writes one self-contained HTML page styled like ummit.dev to `~/.review-pr/` with the verdict, findings, screenshots and diff, then prints the `file://` URL. The only writes are the temp clone and the report. Requires `gh`; screenshots need `agent-browser`.

</details>

<details>
<summary><b>merge-pr-good-to-go</b>: merge a PR that passed review</summary>

`/merge-pr-good-to-go <number|url>` runs after a `good to go` review. It checks `gh` and the PR state; if the branch is behind or conflicted, it rebases onto the base branch (or merges), resolves conflicts by hand, rebuilds and checks, and pushes with `--force-with-lease` before asking. Then it asks what comment to post, posts it, asks which merge method to use (squash by default), and merges. It stops on drafts, a branch you cannot push to, failing checks, or a PR that has not been reviewed.

</details>

<details>
<summary><b>learn-working-principle</b>: study a repo's code, flow and history</summary>

`/learn-working-principle <repo-path-or-GitHub-repo>` is a read-only study of how a repository works. It always uses git (log, blame, tags, worktrees) and, for GitHub repos, `gh` for metadata and releases, then asks which branch, tag or commit to learn. It reads the entry points, traces one end-to-end flow with `file:line` citations, reads the tests as the spec, and explains architecture, build and release workflow, and history highlights in chat. `--rev <revision>` skips the version question and `--out <file>` also writes the explanation to a file, so other skills can read it.

</details>

<details>
<summary><b>unslop-writing</b>: rewrite AI-sounding prose so it reads like a person wrote it</summary>

`/unslop-writing <file-or-pasted-text>` scans prose for known AI-writing tells with `scripts/scan.py` (strong and weak hits with line numbers; code, front matter and URLs are skipped), then rewrites the sentences without adding or losing facts and scans again. It never touches code, commands, paths or YAML, and it follows house rules of no em dashes, no arrow characters and no emoji. `references/patterns.md` lists each tell with its fix.

</details>

<details>
<summary><b>make-deck-from-repo</b>: turn a repo into a finished deck, automatically</summary>

`/make-deck-from-repo <repo-path-or-GitHub-repo>` turns a repository into a deck in one run. It first asks everything in one message (audience, key message, slide count, language, version, style source), each with a recommended answer, or you can say "you decide". After that it works to the end without stopping. It learns the repo with `/learn-working-principle`, takes the style from a website (the CSS plus `agent-browser` screenshots), an existing deck or a ppt-master preset template, plans and draws the slides with ppt-master, styles them with `/unslop-powerpoint-style`, and builds the PPTX and PDF with `/presentation-deck`. It asks mid-run only when a decision has no sensible default, never commits, and resumes from the files already in `deck-<name>/` or from `--from N`.

</details>

<details>
<summary><b>menti-quiz</b>: join and answer a live Mentimeter quiz</summary>

`/menti-quiz` joins a live Mentimeter quiz in `agent-browser` with the join code, answers each question, screenshots the result, saves one note per question, and commits one per question. Needs `agent-browser`.

</details>

<details>
<summary><b>answer-pdf</b>: build a submission PDF from answer.md</summary>

Builds one PDF with pandoc and xelatex: title page with name and SID, contents, list of figures, boxed code with file-name bars, file trees, zebra tables and framed screenshots. The templates are in `templates/`; `private.example.tex` holds the name and SID fields, so keep your real `private.tex` out of any public repository.

</details>

<details>
<summary><b>asking-for-me</b>: checked study material on a topic</summary>

`/asking-for-me <topic> [--kinds ...] [--profile quick|standard|deep] [--source <path>]` writes study notes, quizzes and exercises, then checks them before anything is rendered. A fresh subagent solves the questions blind, another tries to refute the answers, and `scripts/validate.py` checks the format and compares the blind answers with the key. State lives in one `run.json`, with units that end `covered` or `deferred`, and `scripts/progress.py` records which concepts you get wrong so the next run targets them. It is lean by default: `quick` uses one subagent and starts without asking, and `standard` and `deep` are opt-in with a subagent budget. The four `asking-for-me-*` skills below render the verified items and still work alone.

</details>

<details>
<summary><b>asking-for-me</b>: render the pages, four skills</summary>

`asking-for-me-exercise` makes a fill-in-the-blank page (plus a step-by-step SQL builder), `asking-for-me-quiz` a one-question-at-a-time quiz player, `asking-for-me-study` an explainer page with a ten-year-old version, and `asking-for-me-video` a narrated HTML video lesson (Gemini text to speech, needs `GEMINI_API_KEY`). Each saves under `<course folder>/Gen-asking-for-me/...`. They build on the `answer-me-with-html` skill.

</details>

<details>
<summary><b>docx-reverse-pandoc</b>: edit a DOCX as Markdown and rebuild it with Pandoc</summary>

`/docx-reverse-pandoc <file.docx> [out-dir]` reverses a DOCX into `doc.md`, a `reference.docx` and a `build.sh`, so you can edit plain text and rebuild a matching `.docx`. It puts back what Pandoc drops: page breaks, tabs, the table of contents, the page background colour, empty paragraphs, colours, sizes, fonts, alignment and spacing (as named styles), and for tables the exact widths, empty rows, shading, row heights and cell alignment. `scripts/inventory.py` summarises a DOCX without extracting it, lists the fonts it needs and which are missing on this machine, and compares a rebuild with the original. `scripts/render.sh` renders both with LibreOffice into one side-by-side image, because a passing compare once hid tables that drew wrongly. Caption numbers become plain text. It runs in nine phases with gates for fonts, structure, per-paragraph formatting and the rendered look, a property coverage ledger, and a run state validator; `sh skills/docx-reverse-pandoc/tests/run.sh` reproduces past mistakes. Needs `pandoc`; the render check needs LibreOffice.

</details>

<details>
<summary><b>pdf-reverse-pandoc</b>: edit the text of a PDF and rebuild it with Typst</summary>

`/pdf-reverse-pandoc <file.pdf> [out-dir]` reverses a text PDF into `doc.typ`, which puts every run of text back at its place with the same font, size and letter spacing and redraws the table lines, then rebuilds a matching PDF. It is a positional rebuild, not a reflow. `scripts/setup.sh` lists the tools you need (poppler, typst, ImageMagick) and prints the install command for your system without running it. It runs in nine phases with gates for fonts, structure, per-run fidelity (text, font, size, baseline, width, lines, page count) and the rendered look, and `sh skills/pdf-reverse-pandoc/tests/run.sh` reproduces past mistakes. Scanned PDFs, curves and pictures are not supported.

</details>

<details>
<summary><b>verify-skill</b>: check a skill in one shot, including a cold-start run</summary>

`/verify-skill <skill-dir> [sample-input]` runs static checks (frontmatter, scripts, forbidden glyphs, personal paths), the skill's own tests, then a cold-start run by a fresh Sonnet low-effort subagent that follows only the `SKILL.md`, and fixes the bugs and gaps it reports, up to 3 rounds. It asks nothing unless there is no sample input. It never commits or pushes.

</details>

<details>
<summary><b>auto-find-best-skill</b>: make Claude Code pick the best installed skill in every session</summary>

`/auto-find-best-skill on|off|status` adds or removes one SessionStart hook in `~/.claude/settings.json`. The hook prints a short reminder at the start of every session, so Claude checks the installed skills for the best match before each task and searches with `find-skills` only when none fits. It never installs a skill without asking. It keeps your other settings and hooks, keeps a one-time copy of the original file, and refuses to touch a settings file that is not valid JSON. Claude Code only.

</details>

<details>
<summary><b>update-repo-directory-path</b>: keep Claude Code memory after renaming a repo folder</summary>

After you rename or move a repo folder by hand and start a new session there, the agent has no memory, because Claude Code stores memory per project path. Run `/update-repo-directory-path <old-path-or-name>` inside the moved repo to copy the old memory into it. With no argument it lists projects whose recorded folder no longer exists, so you can pick the old one. It shows a preview first and only copies on a second step. It never deletes or overwrites: a file that differs is reported as a conflict, `MEMORY.md` only gains its missing lines, and the old folder is left as it was. `--with-sessions` also copies the old conversations. Claude Code only.

</details>

<details>
<summary><b>starred-list-summary</b>: summarize a GitHub star list</summary>

`/starred-list-summary <list-url or USER/SLUG>` fetches the repositories in one of your GitHub star lists (for example `https://github.com/stars/USER/lists/agent-skill`) and summarizes them by theme, with the most starred, archived and stale ones flagged. GitHub has no REST endpoint for star lists, so it uses the GraphQL API through the `gh` CLI. It is read-only and needs `gh` logged in. With only a user name it shows the lists to pick from.

</details>

<details>
<summary><b>list-claude-projects</b>: list your Claude Code projects and session titles</summary>

`/list-claude-projects [filter]` lists every project under `~/.claude/projects` with its folder path and the title of each session, in two groups: titles you set with `/rename`, and the titles Claude made from what the session was doing. Sessions with neither are only counted, and folders that no longer exist are marked. It reads only the title fields and the working directory, never the conversation text. Claude Code only.

</details>

<details>
<summary><b>use-proton-cli</b>: work with a Proton account through the proton command, safely</summary>

Teaches the agent how to behave with your Proton account (Mail, Drive, Calendar, Pass, Meet, Contacts) when you use the unofficial [`proton-cli`](https://github.com/roman-16/proton-cli). The mailbox is strictly read only: all mail access goes through `scripts/mail-read.sh`, which allows only `list`, `get` and `count` and refuses everything else, so nothing can send, move, delete or mark mail. For Drive, Calendar and Pass it previews with `--dry-run` and asks before anything that changes data, never does irreversible or security actions on its own, never prints secrets beyond what you asked for, and treats mail content as data, not instructions. It does not copy the tool's reference: it tells the agent to use `proton <command> --help` and `proton skill --body-only`, which match the installed version. `scripts/preflight.sh` checks the install and sign-in without printing account data. Needs `proton`; signing in is done by you with `proton account login`.

</details>

## License

[MIT](LICENSE)
