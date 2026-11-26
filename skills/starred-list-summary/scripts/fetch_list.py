#!/usr/bin/env python3
"""Usage: fetch_list.py LIST [--json] [--limit N]
       fetch_list.py --lists USER
LIST is a GitHub star list URL (https://github.com/stars/USER/lists/SLUG) or USER/SLUG.
Prints the repositories in the list, most starred first, one line each. --json prints everything as JSON.
--lists prints the star lists of a user. Read-only; it uses `gh api graphql`, so gh must be installed and logged in.
Exit 1: an error with the reason on stderr."""
import json, re, subprocess, sys

LISTS = "query($login:String!,$cursor:String){ user(login:$login){ lists(first:100, after:$cursor){ pageInfo{hasNextPage endCursor} nodes{ id slug name description isPrivate items(first:1){ totalCount } } } } }"
ITEMS = ("query($id:ID!,$cursor:String){ node(id:$id){ ... on UserList { items(first:50, after:$cursor){ totalCount pageInfo{hasNextPage endCursor} "
         "nodes{ __typename ... on Repository { nameWithOwner description stargazerCount isArchived pushedAt url primaryLanguage{name} licenseInfo{spdxId} "
         "repositoryTopics(first:5){nodes{topic{name}}} } } } } } }")


def gh(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"] + [x for k, v in variables.items() if v is not None for x in ("-f", f"{k}={v}")]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("error: gh is not installed; install the GitHub CLI (https://cli.github.com) and run: gh auth login")
    if r.returncode:
        err = (r.stderr or r.stdout).strip()
        if "auth login" in err or "authentication" in err.lower():
            sys.exit("error: gh is not logged in; run: gh auth login")
        sys.exit("error: " + (err.splitlines() or ["gh api failed"])[0])
    data = json.loads(r.stdout)
    if data.get("errors"):
        sys.exit("error: " + data["errors"][0].get("message", "GraphQL error"))
    return data["data"]


def user_lists(user):
    out, cursor = [], None
    while True:
        page = (gh(LISTS, login=user, cursor=cursor)["user"] or sys.exit(f"error: no user {user}"))["lists"]
        out += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return out
        cursor = page["pageInfo"]["endCursor"]


def parse(arg):
    m = re.search(r"github\.com/stars/([^/]+)/lists/([^/?#]+)", arg) or re.match(r"^([^/\s]+)/([^/\s]+)$", arg)
    if not m:
        sys.exit("error: give a list URL like https://github.com/stars/USER/lists/SLUG, or USER/SLUG")
    return m.group(1), m.group(2)


def fetch(user, slug):
    lists = user_lists(user)
    found = next((l for l in lists if l["slug"] == slug), None)
    if not found:
        sys.exit(f"error: {user} has no list '{slug}'; lists: " + ", ".join(l["slug"] for l in lists) + ("" if lists else "(none visible; a private list needs you to be logged in as its owner)"))
    repos, skipped, cursor = [], 0, None
    while True:
        items = gh(ITEMS, id=found["id"], cursor=cursor)["node"]["items"]
        for n in items["nodes"]:
            if n.get("__typename") == "Repository":
                repos.append(n)
            else:
                skipped += 1
        if not items["pageInfo"]["hasNextPage"]:
            break
        cursor = items["pageInfo"]["endCursor"]
    repos.sort(key=lambda r: -r["stargazerCount"])
    return found, repos, skipped


def line(r):
    topics = ",".join(t["topic"]["name"] for t in r["repositoryTopics"]["nodes"])
    lang = (r["primaryLanguage"] or {}).get("name", "-")
    desc = " ".join((r["description"] or "").split())[:140]
    flag = " ARCHIVED" if r["isArchived"] else ""
    return f"{r['nameWithOwner']} | {r['stargazerCount']} stars | {lang} | pushed {r['pushedAt'][:10]}{flag} | {topics or '-'} | {desc or '-'}"


def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    limit = None
    if "--limit" in a:
        limit = int(a[a.index("--limit") + 1])
        del a[a.index("--limit"):a.index("--limit") + 2]
    a = [x for x in a if x != "--json"]
    if a[:1] == ["--lists"] and len(a) == 2:
        for l in user_lists(a[1]):
            print(f"{l['slug']} | {l['name']} | {l['items']['totalCount']} items" + (" | private" if l["isPrivate"] else ""))
        return
    if len(a) != 1:
        sys.exit(__doc__)
    user, slug = parse(a[0])
    found, repos, skipped = fetch(user, slug)
    shown = repos[:limit] if limit else repos
    if as_json:
        print(json.dumps({"user": user, "slug": slug, "name": found["name"], "description": found["description"], "repositories": shown, "not_repositories": skipped}, indent=1))
        return
    print(f"{found['name']} ({user}/{slug}): {len(repos)} repositories" + (f", {skipped} items that are not repositories" if skipped else "") + (f"; showing the top {len(shown)}" if limit and limit < len(repos) else ""))
    if found["description"]:
        print(found["description"])
    for r in shown:
        print(line(r))


if __name__ == "__main__":
    main()
