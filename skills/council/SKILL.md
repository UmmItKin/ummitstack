---
name: council
description: Get review or feedback from three Claude models (Opus, Sonnet, Haiku), then fix what they agree on and review again until they are satisfied. Use when the user says "council".
---

# Council

## Seats
Three seats: Claude Opus, Claude Sonnet and Claude Haiku. Each model sees the code differently at a different depth, so a finding that two or three of them report is worth more than one only Opus reports. If the user or their `CLAUDE.md` / `AGENTS.md` names other members, use those.

| Seat | From Claude Code | From Codex or another agent |
|---|---|---|
| Opus | Agent tool, `model: opus`, `effort: high` | `claude -p --model opus --allowedTools "Read,Grep,Glob" "<prompt>"` |
| Sonnet | Agent tool, `model: sonnet`, `effort: high` | `claude -p --model sonnet --allowedTools "Read,Grep,Glob" "<prompt>"` |
| Haiku | Agent tool, `model: haiku`, `effort: high` | `claude -p --model haiku --allowedTools "Read,Grep,Glob" "<prompt>"` |

Use a general-purpose subagent so the delegate can read files. Start all three in parallel (several Agent calls in one message, or Bash `run_in_background`), not one after another. If a seat cannot be reached, tell the user which one and why; do not fill it with a second copy of another seat.

## What each delegate gets
- The user's request and the context it needs: the diff (`git diff <base>...HEAD`) or the files, the goal, and any constraints.
- For review or feedback, **read-only** access. Say so in the prompt, and use the read-only flags above.
- For a code review: ask for findings ranked by severity, each with file and line, and **a score out of 10**.

## While they run
Do not wait idle. When a result arrives, check each finding against the code at once and decide whether to fix it. Do not edit files while another delegate is still reviewing the same checkout. If the user marks a delegate as non-blocking, do not wait for it: treat a late result as feedback and do not record its score.

## Rounds
- One full review pass is one round. A fresh review after fixes starts a new round.
- Fix the findings you agree with, then ask for a fresh review. Repeat until all three are satisfied.
- Fight scope creep. A round's fixes address what was found, not new ideas the reviewers raised along the way. Name those as follow-ups instead.

## Report
Summarize the useful findings, which seats agreed on each, the disagreements between delegates, and what you did about each. Then the score table:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus | 7/10 | 9/10 |
| Claude Sonnet | 8/10 | 10/10 |
| Claude Haiku | 7/10 | 9/10 |
```

If a delegate gives no score, write `no score`. Never invent one.
If the work ends in a pull request, put this section in the PR description, before the model and harness line at the end.
