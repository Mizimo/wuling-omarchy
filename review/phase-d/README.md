# Phase D independent verification

Inbox v164/v165; candidate `03df1dda26aeac14a4e50fecb3f9dc1311a01e65` (D.1).
The native update was reported separately before the VM work. Three findings
below remain; the design lead has accepted the DND finding as P2 and assigned
its repair for E. This is not an unconditional D acceptance.

## Findings

### P2 — the C.1 → D.1 update turns DND off

On each clean VM, install C.1 `e99afec`, call native
`notifications.setDnd(true)`, verify the native reply is `on`, then run the
D.1 installer as an update. Installation and doctor succeed, but the new
provider answers `off`, with `probe.doNotDisturb == false`. No notification
history or user configuration was removed to produce this result.

The first installation of the replacement does not have a WULING notification
state file. `bin/lib/wuling/notifications.py:read()` returns `dnd: false` for
that case; `plugins/notifications/Service.qml` adopts it during boot. The
native provider's active preference never reaches the new provider. An update
can therefore expose ordinary notifications that the user had silenced.

The same symptom appeared on kujira: the retained native state said DND was
on, while D.1 was off. Its native preference was not queried immediately
before the update, so the two VM before/after reproductions establish the
finding. Kujira's WULING DND was explicitly restored to on and verified.

Suggested repair boundary: capture the old provider's active preference before
first takeover, using that version's supported interface, and initialize only
missing WULING state. Preserve an existing WULING preference and independent
plugin disablement. Add a native-on upgrade test on both supported versions.

Evidence: `vm{406,450}/c1-dnd-on.txt`, `update-d.txt`, `d-probe.txt`; native
`kujira/dnd-upgrade-state-and-restore.json`.

### P2 — an exited persistence child silently stops history persistence

On each VM, send one critical notification and wait for it to reach disk.
Identify the single `wuling notifications persist` child, kill that child
only, send another notification, then dismiss both. The running provider has
zero live notifications and two history rows, but its file is byte-for-byte
unchanged: one old live notification, no history. An official shell restart
then resurrects the dismissed old critical notification and loses the new row.

This is a controlled child-exit fault, not evidence of a spontaneous crash.
The user-visible failure persists after the fault: subsequent updates have no
writer. `Service.qml` clears the ready/in-flight flags in `onExited`, but
neither starts a replacement nor reports loss of persistence. Replies from
`persist` also clear the in-flight flag without checking `ok`.

Suggested repair boundary: retain the latest complete pending state until a
successful acknowledgement; restart or explicitly degrade after a writer exit
with bounded retries. A write error must not count as an acknowledged save.
Keep teardown bounded: the separate stopped-writer/restart test below must
continue to finish without hanging the desktop.

Evidence: `vm{406,450}/evidence/writer-exit-results.json`; independent fault
controller `guest-d-writer.py` in the private evidence root.

A separate native audit after the v165 font/radio sequence found no matching
persistence process while the WULING notification probe and doctor still
succeeded. The empty state file's mtime predated the second restart. Installed
notification-source hashes still matched D.1. No native child was killed and
no native persistence fault was injected. This observation is retained in
`kujira/v165/budget/writer-audit.json`; its trigger and whether a new native
notification would persist were not established. Do not silently treat this
state as healthy or as proof of the controlled VM fault's cause.

### P2 — a code in a caller-supplied image path reaches the journal (4.5)

The normal notification body and WULING state were redacted correctly. The
stronger “verification codes never reach files” claim has a separate boundary:
when the sender also puts that synthetic code in an `image-path` filename
that does not exist, Qt's image-load warning includes the complete filename
in the persistent user journal. The first case was found in the final log
audit, not inferred from the implementation.

A fresh 4.5 control run compared the original native provider with D.1. For
both providers, a code only in the body stayed out of the journal; a second
code repeated in the nonexistent image filename appeared in the Qt warning.
D.1's notification state still contained neither code. Thus this is also a
native behavior, not a WULING-only regression. The tested 4.0.6 hint did not
produce that warning; no broader 4.0.6 conclusion is claimed.

Under the literal inbox no-code-in-files requirement, this remains a gap.
The privacy boundary should cover failed media loads, or the specification
must explicitly limit its claim to the notification state store. One possible
repair is non-identifying fallback art for detected verification messages;
checking only the persisted JSON cannot establish the stronger claim.

