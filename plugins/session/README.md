# Session motion

The keep-loaded service synchronously reads a marker and the Arrival switch
before creating its first ink frame. A missing marker counts as a login only
when the supported Hyprland instance signature is less than 30 seconds old.
Unknown formats and older sessions are marked without playback. Shell restart,
update, first install on an existing desktop, unlock and late enable do not
replay it. `wuling session preview arrival` bypasses the login gate.

After ink has submitted, the full animation loads in the same shell. No font,
data reader or wave object delays that first frame. A separate watchdog plus a
wall-time frame check enforce the 3.5-second lifetime. Normal completion unloads
the animation and all of its windows, images and timers. Qt's shared font/scene
caches can remain; repeated previews must not produce steady growth.
No forced GC, second shell or native patch is installed. The existing owned
Hyprland block disables compositor animation only for `wuling-session-arrival`,
so wallpaper cannot flash through its first ink frame. The QML sequence still
animates; Exit and unrelated layers retain their existing rules. This owned
rule is updated and removed with the bindings and takes effect on next login.
Wall time from the first ink swap drives the sequence, rather than an animation
clock which can smooth out startup stalls.

A single bounded metadata read supplies versions, interface (no address),
optional battery, operator and display mode. Unavailable readings are `—`.
There is no public background presented-frame signal on the tested versions,
so arming uses the specified one-second bound. Preview does not request login
music. Every animation object disappears after release.
The bar's optional six-slice reveal has its own expiry if the session service
vanishes. Disabling either the bar or sound service remains supported.

`Exit.qml` is created only for a confirmed dangerous Power action. A worker
prepares while that menu is open and waits for a confirmation line; after
receipt, a child detaches from the QML Process lifetime. It invokes the unchanged
native action once at hold+560 ms, or hold+120 ms with reduced motion, using the
inherited environment. QML never owns that deadline. Disabled exit motion, a
missing plugin or a failed visual load dispatches immediately.

The exit covers every live output in 16×9 cells and shows the theme's unlock
image at native pixel size. Other themes use our vector mark in their text
colour. A surviving session gets its desktop and a notification back after ten
seconds. A separate QML watchdog releases the visual tree if the worker dies.
`wuling session preview exit` performs no system action and does not affect OSD.
During real exit, an expiring runtime `exit-osd.json` lease suppresses WULING OSD;
each show reads it synchronously, with no watcher or polling. Native OSD and new
notifications can appear above ink, as specified. No PATH wrapper is installed.
If an external SIGKILL kills the Exit worker between hold completion and the
action, that action will not happen; the desktop returns after about ten seconds.
This external termination is outside the action guarantee.

State stays under `$XDG_RUNTIME_DIR/wuling/`: login markers, the bounded OSD
lease, an exit lock and (for external themes) a temporary recoloured mark.
Settings: `session.arrival`, `session.exit`, `session.theme`, `motion`. Internal IPC:
`wuling.session begin/finish/state` and `arrival/inspect`; tokens reject stale
exit replies.
Supported: Omarchy 4.0.6 and 4.5.0-rc2. Disable with the official plugin command;
Power still executes its native actions.

The optional theme wave watches only `current/` at idle. A new `next-theme`
directory requests one capture per output. The installed theme-set, Color,
Style and Background files must match one tested content contract, checked at
startup and again before each cover. Unknown content disables this effect,
leaving the native theme command untouched; doctor reports the boundary.
The installer owns a separate `wuling-theme-wave` no-animation layer rule.

Every output must have a capture and two cover swaps before the native palette
arrives. A changed theme name is an additional, earlier cutoff. Any late output
cancels the whole effect; it never displays an old screenshot after revealing
the new theme. The cover ignores input and lasts at most 1.5 seconds from the
preparation event. Same-theme refresh, failure, lock, Arrival, Exit, output
changes, disabled settings and reduced motion cancel or bypass it. The reveal
is a 420 ms, 16 by 9 cell wave with a half-level open cue. All captures, effect
objects, windows and active timers unload afterwards. Only aggregate counters
and the last timing record remain in memory (`wuling.session themeState`).

The native background has no public completion fence. The wave uses its
content-gated reveal duration from the last palette assignment, plus 67 ms,
bounded by the total 1.5-second deadline. These durations and the padding live
beside the content hashes. This is a
contract-derived time bound, not an observed completion fence.
It reads no private native object tree, adds no wrapper, and never waits on or
changes an Omarchy action. Lock state uses the existing read-only IPC only
during an attempt.
