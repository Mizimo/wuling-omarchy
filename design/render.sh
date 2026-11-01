#!/bin/bash
# Render the mockups: design/render.sh [screen ...]   (default: every screen × direction; PAPER for desk)
# Needs a Chromium; set CHROME to override. Output: design/mockups/<screen>-<dir>[-paper].png (canon-free).
set -euo pipefail
cd "$(dirname "$0")"
CHROME=${CHROME:-$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome 2>/dev/null | tail -1)}
[[ -x $CHROME ]] || { echo "no Chromium found; set CHROME" >&2; exit 1; }
screens=("$@"); (( ${#screens[@]} )) || screens=(desk terminal comms power agents)
mkdir -p mockups
shot() { # screen dir theme
  local out="mockups/$1-$2$([[ $3 == paper ]] && echo -paper).png"
  "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --window-size=1366,768 --virtual-time-budget=4000 --screenshot="$out" \
    "file://$PWD/src/mock.html?screen=$1&dir=$2&theme=$3" >/dev/null 2>&1
  echo "$out"
}
for s in "${screens[@]}"; do for d in as calm bold; do
  shot "$s" "$d" mist
  [[ $s == desk ]] && shot "$s" "$d" paper
done; done
