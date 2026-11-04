# Field Terminal

`Terminal.qml` is a `bar-widget` using the installed `qs.Ui.Panel` and
`KeyboardPanel`. Omarchy routes it to the focused output and owns focus,
Escape, outside clicks and handoff to the next panel. It also runs under the
native bar. The native square frame is retained.

Open it with `wuling terminal open|close|toggle` or Super+Ctrl+G.
`wuling terminal open PAGE` opens `comms`, `performance`, `power`, `audio`,
`system`, `calendar`, `wifi`, `bluetooth` or `tailnet` on the focused output.
Tab/Shift+Tab switch panels. Up/Down select a control; Enter/Space activate it.
Escape, Left and Backspace return from a page; a second Escape closes Terminal.
Power uses Left/Right to select an available profile, Enter to apply; Backspace
returns. Performance uses S to sort and Enter to open btop. System uses C to
copy and F for Fastfetch. Calendar uses PageUp/PageDown and T for today.
Closing forgets the page. Left/Right and Home/End adjust a focused level.
Overview level drags and wheel changes call the native command and OSD used by keys.

`wuling status --watch` starts while open and stops on close. Entering a page
replaces the collection set with the configured clock and that page only. Pending probes and
subprocess descendants stop with their collector. State and bounded telemetry
history are discarded on close. Native agent display records are read, never
credentials, and no agent collector is started. Missing hardware hides its
control; no agent usage hides that section. Each UPower battery pack has its
own cell. Zero full capacity means absent, not zero charge; low charge is a
static vermilion value.

Signal remains visible without a player and keeps paused players. Selection
and transport use Omarchy's native media service. Art is loaded only while
the overview is open. While playing, public MPRIS supplies length and position
only when exactly one player matches native identity, desktop entry, track
metadata and playback state. Ambiguous, unreadable or inconsistent candidates
leave the times unknown and progress empty; this never selects a player.
Paused players remain visible without querying MPRIS times.
Optional `cava` runs at nice 19 only while that view is
open and playing; WULING does not install it. Without cava, the public
PipeWire peak monitor follows a uniquely matching playback stream. A missing
or unsupported stream leaves flat cells. The stock peak monitor negotiates
stereo; mono streams use the flat fallback to avoid its channel-mismatch log.

Comms reads WULING's private, redacted history while the notification plugin
is enabled. Rows show source, time, summary and two body lines; activation
expands the full retained body and available actions. `+N` opens the history
page with every retained row. `CLEAR ALL` clears history through the existing
notification service. Actions are revalidated there, including expiry and
the installed native action rules. Unchanged samples retain delegates while
a pointer is held down. The detail page covers the footer, preserves the
clock and releases its row objects after closing.
The footer's dangerous actions open the System route, never execute
logout, reboot or shutdown directly.

Settings: `terminal.sections`, `labels`, `motion`, `language`, and theme preset,
palette and native font scale. This plugin persists nothing itself. Actions
are fixed argv commands in `bin/lib/wuling/actions.py`; errors appear in the
panel without logging native service responses. Pending level actions coalesce.

Supported versions: Omarchy 4.0.6 and 4.5.0-rc2, through the installed panel and
scoped bar API. Disable with `omarchy plugin disable wuling.terminal`; native
panels and shortcuts remain. The owned new key is removed by
`wuling uninstall`, which preserves edited user bindings and settings.
The manifest declares the native `right` default section for re-enablement.
Per-output `wuling.terminal.<output>` IPC exposes `geometry`, `history`, `page` and diagnostic `state` to
the notification plugin. Geometry comes from the panel instance's public
`cardOrigin` and content dimensions; no private child is traversed.
`truncated` lists visible WULING text in the open panel that is elided or
overflows its box, so a check can confirm that fixed labels wrap instead of
being cut; it reads only WULING's own items and returns `[]` when closed.

Changes to `terminal.sections` restart the open collector with the new selection;
an empty selection stops collection. A native panel absent from the bar returns
`panel_unavailable`; the Terminal stays open with a translated explanation.

