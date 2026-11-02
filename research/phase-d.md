# Phase D — notifications and OSD

Implemented against inbox v415 and DESIGN `f67cf4b`. C.1 was delivered separately
as `e99afec`. This change adds `wuling.notifications` and `wuling.osd`, connects
the Terminal log, and applies v413's tabular digits to shared labels. It does
not change an Omarchy key or upstream file. No phase E work is included.

## Implementation

Notifications and OSD use the native clone contract. The installer adds a new
replacement once, preserves later independent disablement, refuses another
active replacement, and restores only a previously enabled native provider.
Edited clone configuration is retained but disabled on removal. Upgrading a C
installation does not revert intervening user edits to shell configuration.

Notification rules come from installed native JS modules behind an exact
version and SHA-256 gate. The manifest records the tested modules; the QML
adapters import them at runtime, without bundling upstream implementations.
The server starts only after the gate succeeds. Failure disables the replacement
through the official command, restores native receipt and is explained by
`wuling doctor`. Optional Terminal geometry lookup runs separately, so it cannot
delay D-Bus registration beyond the native restart command's short deadline.

The flat stack holds at most 100 rows. Only presented rows consume their
lifetime. Hover pauses expiry and holds new arrivals for at most 30 seconds;
overflow waits behind `+N`. Keyboard selection can reach overflow rows. Critical
cards persist; other durations, DND bypass and argv validation follow the
installed rules. 4.0.6 displays on every output; 4.5 pins a stack until empty.
Restart restores critical cards and the native version's grace for other rows.

State is bounded to 100 live and 100 history rows, with a 24-hour history TTL.
One stdin writer coalesces event-driven updates into an atomic 0600 file in a
0700 directory. Images and detected links are excluded; verification text and
its metadata are redacted before writing. `clear` affects history only.
Uninstall deletes the message file; repeated removal can finish that cleanup.
No idle poller or separate Quickshell process is added.

The Terminal reads only WULING's history while its provider is enabled. It
shows the rows that fit, at least three, with `+N` expanding the whole body.
Unchanged status samples retain the same delegates. Row clicks revalidate
stored argv; rows without it have no action. `showHistory` opens and scrolls
the log, or replays six rows when Terminal/log is off, including under DND.
Empty history produces the low-priority empty-state toast.

Terminal declares `barWidget.defaultSection: right`; native re-enablement puts
it in the right section before Power. Its own `KeyboardPanel.cardOrigin` and
content dimensions are sent over per-output IPC. A toast moves only for an
actual overlap, first left of the panel, then right if needed, otherwise back
to its normal position. The 340 px card is never narrowed for this avoidance.
No private native child is traversed.

OSD accepts the existing `osd` payload and the cloned panel `open` route.
It has an empty input region and no keyboard focus. A surface per output avoids
the lost mapping found when removing the screen of a single reused window.
Only the selected output displays it. HUD audio labels use a bounded on-demand
device query, with no idle sampling. Both progress and message-only payloads
follow the active preset, palette and scale.

Service callbacks and live notification references belong to the service,
not a delegate. Models contain values, not native QObjects. Signal connections
are explicitly disconnected on release/teardown. Deferred layout/measurement
and pending image-free state are bounded; no transient delegate installs a
callback into the long-lived service.

## Verification

Disposable VMs: Omarchy `4.0.6-1` and `4.5.0rc2-1`, Quickshell `0.3.2`
(`2b4501a282689792b62e94f3fb30d8f512324fe6`), Qt declarative `6.12.0-2`,
Mesa `26.2.5-1`. KVM, virgl guest display, private software-rendered host,
eight vCPUs per VM, nice 15 and idle I/O priority. Both began from their clean
C checkpoints. No real workstation was operated.

| Check | Result on both VMs |
| --- | --- |
| All urgencies | Low survives to 5 s, normal to 8 s, critical remains; expiry and dismissal work. |
| DND | Ordinary critical from a named app is held; `omarchy-action` and bare critical `notify-send` bypass. 4.5 detected code also bypasses; 4.0.6 does not. Silenced ephemeral message is absent from state. |
| Private state | Synthetic verification code absent from the file, including command/app metadata; modes 0600/0700. Retention and size caps also covered by unit tests. |
| Actions | Real key 2 invokes the second libnotify action once. A competing card command is not executed. Long labels remain inside the card. |
| Click argv | A real toast click preserves quotes, spaces, dollar substitution and backticks as one argument; no injected file is created. |
| Replacement | `replaces_id` updates the existing card. |
| Flood/overflow | 50 critical notifications, visible tail count, keyboard traversal into overflow, deletion and Escape. |
| Hover | Existing low card survives its normal expiry while hovered; arrivals appear on leave or at the 30 s limit. Before/after captures retained. |
| Native keys | Version-specific comma-family routing, DND and dismissal; J/K/Tab/Shift+Tab, numeric action, Backspace/Delete, Escape and 10 s idle release. |
| Restart | Three consecutive official restarts succeed with a visible critical toast retained. |
| History routes | Terminal off, log off, empty history and DND replay; replay does not add history. Thirty-row collapsed/expanded log, actual row click, and a press held across two status samples executes once. |
| Output behavior | Notification all-output/pinned-output distinction, focus changes, pinned-output removal; four bar edges, widget left/center/right placements, 1920×1080 at scale 1.25. |
| v415 geometry | At 1366×768: right panel x=984 gives toast x=634; nonoverlapping center/left panels retain toast x=1016. Measured from captures. |
| OSD | Four themes, progress including `100%`, text-only payload, real virtual-keyboard volume/mute events, native `shell.summon` route, input passing to a real foot window. |
| OSD hotplug | Final per-output implementation: real volume key, focused headless output, then removal returning the open OSD to the remaining output. |
| Native handoff | Disable/enable notifications and OSD independently; actual native receipt/dismissal and native OSD, then WULING receipt. No duplicate notification/OSD handler observed. |
| Missing module | Diagnostic gate input omits `NotificationLogic.js` / `Store.js`; native receipt returns and doctor names the missing module. Upstream files remain intact. |
| Removal | Doctor passes before removal. Two removals succeed; private history and the empty WULING state directory are gone, unrelated concurrent data survives, native notification/OSD receipt remains. |

