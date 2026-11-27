#!/usr/bin/env python3
"""Usage: redact_urls.py   (reads stdin, writes stdout)
Replaces every URL in the text with [link removed], so a reader never sees where a link points. Valid JSON stays valid JSON.
Covers addresses with a scheme (https://, hxxps://, ftp://), www., mailto:, tel:, javascript:, data:, a bare domain followed by a
path, query or fragment, and a domain written with [.] or (.). A bare domain with no path and an address spelled out in words are not covered."""
import json, re, sys

URL = re.compile(
    r"""(?ix)
    (?: [a-z][a-z0-9+.\-]*:// | hxxps?:// | www\. | mailto: | tel: | javascript: | data: ) [^\s<>"'`)\]]+
    | \b (?: [a-z0-9\-]+ \. )+ [a-z]{2,} [/?\#] [^\s<>"'`)\]]*
    | \b [\w\-]+ (?: \[\.\] | \(\.\) | \[dot\] ) [\w\-.\[\]()]+
    """
)
MARK = "[link removed]"


def clean(text):
    return URL.sub(MARK, text)


def walk(node):
    if isinstance(node, str):
        return clean(node)
    if isinstance(node, list):
        return [walk(x) for x in node]
    if isinstance(node, dict):
        return {k: walk(v) for k, v in node.items()}
    return node


def main():
    text = sys.stdin.read()
    try:
        data = json.loads(text)
    except ValueError:
        sys.stdout.write(clean(text))
        return
    sys.stdout.write(json.dumps(walk(data), ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
