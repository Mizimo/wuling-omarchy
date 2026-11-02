# Field Terminal

`Terminal.qml` is a `bar-widget` using the installed `qs.Ui.Panel` and
`KeyboardPanel`. Omarchy routes it to the focused output and owns focus,
Escape, outside clicks and handoff to the next panel. It also runs under the
native bar. The native square frame is retained.

Open it with `wuling terminal open|close|toggle` or Super+Ctrl+G. These commands
use the native shell router; the widget registers no duplicate IPC target.
Tab/Shift+Tab switch panels. Up/Down select a control; Enter/Space activate it;
Left/Right and Home/End adjust a focused level. Level drags and wheel changes
call the same native volume/brightness command and OSD as the system keys.

The only data source is `wuling status --watch`, started while open and stopped
on close. State and the bounded telemetry history are discarded on close.
Native agent display records are read, never credentials, and no collector is
started. Signal uses Omarchy's selected player. Missing hardware hides the
corresponding control; no playing media and no agent usage hide those
sections. Comms is empty until the independent notification plugin is shipped.
The footer's dangerous actions currently open native System, never execute
logout, reboot or shutdown directly.

Settings: `terminal.sections`, `labels`, `motion`, `language`, and theme preset,
palette and native font scale. This plugin persists nothing itself. Actions
are fixed argv commands in `bin/lib/wuling/actions.py`; errors appear in the
panel without logging native service responses. Pending level actions coalesce.

Supported versions: Omarchy 4.0.6 and 4.5.0-rc2, through the installed panel and
scoped bar API. Disable with `omarchy plugin disable wuling.terminal`; native
panels and shortcuts remain. The owned new key is removed by
`wuling uninstall`, which preserves edited user bindings and settings.