Evidence: `runtime-log-summary.json`, `log-repro/native.txt`,
`log-repro/wuling.txt`, and their fresh private guest journal extracts. Only
synthetic values were used; no real code or notification was inspected.

## Method and results

Both verifier-owned VMs began at the retained `verified-clean-b` checkpoint,
then received C.1 followed by the pinned D.1 update. They ran one at a time,
with eight vCPUs, nice 15 and idle I/O. Guest versions: Omarchy 4.0.6-1 and
4.5.0rc2-1, Quickshell 0.3.2 (`2b4501a`), Qt declarative 6.12.0-2, Mesa
26.2.5-1. These are functional tests, not a hardware performance comparison.
No tool was injected into the shell process and no product file was patched.

The independent sender remained connected to the real session D-Bus and
recorded `ActionInvoked` and `NotificationClosed`. QMP supplied pointer and
keyboard input; queries, persistent state and immutable captures checked the
outcomes. Native `notify-send` and the installed crash watcher were also used.
Implementation research was read for its claims; its controllers were not run.

| Area | Independent observation on both versions |
| --- | --- |
| DND | Ordinary named-app critical messages are silenced into history; transient and bare normal `notify-send` are discarded under DND. `omarchy-action` and critical `notify-send` bypass. Code bypass occurs only on 4.5. Twelve alternating DND/send pairs produce six live and six history rows. |
| Lifetimes and actions | Low remains at 4.5 s and expires by 5.8 s; normal remains at 7.5 s and expires by 8.8 s; critical remains. A replacement keeps one ID/card. Action 2 emits one callback. `clear` keeps the live toast. |
| Bounds and privacy | 120 actual sends leave 100 live and 20 history; dismissal caps history at 100. A synthetic code is absent from both live and archived files, including app and argv metadata; files/directories are 0600/0700. |
| Corrupt/unreadable state | Malformed JSON and mode 000 each disable the replacement and restore native receipt and closure. Restoring the private fixture permits normal re-enablement. |
| Flood during teardown | Pause the identified writer, start 50 real sends, and restart the shell concurrently. Restart exits 0, continuous reads see no malformed file, and the previously durable critical row returns. 21/20 sends were acknowledged before teardown on 4.0.6/4.5; 29/30 failed during the service gap. Unwritten acknowledged rows are not claimed durable. |
| Handoff | Three disable/enable cycles for notifications and OSD: one close event per fresh send, one live row when WULING is active, and one matching native/WULING OSD surface. D-Bus name ownership alone was not used as evidence. |
| History routes | With Terminal off or Comms off, explicit history replays six of eight rows under DND, without adding history on dismissal. Empty replay produces one low toast. Normal `showHistory` opens the Terminal and exposes the full scrollable log. |
| Hostile argv | A real toast click preserves spaces, quotes, backticks and command-substitution syntax as one literal argument; the injection sentinel is absent. Invalid JSON, empty argv, a leading-dash executable and a non-string argument are rejected. |
| Keyboard | Real navigation through Down/J/Tab and Up/K/Shift+Tab, button 2, Delete, Backspace, Escape and idle focus release. The installed version's comma-family shortcuts are exercised separately, including DND, dismissal/action and history. |
| Hover and overflow | 51 visible-test sends produce a flat stack and a `+N` tail. An explicit pointer leave/enter holds a low toast beyond its minimum; new arrivals wait until leave or the 30 s bound. |
| Crash path | Two identical synthetic records enter the actual guest journal. The unmodified installed watcher, with only agent-choice lookup replaced by a private fixture, emits one critical `omarchy-action` toast under DND. The stored discrete argv preserves a semicolon in the synthetic executable name. No real process was crashed and no agent was launched. |
| OSD | Native panel route and text-only payload; `40 dB` remains intact and percentages have no doubled suffix. QMP volume up/down/mute uses a private null sink, changes actual values and opens OSD. A real foot client receives a line through the OSD and retains pointer/keyboard focus. |
| Outputs | 4.0.6 maps notifications on both outputs. 4.5 pins a nonempty stack to its first focused output, keeps it there after focus changes, and chooses the new focused output after clearing. OSD uses the focused output and returns to the surviving output after removal. |
| Appearance | Four themes at 1366×768: readable summaries, action rows, close glyph, overflow strip and segmented OSD. Raw captures remain private. |

