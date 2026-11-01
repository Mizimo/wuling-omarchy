# Themes and generation

`tokens/wuling.json` is the product's palette, type, geometry, motion and
preset source. The design CSS is reference material, not runtime input.
`tools/generate` emits the four `theme/` directories and plugin style data.
Do not edit generated files. Build-only dependencies never enter the runtime.

Omarchy stages a theme into its current theme directory. It reads `shell.toml`
there; editing a source theme alone does not repaint the running shell.
`wuling config set menu.selected …` regenerates owned installed themes and
reapplies the active WULING theme with the official command, preserving the
current background through `omarchy theme refresh`. Other overrides
are resolved independently of the active theme. Never rewrite a user-edited
installed theme to make a test pass.

Check actual alpha-composited detail text, not just selected-text. Native menu
detail text remains the menu foreground at 52% alpha. Clipboard has its own
row drawing and does not use the selected border. No theme ships executable
app configuration or `hyprland.lua`.

Copy the approved boot mark and backgrounds from `design/assets/`; their
build command is `design/render.sh bg`. Previews come from
real VM captures. Update the image manifest deliberately after inspecting
captures, then run `tools/generate --check` and `tools/check`.
