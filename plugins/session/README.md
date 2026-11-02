# Session motion

`Session.qml` is a minimal keep-loaded service. In this phase it creates
`Exit.qml` only for a confirmed dangerous Power action, on every output. The
worker prepares while the menu is open and waits for a confirmation line;
after receiving it, a child detaches from the QML Process lifetime. The full sequence dispatches the
native action at hold+560 ms, reduced motion at hold+120 ms. An independent
Python worker owns this deadline and invokes the unchanged native action once,
with the inherited environment. No preparation runs while the menu is closed. Disabled motion, a missing plugin or a failed
visual load dispatches immediately. QML never owns the action callback.

The overlay consumes local input, covers the live desktop with 16×9 cells,
and uses the theme's unlock image at native pixel size. Other themes use our
vector mark in their text color. The overlay remains until the session ends;
a surviving session gets its desktop and a notification back after ten seconds.
A separate QML watchdog also releases the visual tree if the worker disappears.

`wuling session preview exit` performs no system action and does not affect
OSD. During a real animated exit, a private expiring `exit-osd.json` lease in
`$XDG_RUNTIME_DIR/wuling` tells WULING OSD to discard shows. Each OSD show reads
it synchronously; no watcher, polling or plugin connection exists. The lease
expires even if this plugin or its worker dies. Native OSD, when WULING OSD is
disabled, and new notifications can appear above the ink as documented in
DESIGN. No native command, PATH wrapper or layer rule is installed.

State: a per-user exit lock, the bounded runtime lease and a temporary recolored
mark for external themes. The worker cleans its own lease and mark; runtime
state disappears with the login runtime. Settings: session.exit and motion.
`wuling.session begin/finish/state` is the internal worker handshake; the token
rejects a stale finish. The animation tree is destroyed after release.
Supported: Omarchy 4.0.6 and 4.5.0-rc2. Disable with the official plugin command;
Power still executes its native actions. Arrival and preview arrival follow in
phase F; the setting is reserved now, without a startup animation in this phase.
