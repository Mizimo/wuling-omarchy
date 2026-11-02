# Termination Protocol

`Power.qml` is an independent, keep-loaded overlay on the focused output.
`wuling power open|close|toggle` checks the native lock state before opening.
The installer adds one owned `system` entry to Omarchy's menu extension,
retaining its icon, label and aliases. Super+Esc, power key, bar power cell and
System route all reach it. Native search results and commands keep their own
immediate behavior; no native binding changes.

`wuling power snapshot` reads installed System entries and user replacements
on opening, with native action syntax, visibility and disabled guards. A read
failure uses the seven native actions in order. Arrows select; S/L/U/H/E/R/P
jump without executing. Enter or pointer activates ordinary actions. Logout,
Reboot and Shutdown need an uninterrupted 800 ms hold. Release, pointer exit,
selection change and Escape cancel it; autorepeat cannot complete a second
activation. The action is then handed once to the independent session worker.

Settings: language, motion, session.exit, palette and native font scale. No
persistent state or idle process. `wuling.power state` exposes selection, row
names and hold state for diagnostics. With the plugin disabled, the CLI opens
the existing native System submenu through the official generic shell method
IPC, bypassing the extension action to avoid recursion. Uninstall restores the
exact original System entry when unchanged and preserves subsequent user edits.
Native files remain untouched. Supported: Omarchy 4.0.6 and 4.5.0-rc2.
