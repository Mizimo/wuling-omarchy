---
name: wuling
description: Inspect and customise an installed WULING desktop on Omarchy using its supported settings, theme resolver and diagnostics. Use for WULING appearance or configuration changes, not unrelated system administration.
---

# WULING customisation

Read `wuling commands --json` for the installed command contract. Inspect
`wuling theme resolve`, `wuling config get` and `wuling doctor` before changing
settings. JSON includes a schema version and the origin of resolved values.

Use `wuling config set <key> <value>` for requested customisation. Supported
keys are listed by `config get`; reject unrelated or unknown settings rather
than inventing keys. Configuration lives in `~/.config/wuling/overrides.toml`
(or the user's XDG configuration directory). Back up that file before a
multi-setting change. Updates preserve it.

Themes switch with Omarchy's own theme switcher or `omarchy theme set`:
`wuling`, `wuling-paper`, `wuling-hud`, `wuling-hud-paper`. `menu.selected`
regenerates owned installed WULING themes and reapplies the active one while
preserving the current background.
Other Omarchy themes remain usable. Do not edit generated installed themes,
the WULING release, `/usr/share/omarchy`, authentication code or default keys.

After a change, inspect the resolver and the actual affected surface. Settings
for components not installed yet may resolve without changing a surface;
`wuling status --json` and `doctor` distinguish availability from configuration.
To undo a setting, restore its previous value or the backed-up overrides and
reapply the theme. Preserve unrelated concurrent edits.

The desktop components are independent Omarchy plugins:
`wuling.bar`, `wuling.terminal`, `wuling.notifications`, `wuling.osd`,
`wuling.dispatch`, `wuling.power`, `wuling.session`. Inspect native `omarchy plugin`
and `omarchy bar` help before changing their enablement or placement. Bar
replacement needs the official `omarchy restart shell`; never restart a live
lock client or bypass Omarchy's refusal. Super+Ctrl+G belongs to Terminal and
Super+D to Dispatch;
all original keys still belong to Omarchy. `wuling terminal open` opens the
panel on the focused output. `status --watch` belongs only to a visible view,
and must stop when the view closes. Do not start an agent usage collector or
read account credentials to populate the panel.
Notifications and OSD replace their native providers through the official
clone contract; disabling one restores its previously enabled native provider.
Never bypass the notification module compatibility check. Notification state
contains private messages: do not publish it or include it in diagnostics.
Uninstall deletes that state; ordinary plugin disablement preserves it.
Dispatch history also contains private commands and questions; do not publish
it. For session motion, use `wuling session preview exit`, which performs no
system action. Never use a real exit action merely to inspect its appearance.

`wuling uninstall` prints its plan and removes only unchanged resources it
owns. It preserves user overrides and reports changed files instead of
deleting them. Do not bypass an ownership conflict by removing a user's files.
Boot-unlock theming is an optional, separate Omarchy operation that requires
system privileges; the WULING installer does not perform it.