Shell transition logs are retained. Both versions log native
notification IPC registration conflicts during provider transitions, despite
single receipt/closure afterward; this is not a claim of warning-free handoff.
Unrelated native bar/panel teardown warnings also occur.

Harness corrections are evidence, not product findings: the first hover run
had not moved the pointer away before remapping the surface; the corrected
leave/enter run is authoritative. `wtype` media keys did not invoke the native
bindings, so QMP volume keys supply the actual key evidence. A first history
controller used invalid section names; the corrected run uses the documented
section enum. Captures were not overwritten to conceal any of these attempts.

## Kujira update and v165 hardware continuation

The normal C.1→D.1 update succeeded and doctor passed. Language, theme,
overrides, background and the original lid stanza were preserved. Clone
configuration changes are limited to adding the two new replacements and their
native-source restore entries. The owner client stayed on workspace 1 with
unchanged address/workspace/mapped metadata; the session stayed unlocked.

The v164 workspace command failed with exit 7 because this compositor expects
Lua. Testing stopped and that first result was delivered before VM testing.
After the VM matrix, the v165-authorized Lua focus route successfully reached
empty workspace 9 and returned to 1. Every capture had pre/post checks for
zero workspace windows, empty activewindow, zero special-workspace IDs and no
live or historical notification. All twelve images from the two attempts are
retained privately, with immutable filenames. They contain the permitted local
USER; the inspected images have no SSID, network address, online account or
real notification. No image was uploaded or committed. The lead's separate
four-theme/toast/OSD showcase captures were not repeated.

For native font size 16, each of two runs used an official shell restart,
with more than 15 seconds between restarts, then the native text-size command.
The corrected six-frame run invoked captures at **0.231, 0.724, 1.000, 2.000,
3.000 and 5.000 seconds** after the open command returned. Capture completion
was at 0.379, 0.800, 1.077, 2.074, 3.073 and 5.077 seconds. The first frame
shows the panel shell/footer before its content; the next has complete clock
and header glyphs. Link/Agent data fills by the 2-second frame. No sustained
selective clock/header glyph loss was reproduced. The sequential privacy
gates delayed the nominal 0.5-second image; this is not exact presentation-time
measurement. The first run's earliest image began at 0.389 seconds, with
clock/data placeholders; it was retained rather than overwritten. Original
font files, modes and dconf scaling were restored byte-for-byte and the bar
returned to size 30. Evidence: `kujira/v165/font16{,-r2}/`.

Real XF86 bindings were driven by an external Wayland virtual-keyboard client
using the standard evdev keymap, after checking the empty-workspace/focus gate.
It permits only the four tested media keys, uses no root/input device access,
and loads nothing into the shell. Brightness changed **68→136→68** raw units.
Volume up changed both channels **19205→22282**, then down to 19005 because of
rounding; both channels were explicitly restored to **19205**. Each route
opened the WULING OSD. The default sink/mute state stayed unchanged, no audio
stream was running and no sound was played. This is actual binding/value/OSD
evidence, not just an IPC return.

Right-clicking the Wi-Fi and Bluetooth tiles opened the corresponding native
panels, which were then closed without selection. The full connection-state
hash and controller Powered/Discoverable/Pairable values matched before and
after each panel. The exact original overrides were restored. An initial
harness allowlist incorrectly expected the Wi-Fi target to be `omarchy.wifi`;
it stopped before clicking and restored all fixtures. The corrected target
`omarchy.network` was read from the product's status/action contract.
Evidence: `kujira/v165/events.jsonl`, `result-r2.json` and controller logs.

Final continuation audit: workspace 1, same owner client metadata, unlocked,
protected hashes unchanged, radios unchanged, DND on, no armed marker. Kaede
was untouched; no native logout, lock, suspend or reboot occurred. The boot
screen still needs the owner's attended LUKS boot.

## Native resources

The phase-0 method was retained: smaps_rollup PSS/USS, process ticks over
monotonic time (100% means one core), and per-process DRM clients deduplicated
by device/client. There are 91 idle samples over 900 seconds and 31 open
samples over 300 seconds at ten-second spacing. Idle uses workspace 1;
open/cycle work uses authorized empty workspace 9 and restores 1. Boot/process
identity, unlocked/stay-awake state, owner metadata, layers and protected
settings were guarded. External remote workloads were recorded only.

