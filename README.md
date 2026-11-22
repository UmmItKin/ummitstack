# ummitstack

The agent skills I use, packaged so anyone can install them. They work in Claude Code, Codex, and the other agents that `npx skills` supports.

## Skills

| Skill | Say | What it does |
|---|---|---|
| `soc-me` | `/soc-me linux`, `/soc-me windows` | Read-only security check of this machine: anything compromised, what is odd but yours, what is wasting CPU or memory. Writes one HTML report. |
| `council` | "council" | Gets review from Claude Opus, Sonnet and Haiku, fixes what they agree on, and loops until they are satisfied. |
| `conventional-commit` | "commit" | Writes every commit message as one short Conventional Commits line, such as `fix: exclude nobody from orphan list`. |
| `commit-regular` | `/commit-regular on`, `/commit-regular off` | While on, the agent commits after every finished change without being asked. It never pushes. |

## Install

```sh
npx skills add UmmItKin/ummitstack                    # pick skills from a list
npx skills add UmmItKin/ummitstack --skill soc-me     # one skill
```

## soc-me

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

## council

Say "council" after a change. The agent asks Claude Opus, Sonnet and Haiku to review it read-only, checks each finding against the code, fixes the ones it agrees with, and asks again until all three are satisfied. Each review gives a score out of 10, and the final reply (or PR description) has a score table per round.

In Claude Code the three seats are subagents. From Codex or another agent, it calls `claude -p --model <opus|sonnet|haiku>`. Either way you only need a Claude subscription.

Name your preferred members in `CLAUDE.md` or `AGENTS.md`, so you can update the skill without losing them.

## License

[MIT](LICENSE)