The crash test fed a synthetic coredump journal record through the **unmodified
installed `omarchy-crash-watch`**. Only journal input and configured-agent lookup
were fixtures. Its real notification sender produced the critical card under
DND with the expected discrete `omarchy-agent-crash` argv. No real process was
crashed and no external agent diagnosis was launched. Hostile argv execution
was tested separately with a harmless local fixture.

The missing-module test kept shell IPC on the real configuration path. A private
launcher redirected only the compatibility input and supplied the installed
version response: Omarchy otherwise reports any alternate root as `dev` before
the module check is reached. This is a diagnostic fixture, not a product bypass.

An early keyboard candidate used OnDemand and did not acquire focus; it now
uses native Exclusive mode only while keyboard mode is active. An early 4.5
restart failed because optional Terminal probes delayed registration; the
three-repeat test above is after separating those probes. A single OSD surface
lost its mapping on hot-unplug; the per-output implementation replaces it.
These failed runs remain in the evidence directory and are not counted as passes.

Several harness corrections are recorded separately: shell IPC is `summon`,
not `open`; native 4.5 DND has an extra Alt modifier; theme reload can restore
the VM's preferred mode, so capture geometry must be settled before measuring;
row clicks must wait for the first status sample. Captures always have unique
run IDs and timestamps, including repeats.

Hardware limit: real Linux input brightness-up/down events were injected into
both guests, but they have no backlight or DDC display. Actual brightness change
and its OSD need the verifier's hardware run. VM volume, explicit brightness
payload and the native panel route were verified. No hardware performance
budget or physical brightness result is inferred from these VMs.

## Evidence and cleanup

Raw evidence stays outside git under `~/.cache/wuling-build/wd1/`. Relevant
families: `notifications-matrix-r5-*`, `notifications-rest-r6b-*`,
`module-gate-r6-*`, `osd-matrix-r6-*`, `osd-input-r6-*`, `crash-watch-r6b-*`,
`edge-cases-r7-*`, `history-rest-r7b-*`, `geometry-final-r8c-*` and
`cleanup-final-r9-*`. Their JSONL command journals and immutable `shots/` give
the individual observations; later successful focused reruns resolve the
explicit earlier harness failures. No screenshot, raw JSON or log is committed.

The final 4.5 cleanup harness initially called native `notifications.clear`,
which that version does not expose. Removal and history deletion had already
passed; `cleanup-native-450-final.log` records the completed native-provider
check. No product change was needed for that harness error.

Live bar replacement/removal emitted native bar/widget duplicate-registration
and teardown warnings during transition. None named `notifications` or `osd`;
the official restart completed and final native receipt was verified. These
warnings remain in the raw logs rather than being described as a warning-free
session. The new notification/OSD steady-state runs did not report QML binding,
type or context errors. Short geometry captures include panel entry timing;
they establish placement, not a new full C visual acceptance pass.

`tools/check` passes all 52 tests, generation, metadata, syntax and staged
privacy checks. Added cases cover state bounds/redaction/permissions, missing
module refusal, clone ownership/restoration, edited entries, C-to-D upgrade
preservation and the selected audio device.

Both VMs were uninstalled and shut down normally (container exit 0). Only their
original snapshots and `d-clean-406` / `d-clean-450rc2` remain; the old C clean
snapshots were deleted. Containers `wuling-wd1-vm` and `wuling-wd1-vm450`, and
images `wuling-wd1-vm:runtime` / `runtime-r2`, were removed by name. Guest copies
of this round's checkout and captures were removed after final logs were saved
locally. No shared prune was used.

Disk at delivery: `wd1` about 63 MiB, retained `wc1` evidence about 61 MiB;
the two existing `wa1` VM directories remain about 11 GiB each. No new VM disk
or release tar was added. Raw evidence is retained pending review.

DESIGN suggestions: v415 already records the only required placement change.
The remaining physical-brightness and hardware-budget checks belong to the
verifier; this report makes no hardware pass claim.
