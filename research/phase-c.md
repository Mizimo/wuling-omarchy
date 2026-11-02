# Phase C: bar and Field Terminal

WULING now provides two independent Omarchy plugins, `wuling.bar` and
`wuling.terminal`. The bar draws WULING's menu, identity, workspaces, active
window label, clock face and power entry while loading the other widgets and
panels from Omarchy's installed registry. The Terminal uses the native square
panel and dismissal/navigation rules. No upstream implementation is copied.

The shared QML kit is generated into each plugin as regular files with hashes.
It follows native font scaling, the four WULING themes and other themes'
palettes. Overrides reload after first creation, atomic replacement and
in-place edits; English, Traditional Chinese and Simplified Chinese are
included. The four shipped theme previews now show the real bar, desktop and
one neutral terminal window, without an open menu or backdrop.

## Data and ownership

`wuling status` emits versioned JSON. Its visible-panel watch has one bounded
schedule, concurrent nonoverlapping slow probes and a 40-sample telemetry
history. Closing the Terminal stops the schedule and discards its state.
Agent usage projects Omarchy's existing display records; no collector or
credential reader is added. Media selection and transport use the native
service. Actions are fixed argv calls, and pending level changes coalesce.
Comms remains empty until phase D; dangerous footer buttons open native System
until phase E supplies the replacement power menu.

Installation owns two plugin directories, the bar selector, the Terminal
layout entry and a Super+Ctrl+G Lua block. Effective key conflicts are checked
before writes. Updates preserve independent disablement, native placement and
user overrides. Removal preserves changed shared entries. The official shell
restart avoids the stale live bar IPC observed on 4.0.6.

Font rollback copies now live outside fontconfig's search tree. Hidden sibling
backups had still been discoverable, leaving Qt with a font path removed after
activation. Unchanged fonts are not replaced. A separate font filesystem that
cannot support the atomic backup rename is refused. Recovery removes child
backup directories before its own newly created empty state root.

The phase B rollback hotfix is separate (`2e46f48`); its explicit native-theme
scope is documented in [theme-effect-scope.md](theme-effect-scope.md). The
phase C lifecycle tests include that hotfix.

## Verification

The candidate passed `tools/check`, including 40 unit tests, deterministic
kit/theme generation, metadata, syntax and staged-file privacy checking.
Runtime tests used disposable VMs running Omarchy `4.0.6-1` and `4.5.0rc2-1`,
with real QMP keyboard, pointer, wheel and drag input. Both started from the
clean B checkpoints after the host reboot. Tests interrupted by that reboot
were discarded and repeated; completed earlier matrix results are retained.

| Check | 4.0.6 | 4.5.0-rc2 |
| --- | --- | --- |
| Fresh/repeated install and remove; doctor and native plugin validation | Pass | Pass |
| Concurrent app write at native theme barrier; no unrelated journal data | Pass | Pass |
| Read-only skill directory, SIGKILL recovery, failed final activation | Pass | Pass |
| Effective Super+Ctrl+G conflict refused without changes | Pass | Pass |
| Native panel shortcuts, clicks, Escape/outside dismissal, clock format/timezone, workspace/menu input, Tab handoff | Pass | Pass |
| Four bar edges, 1366×768, 1920×1080, scale 1.25 | Pass | Pass |
| Two outputs, focused-output native/Terminal panels, unplug with a panel open | Pass | Pass |
| Official bar move/set/transparency; hide/show; empty-space double-click | Pass | Pass |
| Duplicate singleton placement, section overflow and shortcut reachability | Pass | Pass |
| Native indicator reveal/tooltip/action, keyboard layout, weather input | Pass | Pass |
| Terminal under native bar; Terminal disabled; broken bar loader falls back | Pass | Pass |
| DND, level click/drag/wheel/keyboard and native OSD; synthetic media transport | Pass | Pass |
| Synthetic agent usage, closed watch stopped, all data sections disabled | Pass | Pass |
| Both presets/palettes, languages, reduced motion, live configuration | Pass | Pass |
| Native text size 16/reset and a non-WULING theme | Pass | Functional pass; visual observation below |
| Final removal: configuration inventory and logical dconf values restored | Pass | Pass |

The native agent widget was unavailable on the 4.0.6 fixture; the 4.5 fixture
also exercised its left/right/middle input and tooltip. Synthetic Agent data
was separately checked in both Terminals. Physical battery, Bluetooth devices,
tray applications and brightness remain the verifier's real-hardware matrix.
No virtual GPU result is used to claim the kujira CPU/PSS budget or soak gate.

The final inventory fixture initially recreated 4.5's `shell.json` with mode
0644 instead of its original 0600. Contents were identical. Restoring that
test-induced mode difference produced a clean comparison; the product was
not changed to overwrite user-selected modes.

Raw evidence is outside git in round `wc1`: `matrix-rest-406.log`,
`matrix-450.log`, `layout-final-vm{406,450}.log`, `hardening-v411-{406,450}.log`,
`extras-v411-{406,450}.log`, `independence-{406,450}.log`,
`font-steady-vm{406,450}.log`, `scale-observe-450.log`,
`media-v411-{406,450}.log`,
`c-lifecycle-vm{406,450}-r2.log`, `final-lifecycle-406.log` and
`final-lifecycle-450-r2.log`, with private inventories and captures alongside.
The published previews contain only the neutral VM fixture and project assets.

The last visual pass used a new login. Comparing it with the previous login
showed native IBus session records and a native service log changing; those
unrelated files were left untouched. A new same-login install/remove control
then returned the full configuration inventory and logical dconf values to
its own baseline on both versions (`same-login-cleanup-vm{406,450}.log`).

The original observation after a fresh 4.5 login and native text-size change
to 16 was missing Terminal text, including the large clock and header. **The
frame was overwritten; only the contemporaneous observation remains.** The
previous report incorrectly cited `shots/vm450-font-scale-16.png` as the bad
frame. That file is complete: its clock reads 08:25:03 and its host mtime is
00:25:03, matching `font-steady-vm450.log`, not the 00:15 run in
`font-scale-450.log`. No surviving bad frame has been identified.

The 00:15 candidate already contained the font-backup fix: the retained
`c-before-hotfix/bin/lib/wuling/lifecycle.py` (00:02:32) uses the dedicated
`font-backups` directory, and the subsequent install completed at 00:12:28.
These host times are 2026-11-02 PST. This does not establish a cause for the
observation. Do not attribute it to Qt, virgl or the product. Three later
timestamped captures across roughly ten seconds, `shots/vm450-scale-reopen.png`,
and the final edge/fractional-scale captures show complete text;
`scale-observe-450.log` records those controls. The independent verifier should
repeat the cold-login text-size change, including on real hardware. New
capture helpers use unique run IDs and frame timestamps and refuse overwrite.

## Design decisions and remaining phases

The Terminal retains the native square frame, as approved in DESIGN §4.
Its field clock uses 54 px and HUD 56 px. The proposed HUD focus decoration
was removed in accordance with DESIGN §8.7; [focus-events.md](focus-events.md)
records the missing complete compositor geometry event stream. No polling or
unused focus plugin remains. There is no additional requested design change.

Notifications/OSD, Dispatch/power, session animation and sound remain phases
D–F. The Arrival first-frame experiment belongs at the start of E. Phase C's
remaining acceptance is the independent verifier's hardware and budget work.
