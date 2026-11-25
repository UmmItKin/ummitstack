# Pipeline

## Profiles

Profiles change breadth and redundancy. They never lower the bar: every item is validated by the script and every quiz or exercise is solved blind.

| | `quick` (default) | `standard` | `deep` |
|---|---|---|---|
| Subagent budget | 2 | 8 | 30 |
| Planned subagents | 1 | 4 | up to the budget |
| Research | you do it | 1 research subagent (source, topic map, common mistakes) | up to 3 in parallel |
| Writing | you | you, in batches per kind | you, plus writer subagents per unit group |
| Review of coverage | none | 1 critic after writing | a critic after each wave, until clean (3 at most) |
| Solving and refuting | 1 subagent, two messages: blind solve, then refute | 1 solver and 1 checker, separate | 1 solver and 1 checker per kind, plus a record verifier at the end |
| Asks before starting | no | once | once |

Every subagent runs on `sonnet` at low reasoning effort, in every profile. Never use another model or a higher effort. If the harness has no effort setting, tell the subagent in its prompt to answer directly without extended reasoning.

`standard` and `deep` need an explicit `--profile`. Do not move up a profile on your own, even for a large topic. Say that a deeper profile exists and let the user choose.

## Phases

**Research** (`standard` and `deep`). Read-only subagents return facts only: what the source says, a concept map with prerequisites, common mistakes, and the likely exam style. You write the topic map into `run.json` units. In `quick` you do this from your own knowledge, and say so in the reply when there is no source.

**Write.** For each unit write the items:
- `quiz`: single-answer questions (see `asking-for-me-quiz` for the style).
- `blank`: fill-in-the-blank exercises (see `asking-for-me-exercise`).
- `claims`: for `study` and `video`, the list of factual claims the page will make, one sentence each. The page text is written later from the verified claims.

**Critic** (`standard`, `deep`). A fresh subagent sees the unit list and the item list. It returns missing concepts, misconceptions with no item, duplicate items and difficulty gaps. It proposes units, not items. You decide, and units you do not cover become `deferred` with a reason.

**Solve blind.** A fresh subagent receives only the questions and options: no key, no hint, no `why`, no source. It returns its answers. Disagreement with the key means the item is wrong or ambiguous.

**Refute.** A subagent that did not write the items receives them with the key and the source, and tries to break each one: wrong key, ambiguous stem, a distractor that is also correct, an obviously absurd distractor, a false claim. It returns flags, not rewrites.

**Fix.** You rewrite flagged items. A rewritten item goes through solving again. An item that fails twice is dropped, and its unit becomes `deferred` with reason `item_failed_check`.

**Validate and render.** `validate.py` must pass, then the `asking-for-me-*` skills build the pages from the verified items.

## run.json

```json
{
  "topic": "Inheritance",
  "course": "Java",
  "profile": "quick",
  "budget": 2,
  "agents_used": 1,
  "run_status": "complete",
  "incomplete_reason": null,
  "source": null,
  "units": [
    {"id": "inheritance::quiz", "concept": "Inheritance", "kind": "quiz", "state": "covered", "reason": null},
    {"id": "inheritance::blank", "concept": "Inheritance", "kind": "blank", "state": "covered", "reason": null},
    {"id": "inheritance::claims", "concept": "Inheritance", "kind": "claims", "state": "covered", "reason": null}
  ],
  "items": [
    {"id": "q01", "kind": "quiz", "concept": "Inheritance", "q": "Which keyword makes a class extend another?",
     "options": ["extends", "implements", "inherits", "super"], "answer": 0, "hint": "It is about a parent class.", "why": "A class uses extends for a parent class."},
    {"id": "b01", "kind": "blank", "concept": "Inheritance", "title": "Extend a class", "prompt": "Fill in the keyword.",
     "code": "class Dog ___ Animal { }", "options": ["extends", "implements", "inherits"], "answer": "extends",
     "typePrompt": "Type the keyword. Case counts.", "why": "A subclass uses extends."},
    {"id": "c01", "kind": "claims", "concept": "Inheritance", "claims": ["A Java class can extend only one class."]}
  ]
}
```

Unit states are `planned`, `covered` and `deferred`. A `covered` unit has at least one item with the same concept and kind. A `deferred` unit has a reason. `run_status` is `in_progress`, `complete` or `incomplete`. `complete` needs every unit `covered` or `deferred`. `incomplete` needs `incomplete_reason`. `agents_used` never exceeds `budget`.

## Across runs

`progress.json` holds a count of right and wrong answers per concept. At the start of a run, concepts with the most wrong answers get extra units, so repeated practice goes where the user is weak. A concept the user has never been tested on is not weak.
