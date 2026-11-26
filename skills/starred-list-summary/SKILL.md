---
name: starred-list-summary
description: Fetch the repositories in a GitHub star list with the gh CLI and summarize them by theme, with the most starred, archived or stale ones flagged. Use when the user types /starred-list-summary or gives a github.com/stars/USER/lists/NAME link and wants to know what is in it.
---

# Starred list summary

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/starred-list-summary <list-url or USER/SLUG>`, for example `https://github.com/stars/USER/lists/agent-skill` or `USER/agent-skill`. With only a user name, or nothing, show the user's lists first.

GitHub has no REST endpoint for star lists, so the script uses the GraphQL API through `gh`. It is read-only.

## Steps
1. Check `command -v gh`. If it is missing, say how to install it (https://cli.github.com) and stop. If the script says gh is not logged in, tell the user to run `gh auth login` and stop.
2. If the argument is a user name or empty, run `python3 <skill-dir>/scripts/fetch_list.py --lists <user>` (use the current `gh` user if none is given), show the lists with their sizes, and ask which one to summarize.
3. Fetch: `python3 <skill-dir>/scripts/fetch_list.py <list>`. Each line is `owner/name | stars | language | last push | topics | description`, most starred first. Add `--limit N` for a very long list, and say that you cut it.
4. Summarize in the user's language, in this order:
   - One line: the list name, how many repositories, and how many are archived or have had no push for more than 12 months.
   - The 3 to 6 themes the repositories fall into (for example installers and registries, security skills, document tools), each with its repositories as `name (stars): what it does in a few words`.
   - The five most starred, and anything archived or stale, named.
   - One or two things worth a look, based on the descriptions only.
5. Offer to read the README of any repository for more detail. Do not fetch READMEs unless asked.

## Rules
- Never star, unstar, or change a list, and never print or store a token. The script only reads.
- Base the summary on the fetched fields. Do not claim what a repository does beyond its description and topics; say when a description is empty.
- A private list is visible only when `gh` is logged in as its owner. If a list is not found, show the lists that are visible.
