# Phase E — Dispatch, Power and Exit

Implemented against inbox v420 and DESIGN `0c65c69`. D.1 (`03df1dd`) and the
accepted Arrival first-frame experiment (`aff1561`) were delivered separately.
Full Arrival, sounds and the soak remain phase F. No upstream file or native
binding changes, no PATH wrapper, and no workstation operation are included.

## Components and ownership

Dispatch is an independent overlay on Super+D. Super+Space remains native.
Its five modes use bounded, on-demand data: desktop entries with XDG precedence,
native clipboard history, recent commands/questions, and a small arithmetic
parser. GUI apps use the native desktop launcher; terminal apps expand Exec
field codes into argv for Omarchy's terminal launcher. Run intentionally accepts
a shell command; Ask passes one prompt argument to `omarchy agent prompt`.
Clipboard data is never stored by WULING. Its own bounded history is private
(0600 in a 0700 directory) and removed on uninstall.

Power reads the installed System entries and user extension on each opening,
including guards. One owned JSONC `system` action routes the existing native
entry points to it. Dangerous actions require an uninterrupted 800 ms hold;
release, moving off the card, selection change and Escape cancel. Lock state
is checked before opening. Disabling Power uses the native existing System
submenu; removal restores the original root entry and retains subsequent user
edits. JSONC parsing preserves comment/comma syntax inside quoted strings.

Exit uses a minimal keep-loaded service and a visual tree created only on
request. The menu prepares an idle stdin worker while open. Confirmation forks
a detached child; a separate timer thread executes the unchanged native action
once, independently of visual IPC or QML lifetime. The action inherits its
environment. Full motion targets hold+560 ms, reduced motion hold+120 ms; a
disabled sequence dispatches immediately, and a failed visual handshake
expedites the pending action. A surviving session gets the desktop back ten
seconds after dispatch. The visual service also has an independent watchdog.

The all-output overlay uses 16×9 cells and the theme's native-pixel unlock mark.
WULING OSD synchronously reads one expiring runtime lease per show, with no
watcher or idle polling. It does not map during a real animated exit. The lease
expires even if the service or worker disappears. Preview sets no lease and
does not affect OSD. Native OSD when its replacement is disabled, and newly
arriving toasts, retain the accepted ability to appear above the ink.

The installer adopts new independent components once, preserves user
disablement on updates, and checks both new keys against effective Hyprland
bindings. The System extension uses the existing ownership transaction.

## C follow-ups included

Native `unknown` is now a nonzero structured `panel_unavailable` error.
Void hide/toggle calls validate their live public target first. Terminal keeps
its surface and translates errors locally in all three languages. Changing
`terminal.sections` restarts an open collector; closed/empty views collect
nothing. The native clock's two-click handoff is documented.

The stock `dddd HH:mm` clock format, like an absent format, becomes `HH:mm`
without rewriting shell.json. Weekdays follow Terminal's localized pair.
Wi-Fi uses only active-connection metadata, never a scan; connected Tailnet
uses the translated Connected label. Network names are not diagnostic output
or fixtures. Night requires the installed toggle and hyprsunset, rather than
a running service; a null temperature is Off.

Agent names fit their column, parenthetical limit details are removed, and
uppercase labels share a measured column capped at 66 design pixels. A long
micro label tightens its tracking within a bounded range before eliding; the
three reported labels fit without reducing their type size. The ask button is
left aligned, with the native default-agent display name at the right when
known. The last 14 pixels of overflowing body content fade into the ground;
at the bottom the fade disappears.

On the first missing WULING notification state, DND is seeded once from the
version-gated native file. Subsequent WULING state wins, and no native state
file is written. Disabling the replacement returns to the native stored value.

## Verification

Disposable VMs: Omarchy `4.0.6-1` and `4.5.0rc2-1`, Quickshell `0.3.2`
(`2b4501a282689792b62e94f3fb30d8f512324fe6`), Qt declarative `6.12.0-2`,
Mesa `26.2.5-1`. The existing clean D checkpoints were reused. KVM, virgl guest
display, private llvmpipe host, eight vCPUs per VM, nice 15 and idle I/O priority.
Input was real QMP keyboard/pointer input. Captures are outside git.

| Check | Result on both versions |
| --- | --- |
| Dispatch apps | Real GUI and terminal fixture launches preserve `%c`, `%k`, `%i`, `%U` and `%%` semantics; terminal execution uses the installed default terminal. |
| Other modes | CALC copies 14 for `2+3*4`; RUN creates the requested harmless fixture; CLIP pastes native text history into foot through Shift+Insert; ASK with no agent stays open with the translated explanation. |
| Input and isolation | Prefixes, Tab/back-tab, selection, Escape clearing/closing and outside click; native Super+Space remains separate. Disabling native clipboard removes only CLIP; disabling Dispatch returns the documented error. |
| Power entry points | Super+Esc, power key, bar cell and native System route reach the same cards. Short Enter/pointer holds and pointer exit cancel; letter keys only select. A completed hold invokes exactly once. Native fallback and real lock/unlock guard checked. |
| Exit failure/recovery | Deliberately invalid Exit QML, with an official shell restart to invalidate component caching, still executes the action once. An action that leaves the session alive releases the overlay and sends one notice after ten seconds. |
| OSD | Real animated exit suppresses the show; give-back restores it. Disabling the session plugin mid-sequence does not strand OSD. Preview leaves it available. No native action/PATH modification. |
| Layout | Four themes at 1366×768; 1920×1080 scale 1.25; 3840×2160 scale 2; 768×1366 portrait. English, Traditional and Simplified Chinese. Focused second output, all-output Exit, and Dispatch hot-unplug fallback. |
| Native panel errors | Positive Terminal geometry and negative native IPC controls, including disabled open/hide/toggle. A synthetic Tailnet tile with the real missing native target checks the visible translated error; Terminal remains open. |
| Collector | Open clock-only → link/telemetry replaces the process and arguments; an empty selection and closing leave no collector. |
| DND | Native On + absent own state seeds On without changing native bytes; own Off survives shell restart; disabling returns native On. Native fixture state restored afterward. |
| Real-data layout | Synthetic Session (5-hour), Weekly (7-day), Fable Weekly and Claude Code records; default-agent tag; both presets at 768 high, overflow and bottom position. Installed/stopped Night reads Off. |
| Lifecycle | Independent component disablement survives update; repeated install/remove, original System restoration, edited System-label preservation, private-history deletion and unrelated data preservation. |

