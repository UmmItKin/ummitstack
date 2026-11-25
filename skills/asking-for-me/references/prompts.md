# Subagent prompts

Paste the block you need, fill the angle-bracket parts, and send it with `model: sonnet` at low effort. Every subagent returns exactly one JSON object and nothing else. Discard a malformed answer and ask once more; do not repair it yourself. Subagents write no files.

## Research (`standard`, `deep`)

```
You are a read-only researcher. Topic: <topic>. Source (read-only, may be empty): <path>.
Do not write files and do not copy long passages.
Return one JSON object:
{"source_facts": ["<fact, with file and page if there is a source>"],
 "concepts": [{"name": "", "prerequisites": [""]}],
 "common_mistakes": [{"concept": "", "mistake": ""}],
 "exam_style": ["<how questions on this topic are usually asked>"]}
Say "unknown" instead of guessing.
```

## Critic (`standard`, `deep`)

```
You are a coverage reviewer. You did not write these items. You see the unit list and the item list below.
Do not write items. Return one JSON object:
{"missing_concepts": [""], "misconceptions_without_item": [""], "duplicates": [["id","id"]], "difficulty_gaps": [""], "stop": true|false}
Units: <units JSON>
Items: <items JSON, with answers removed>
```

## Solve blind (all profiles)

```
Answer these questions as a careful student. You have no answer key, no hints and no source.
For each id give your answer: a number (0-based index) for single choice, an array of numbers for multi choice, the exact option text for a blank.
Also say "ambiguous" for any item where two answers could be defended.
Return one JSON object: {"answers": {"<id>": <answer>}, "ambiguous": ["<id>"]}
Items: <quiz and blank items with answer, hint, why and explain removed>
```

Save the `answers` object as `solver.json`: `{"answers": {...}}`.

## Refute (all profiles)

```
You did not write these items. Try to break each one. Look for: a wrong key, an ambiguous stem, a distractor that is also correct, an absurd distractor, a false or unsupported claim, a code line that does not compile or run.
Do not rewrite items and do not confirm items you could not break. Source (read-only, may be empty): <path>.
Return one JSON object: {"flags": [{"id": "", "problem": "", "evidence": ""}], "checked": ["<ids you checked>"]}
Items: <all items with answers>
```

## `quick`: one subagent, two messages

Spawn one subagent with the blind-solve prompt. When it answers, send the refute prompt to the same subagent with `SendMessage`. It counts as one subagent, because the blind solve is finished before it sees any key.
