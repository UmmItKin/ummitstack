# Cold-start prompt

Give the subagent exactly this, with the three values filled in. Start it with `model: sonnet` and low effort. Do not add hints.

```
You have no prior context. A user typed: /<skill-name> <sample-input> <out-dir>
Do exactly what the skill file says, using only that file and the files it points to: <skill-dir>/SKILL.md
(the skill dir is <skill-dir>). Do not edit any file in <skill-parent-dir>. Do not hand-write any file that a
script is supposed to produce; if the instructions seem to require that, say so. Run every step in order,
including any bookkeeping and closing the run. You cannot ask the user anything: where the skill says to ask,
take the safest option (accept no loss, choose nothing irreversible) and say so.
Reply briefly with: (1) each command you ran, (2) every point where the instructions were unclear, missing or
wrong and what you had to guess, (3) the final result and how the run ended.
```

## Reading the report

| The subagent says | It is |
|---|---|
| It hand-wrote a file, or a command failed on the first try for a reason the docs do not mention | a gap: a producer or a doc line is missing |
| A wrong result was accepted, a run closed with a failing check, or a step could be skipped | a bug: add the gate, then a test that fails without it |
| Two documents say different things, or a name or flag is guessed | a gap: fix the wording in one place and point the other to it |
| It cannot ask the user, or a tool is not available to it | a limitation: note it, do not change the skill |
| It succeeded and lists nothing | no finding; do not invent one |

When a bug is fixed, add the check that would have caught it to the skill's tests, so the next round cannot regress it.
