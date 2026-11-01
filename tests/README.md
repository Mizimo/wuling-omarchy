# Checking WULING

Run `tools/check` for display-free validation. Tests use temporary homes and
mock only the external Omarchy/fontconfig operations; file ownership,
transactions, config parsing and restoration run against real files. No host
desktop, service or package is modified.

VM acceptance uses a clean supported Omarchy checkpoint and the actual
`install`, `wuling` and official Omarchy commands. Keep before/after inventories
and raw results outside git. For phase B:

1. Install, run doctor, install again, remove twice using the checkout command.
   The configuration inventory must return exactly to its baseline.
2. Repeat with a pre-existing conflicting name, an edited installed theme,
   user overrides and the optional fastfetch mark. Keep user changes intact.
3. Apply all four themes. Use real keyboard input to inspect menus and panels;
   verify menu selection changes survive re-applying the theme and preserve
   the selected background during a settings update.
4. Capture backgrounds on real outputs at 16:9, 16:10, 3:2 and 21:9. Inspect
   cropping and text at each aspect ratio, not an image-resizing simulation.
5. In the disposable VM, use the official Plymouth theme setter, then
   plymouthd and ask-for-password to inspect the actual boot mark and prompt.
   Save real captures, quit Plymouth, and restore the original system theme.
6. Confirm wuling.toml survives the upstream git-theme staging filter.
7. Restore the original theme and only fixture-created configuration, shut
   down normally and retain the baseline plus newest clean checkpoint.

Run this on both 4.0.6 and 4.5.0-rc2. Physical hardware and the optional next
boot's Plymouth screen require the separate verifier/owner workflow in BRIEF.