Action timing used the prearmed product worker and a harmless bash builtin
timestamp action, avoiding interpreter startup in the measurement. These are
wall-clock dispatch measurements, not compositor presentation timestamps.

| Mode | 4.0.6 | 4.5.0-rc2 |
| --- | ---: | ---: |
| Full, target 560 ms | 562.61 ms | 562.64 ms |
| Reduced, target 120 ms | 122.36 ms | 122.54 ms |
| Sequence disabled | 10.83 ms | 9.71 ms |
| Failed visual load, dispatch on failed handshake | 214.30 ms | 233.27 ms |

An earlier sequential worker allowed visual IPC to delay reduced motion.
The final timer is independent; an automated slow-IPC test covers that failure.
CALC also exposed a native clipboard helper retaining stdout in a background
process. Status-only native launching now disconnects those pipes, with a
real background-process regression test.

## Real exits and recording limits

Logout, reboot and shutdown each completed on both VMs. External X11 capture
of the QEMU display targeted 120 fps for 35 seconds; frame tables and contact
sheets cover all six recordings. No captured desktop/bar frame reappears after
the ink. In the transition interval (capture seconds 1.5–3.5), the largest
inter-capture gaps were 12/11 ms for logout, 10/10 ms for reboot and 10/9 ms for
shutdown (4.0.6/4.5). This is sampling evidence, not a presentation-feedback
guarantee. Later firmware/host intervals contain gaps up to 635 ms.

Logout reaches a black mode-change interval and the native greeter. Reboot
and shutdown expose native system-stop messages after the graphical session
ends; reboot also shows inactive display, TianoCore, bootloader/kernel output
and the greeter. The old desktop does not return. Shutdown ends the QEMU
process; a later fresh boot/login was checked separately after recording.
The optional `omarchy plymouth set-by-theme` operation was not applied to these
checkpoint images, so the next-screen mark is still Omarchy's original mark.
The Exit mark itself is the active WULING unlock asset. No upstream boot or
login behavior was altered to hide those transitions.

## Retained memory

One quiet shell process per version, with Power opened/closed first and no
previous Exit in that measurement session: baseline, then ten preview rounds,
sampling 2.7 seconds after each request with the service reporting idle.
No forced GC or allocator trimming. Values below are KiB, relative to the
no-Exit baseline in that same process.

| Delta | 4.0.6 | 4.5.0-rc2 |
| --- | ---: | ---: |
| First closed preview PSS | +1,774 | +1,560 |
| Largest intermediate PSS | +4,468 | +3,236 |
| After tenth preview PSS | −2,285 | +124 |
| After tenth preview RSS | −2,332 | +124 |
| After tenth preview private dirty | −800 | +572 |

The final residual is within 2 MiB; intermediate allocator/cache occupancy
is higher, as the table shows. This is a short retention check, not the F soak
or a claim of constant per-round allocator capacity. The visual Loader and
window tree are released; no closed-menu worker or collector remains.

## Evidence and limits

Raw evidence: `~/.cache/wuling-build/we1/`. Useful indices:

- `e-dispatch-r3-{406,450}.log`, `e-dispatch-rest-r4-{406,450}.log`.
- `e-power-routes-r1-*`, `e-exit-test-r4-*` and final `e-exit-test-r5-450.log`.
- `e-exit-armed-timing-r5-*`, `e-load-failure-r2-406.log`, `e-load-failure-r3-450.log`.
- `e-real-*.mkv`, corresponding `.frames.csv`, `shots/*-timeline.png`, and the short `e-exit-logout-preview-406.mp4`.
- `e-layout-r3-406.log`, `e-layout-r1-450.log`, `e-matrix-extra-*` and their immutable captures.
- `e-v419-r3-*`, `e-v420-r2-*`, `e-terminal-r1-*`, `e-panel-fixture-*`, `e-memory-r1-*`, `e-lifecycle-r2-*`.

Unit tests additionally cover unsafe desktop metadata, arithmetic bounds,
bounded private history and symlink refusal, owned JSONC restoration, binding
conflicts, failed native targets, DND seeding and independent action deadlines.
`tools/check` passes: 74 tests, deterministic generation, syntax/metadata,
staged-file privacy and whitespace checks. Both VMs were uninstalled cleanly
and shut down normally; each retains its original baseline and one new
`e-clean` checkpoint. The previous D checkpoint and this round's containers
and runtime image were removed after saving the new checkpoint.

VMs have no physical Wi-Fi/Bluetooth hardware or authenticated Tailnet/agent.
Live SSID/Connected behavior therefore needs the verifier's hardware check;
no real network name or credentials were collected. Native image-clipboard
helper routing is implemented but the real-paste test here covers text only.
No agent prompt was sent to an external service. Ordinary Power actions use
native commands; real suspend/hibernate were not exercised. Full Arrival,
sound cues and long-duration behavior are not claimed by this phase.
