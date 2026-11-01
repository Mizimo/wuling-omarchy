#!/bin/bash
# Render the mockups: design/render.sh [screen ...]   (default: every screen × preset × theme). Backgrounds first: design/render.sh bg
# Needs a Chromium; set CHROME to override. Output: design/mockups/<screen>-<dir>[-paper].png (canon-free).
set -euo pipefail
cd "$(dirname "$0")"
CHROME=${CHROME:-$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome 2>/dev/null | tail -1)}
[[ -x $CHROME ]] || { echo "no Chromium found; set CHROME" >&2; exit 1; }
bg=0; [[ ${1:-} == bg ]] && { bg=1; shift; }
screens=("$@"); (( ${#screens[@]} || bg )) || screens=(desk terminal comms power agents)
mkdir -p mockups
shot() { # screen dir theme
  local out="mockups/$1-$2$([[ $3 == paper ]] && echo -paper).png"
  "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --window-size=1366,768 --virtual-time-budget=4000 --screenshot="$out" \
    "file://$PWD/src/mock.html?screen=$1&dir=$2&theme=$3" >/dev/null 2>&1
  echo "$out"
}
for s in ${screens[@]+"${screens[@]}"}; do for d in field hud; do
  shot "$s" "$d" mist
  shot "$s" "$d" paper
done; done
# backgrounds: render.sh bg. The landscape comes from src/wallpaper.py, the survey overlay from src/wall.html; the hud preset adds its overlay on top.
bake() { # url out
  local tmp; tmp=$(mktemp --suffix=.png)
  "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files --force-device-scale-factor=3 \
    --window-size=1366,768 --virtual-time-budget=8000 --screenshot="$tmp" "$1" >/dev/null 2>&1
  python3 - "$tmp" "$2" <<'PY'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB').resize((3840, 2160), Image.LANCZOS)
if sys.argv[2].endswith('.jpg'): im.save(sys.argv[2], 'JPEG', quality=92, subsampling=0, optimize=True)
else: im.save(sys.argv[2])
PY
  rm -f "$tmp"; echo "$2"
}
if [[ $bg == 1 ]]; then
  mkdir -p .build
  echo "window.ANCHORS = $(python3 src/wallpaper.py --anchors);" > .build/anchors.js
  for t in mist paper; do
    python3 src/wallpaper.py --variant "$t" --layer land > "src/.land-$t.html"
    bake "file://$PWD/src/.land-$t.html" ".build/land-$t.png"
    rm -f "src/.land-$t.html"
    bake "file://$PWD/src/wall.html?theme=$t" "assets/bg-field-$t.jpg"
    bake "file://$PWD/src/mock.html?screen=bg&dir=hud&theme=$t" "assets/bg-hud-$t.jpg"
  done
fi
