#!/bin/bash
# Render the mockups: design/render.sh [screen ...]   (default: every screen × preset × theme). Backgrounds first: design/render.sh bg
# Needs a Chromium; set CHROME to override. Output: design/mockups/<screen>-<dir>[-paper].png (canon-free).
set -euo pipefail
cd "$(dirname "$0")"
CHROME=${CHROME:-$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome 2>/dev/null | tail -1)}
[[ -x $CHROME ]] || { echo "no Chromium found; set CHROME" >&2; exit 1; }
bg=0; [[ ${1:-} == bg ]] && { bg=1; shift; }
screens=("$@"); (( ${#screens[@]} || bg )) || screens=(empty desk terminal comms power agents)
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
# backgrounds: render.sh bg. Each is a page from src/wallpaper.py, baked at 3840x2160.
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
  for n in line thin band; do for t in mist paper; do
    python3 src/wallpaper.py "$n" "$t" > src/.wall.html
    bake "file://$PWD/src/.wall.html" "assets/bg-$n-$t.jpg"
  done; done
  rm -f src/.wall.html
  # the boot unlock image: the mark alone, with empty space below it to lift it above the centre (DESIGN 8.8)
  for t in mist paper; do
    [[ $t == mist ]] && fg='#F4F5EF' || fg='#121614'
    { echo "<!doctype html><meta charset=utf-8><style>html,body{margin:0;width:353px;height:340px;background:transparent}svg{display:block;width:345px;height:300px;margin-left:4px;color:$fg}</style>"; cat assets/ef-mark.svg; } > src/.unlock.html
    "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --default-background-color=00000000 --force-device-scale-factor=1 \
      --window-size=353,340 --virtual-time-budget=2000 --screenshot="assets/unlock-$t.png" "file://$PWD/src/.unlock.html" >/dev/null 2>&1
    echo "assets/unlock-$t.png"
  done
  rm -f src/.unlock.html
fi
