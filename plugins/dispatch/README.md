# Dispatch

`Dispatch.qml` is an independent, keep-loaded overlay. Super+D and
`wuling dispatch open|close|toggle` use Omarchy's shell router. Super+Space
and all native launcher keys retain their meanings. The focused output owns
keyboard input; Escape clears the query before closing. Tab/Shift+Tab cycle
modes, prefixes `>`, `=` and `?` select Run, Calc and Ask, and arrows select rows.
Input works while the opening animation builds.

Data is read on opening by `wuling dispatch snapshot`. Desktop entries honor
user precedence, hidden overrides, desktop visibility, TryExec and native
launcher hides. The native terminal launcher receives expanded Exec field
codes as argv; GUI entries go through `uwsm-app -- gtk-launch`. Metadata never
becomes shell source. Run intentionally executes the typed shell command in
the default terminal. Ask passes one argument to `omarchy agent prompt`.
Calc uses a bounded arithmetic grammar, never eval, and copies finite results.

Clip reads Omarchy's history without writing it. It watches that file only
while open, hides the mode when the native clipboard plugin is disabled, and
calls native text/image paste helpers. Clipboard contents never enter WULING's
state. Apps, Run and Ask keep bounded private frequency/history records in
`$XDG_STATE_HOME/wuling/dispatch.json` (0600, directory 0700). Uninstall deletes
that owned file. Do not include snapshots or history in public reports.

Settings: language, motion, palette and native font size. No idle collector.
`wuling.dispatch state` reports open/mode/count/selection/busy without query or
clipboard text. Disabling `wuling.dispatch` leaves Omarchy's menu intact; the
owned shortcut reports an unavailable-panel error. Uninstall removes only the
unchanged binding block and plugin resources. Supported: Omarchy 4.0.6 and
4.5.0-rc2. Entry point and copied-kit provenance are in the manifests.