Native bar boundary on both supported versions: clicking its clock while Terminal
is open closes Terminal on the first click; the second opens the calendar.
The same behavior occurs under Omarchy's own bar. WULING does not alter it.

Wi-Fi's overview reads active connection metadata. Its page reads public
NetworkManager settings and cached access points; opening never starts a scan.
S or SCAN explicitly refreshes the list. Secured networks take an inline
passphrase, handed to nmcli through stdin and immediately cleared from the
input. A replacement secret uses nmcli's password-file parser on `/dev/stdin`,
avoiding readline's saved-secret prefill. No WULING credential file is written;
NetworkManager owns saved profiles. Enterprise authentication stays in Omarchy's
network panel. Network names belong on the local panel, not in public logs.

Wi-Fi, Bluetooth and Tailnet tiles open their detail pages; right-click keeps
the native panel route, except Tailnet, whose right-click opens its page too.
Wi-Fi off/disconnect and Tailnet stop require an 800 ms pointer or Enter hold;
releasing or leaving the control cancels it. Bluetooth uses public BlueZ state
and Omarchy's power/device helpers. Its tile survives a soft-blocked adapter
disappearing from USB. S starts bounded discovery; leaving stops only WULING's
client. Tailnet is available only with the installed CLI. Its login URL goes
to the native browser launcher and is excluded from status output. Radio
failures stay on the page, and leaving cancels in-flight radio actions.

Night is available when the native toggle and hyprsunset are installed;
a stopped service reads Off and the same native toggle starts it on demand.
Agent labels omit parenthetical details and share a measured column capped at
66 design pixels. The default-agent tag reads only native display metadata.

The overview clock opens Calendar, the user label opens System, telemetry
values open Performance, battery cells and the profile tile open Power, and
the volume icon opens Audio. Brightness keeps the native monitor panel.
Performance reads `/proc` deltas, bounds its CPU history to 60 samples, and
retains both process rankings; changing sort needs no extra reader. Power uses
UPower's pack energy and charge history and the official profile helper.
No lid or idle policy is inferred.

Audio projects public PipeWire device/stream state. Device selection uses
Omarchy's native helpers, including moving existing streams; active output
levels follow its DSP-aware physical sink selection. Sliders retain delegates
while levels change, discard them on identity/topology changes, and coalesce
queued changes by node ID and serial. Volume uses PipeWire's cubic amplitude
mapping. No microphone peak monitor is created: on 4.0.6 that monitor itself
activates the native recording indicator. Input selection, volume and mute
remain available. Playback streams exclude the shell and native tuning nodes.

System reads local host/session information and installed `release.json`.
Installation records the checkout's commit, exact tag (or `unreleased`) and
commit date; source archives may provide the same three fields in a root
`release.json`. Without either source, installation writes `unreleased` and
leaves commit/date empty. Clipboard text goes over
stdin with no inherited capture pipes. Successful native TUI launches close
the panel; a failed launch stays on the page. Calendar is a local Monday-first
month grid with ISO weeks, calculated at noon to avoid daylight-saving shifts.

Config is reached by the head's three-dot button or `wuling terminal open config`.
The head remains when clock or every section is disabled. Settings use
`wuling config set`, preserving the existing transaction and ownership checks;
an error retains the page and old stored value. Menu selection reapplies the
native theme without changing the background. A submitted transaction finishes
if the panel closes; the page collector still stops immediately. LOGIN MUSIC
accepts a path, APPLY (also Enter), or CLEAR; validation does not play audio.
Its decoder is pw-play's existing libsndfile dependency. Missing/non-audio paths
are rejected before modifying configuration. Removing an already configured
file does not break unrelated settings.

THEME, BACKGROUND and FONT use installed native menu routes, selected by menu
content rather than version. DISPLAY, INPUT and KEYS open the corresponding
native Lua file through Omarchy's config editor; DEFAULT APPS opens its menu.
WULING does not reproduce these editors or providers.
