#!/bin/sh
# Usage: sh open.sh KEY URL
# Opens URL in a visible window with the browser KEY (chromium, chrome, brave or testing) from detect.sh, with that browser's profile,
# then prints the page URL. Exit 2: KEY is not available here.
here=$(cd "$(dirname "$0")" && pwd)
key=${1:-}
url=${2:-}
[ -n "$key" ] && [ -n "$url" ] || { echo "Usage: sh open.sh KEY URL" >&2; exit 2; }
row=$(sh "$here/detect.sh" | awk -F '\t' -v k="$key" '$1 == k')
if [ -z "$row" ]; then
  echo "not available here: $key; available: $(sh "$here/detect.sh" | cut -f1 | tr '\n' ' ')" >&2
  exit 2
fi
exe=$(printf '%s' "$row" | cut -f3)
profile=$(printf '%s' "$row" | cut -f4)
agent-browser --headed ${exe:+--executable-path "$exe"} --profile "$profile" open "$url" && agent-browser get url
