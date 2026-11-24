---
name: presentation-deck
description: Build a PowerPoint deck with ppt-master, which converts one SVG per slide into native editable PPTX shapes, plus speaker notes and a PDF. Use when building, rebuilding or debugging a deck from SVG sources with ppt-master.
---

# Build a deck with ppt-master

ppt-master converts one SVG per slide into native, editable PowerPoint shapes, not images. This skill covers building and re-exporting a deck that is already authored; planning, templates and slide authoring belong to the installed ppt-master skill.

`scripts/build.sh <project-dir>` runs the pipeline in order and checks the counts: final quality gate, speaker notes, self-contained SVG preview, PPTX, PDF. It finds ppt-master's scripts at `~/.claude/skills/ppt-master/scripts`; set `PPT_MASTER_SCRIPTS` to override, and `PPT_MASTER_PYTHON` to pick the interpreter that has ppt-master's requirements installed.

Read `references/build.md` for the manual commands, export flags, the source layout and the known traps.