| State / process | PSS median [min–max] MiB | CPU weighted mean / p95 % | FD range | Thread range |
| --- | ---: | ---: | ---: | ---: |
| Idle 900 s / shell | 282.01 [280.67–289.83] | 0.053 / 0.200 | 119–120 | 25–26 |
| Idle 900 s / compositor | 41.04 [41.03–41.04] | 0.147 / 0.200 | 134–138 | 16–16 |
| Terminal open 300 s / shell | 288.48 [280.13–294.67] | 0.850 / 0.990 | 124–124 | 30–30 |
| Terminal open 300 s / compositor | 41.03 [41.02–41.03] | 0.140 / 0.202 | 140–142 | 16–16 |

The measured shell idle median is **22.45 MiB below** the accepted 304.46 MiB
baseline, and average CPU is below 0.2%. Read-only observation IPC is included.
This is not a causal memory-saving claim: process age, warmup and cache/swap
residency differ. Shell swap PSS is zero; compositor swap PSS is 59.93 MiB,
versus 27.73 MiB at baseline. DRM counters remain separate from PSS and must
not be summed across clients/processes as unique physical memory.

The same status-helper PID was sampled throughout the open capture: median
PSS **15.70 MiB** [14.63–16.13], average CPU **0.813%**. Short-lived commands
and unrelated native helpers are excluded. The notification writer was absent
throughout, as separately audited above. Consequently these figures describe
the observed desktop; **they do not certify a healthy all-features process-tree
budget**. A repaired persistence lifecycle needs its own incremental check.

Twenty Terminal cycles each verified the actual open layer and its removal,
with samples after 3 seconds open and 5 seconds closed, then a final 30-second
settling point. No status helper remained at any closed sample. Shell PSS was
268.58→270.71 MiB, **+2.13 MiB** settled (+1.86 MiB USS). Closed samples ranged
269.94–274.76 MiB, peaking at cycle 9 and then declining; FDs were 119–120 and
threads 25–26, ending at their original 119/25. Compositor settled PSS changed
by 0.00 MiB. This sequence establishes neither zero growth nor a long-duration
leak; it does not show a continuing cycle-by-cycle increase. The positive
settled difference is retained rather than rounded away.

Evidence: `kujira/v165/budget/{samples.jsonl,summary.json,writer-audit.json}`
and the completed controller/exit records. Final restoration retained the
owner client on workspace 1, original hashes and an unlocked session.

## Evidence, cleanup and limits

Private root: `~/.cache/wuling-build/wd1/verifier-v164/`. Host controllers,
per-VM JSON journals, timestamped `shots/`, guest evidence archives, native
update audits and the first delivered message remain there. Nothing from raw
logs, screenshots, account names or machine addresses is committed here.

Both main runs completed two removals, verified native notification/OSD
receipt afterward, and deleted WULING history and its empty state directory.
The final inventories were compared with the accepted inventory for the same
clean checkpoint: only two ibus session files differed on 4.0.6; 4.5 also
changed its native herdr log. Those unrelated files were not erased to force
an empty diff. The focused 4.5 privacy control was separately uninstalled.
All guests shut down normally; both owned containers and all armed fault
markers are gone. Sender, crash-watcher and guest source fixtures were removed.
The existing baselines and sole `verified-clean-b` checkpoints remain.

No long-soak result is inferred from these short runs. The independent visual
checks concentrate on 1366×768 and output routing; they do not repeat the implementation's entire fractional-scale
geometry matrix. History display/replay was exercised; a stored Comms-row
pointer action was not independently repeated. Atomic JSON integrity during
process teardown is not a claim of power-loss durability.

At cleanup the private round occupied about 111.5 MiB, including the pinned
checkout and evidence. Kujira's 44.7 MiB staging/helpers/captures were collected
and removed after verifying the installed product did not reference them;
no owned native controller or armed marker remains. Final audit evidence is
`kujira/v165/final-audit.json` and `kujira/v165-native-cleanup.json`.
The two retained VM directories occupy about 21.35 GiB together. The named
unused runtime image (1.34 GB logical size) was removed, along with about
148 MiB of reproducible copies from the accepted B/C round. No shared prune
or implementation container operation was used.

`tools/check` passed on the pinned D.1 checkout with this report staged: 52
runtime tests plus generation, syntax, metadata and staged privacy checks.
Only this sanitized review is committed; E changes in the shared tree were
not tested or modified.
