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

`/commit-regular on` (or no argument) and `/commit-regular off`. While on, the agent commits after each finished, working change without being asked, with a `conventional-commit` message. It runs the project's checks first, stages only the files it changed, and never pushes.

</details>

<details>
<summary><b>open-ag</b>: open a visible Chromium window with the saved profile</summary>

`/open-ag <url>` opens the URL in a visible window through `agent-browser`, using the profile at `~/.agent-browser-profile`, then prints the page URL. It uses Chromium or Chrome stable if installed, else agent-browser's own Chrome for Testing. In Codex: `$open-ag <url>`. Needs `agent-browser`.

</details>

<details>
<summary><b>presentation-deck</b>: build a PowerPoint from SVG slides with ppt-master</summary>

A build helper for ppt-master projects. `scripts/build.sh <project-dir>` runs the final quality gate, note split, SVG preview, PPTX and PDF export, then checks the counts. `references/build.md` has the manual commands, export flags, source layout and known traps.

</details>

<details>
<summary><b>review-pr</b>: read-only PR review, one HTML page with screenshots</summary>

`/review-pr <number|url>` reviews a pull request read-only with `gh`: reads the diff, clones and checks out the branch in a temp directory, runs the project's quick checks, and for UI changes reproduces the app and screenshots the result with `agent-browser`. It writes one self-contained Material-style HTML page to `~/.review-pr/` with the verdict, findings, screenshots and diff, then prints the `file://` URL. The only writes are the temp clone and the report. Requires `gh`; screenshots need `agent-browser`.

</details>

<details>
<summary><b>merge-pr-good-to-go</b>: merge a PR that passed review</summary>

`/merge-pr-good-to-go <number|url>` runs after a `good to go` review. It checks `gh` and the PR state, asks what comment to post, posts it, asks which merge method to use (squash by default), and merges. It stops on drafts, conflicts, failing checks or a PR that has not been reviewed.

</details>

## License

[MIT](LICENSE)
