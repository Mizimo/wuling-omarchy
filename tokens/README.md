# Token source

`wuling.json` is the product source. It contains the two palettes, mappings to
Omarchy colours, type, geometry, motion, sound and the field/hud presets. It
was transcribed from the approved design CSS and theme draft; generators do
not scrape CSS at runtime. Settings keys are deliberately limited to DESIGN.

`tools/generate` emits the four themes and `kit/generated/tokens.json`.
Generated files are committed so installation needs no build tools.
`tools/generate --check` regenerates text in a temporary directory and compares
bytes. Images are compared against `images.json`; after inspecting new real VM
captures, `tools/generate --refresh-images` records their hashes.

Backgrounds and the transparent boot mark are copied from the approved
`design/assets/` images; `design/render.sh bg` rebuilds their sources.
`tools/subset-icons` uses the design font
and FontTools to generate `fonts/MaterialSymbolsSharp.ttf` and `icons.json`.
These tools run only while developing. The fonts and generated assets are
already included for users.
