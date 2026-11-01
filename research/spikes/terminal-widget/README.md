# Disposable shared-panel model

This is not a terminal. The small third-party bar widget imports the installed
`qs.Ui.Panel`, `KeyboardPanel` and `PanelKeyCatcher`. Enable it in a disposable
VM and call `omarchy-shell shell toggle research.terminal-widget`, or click TEST.
Esc/outside click close; Tab and horizontal arrows ask the host to switch panels.
`omarchy-shell research.terminal-widget inspect` exposes lifecycle state.

A-2 exercises both the independent host and native bar on 4.0.6 and 4.5.0-rc2.
Disable/remove it and restore shell.json after use. No upstream QML is copied.
