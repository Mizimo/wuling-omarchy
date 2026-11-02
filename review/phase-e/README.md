# Phase E / E.1 independent verification

Inbox v167–v171. E functional candidate: `1f0b4e4caf050f325d49ca3dab7c61113ac25736`.
Writer recovery and visual corrections: `ff501b407cd65d6cd81251796fb04b7890157cf2`.
The original E matrix was retained when E.1 arrived. Both supported Omarchy
versions were exercised independently. Unrelated subsequent implementation
changes in the shared working tree were never installed.

## Finding for adjudication

### P2 candidate — killing the confirmed Exit worker before dispatch loses the action

Both versions reproduce the same narrow fault. Replace native System actions
with an owned, append-only action counter in a disposable VM. Open Power,
select Logout and complete the real hold. Once the active Exit lease exists,
identify the process holding `exit.lock` by its inode in `/proc/locks`, verify
its `wuling session arm` command, and SIGKILL that process before the counter
advances. The confirmed action count stays unchanged. The overlay eventually
returns to idle and the OSD becomes usable; the action is never retried.

The action deadline is a thread in that same worker (`session.py`,
`ActionDeadline`), so terminating the worker also destroys the independent
visual-failure fallback. This is an injected process-death fault, not a
spontaneous crash report. It differs from killing the idle prearmed child:
that earlier fault is detected by Power and successfully falls back to one
action. Killing the worker after the counter advances also preserves exactly
one action. Shell restart after confirmation and a missing Exit visual each
still execute one action.

For the pre-dispatch kill, the first observed idle after an active sample was
10.54 s (4.0.6) / 10.72 s (4.5) later, about 0.15 / 0.18 s after the published
lease expiry. This observation includes polling and the fade; the specified
normal give-back deadline is measured from action dispatch, which does not
occur in this fault. It is not a separate claim that normal action give-back
exceeds its specification. The fault probe did not independently count its
failure notification, so no absence-of-toast finding is asserted.

Repair/adjudication boundary: decide whether loss of the entire confirmed
worker is covered by the action guarantee. If covered, an independently owned
confirmed-action delivery mechanism must survive that worker, with an atomic
single-consumer token so recovery cannot execute the native action twice.
The animation timer alone cannot provide that guarantee.

Evidence: `vm{406,450}/guest/evidence/exit-fault-kill-before.json` and
`exit-fault-kill-before-host.json`; compare `exit-kill-prearmed.json`,
`exit-fault-kill-after-host.json`, `exit-fault-restart-host.json` and
`guest/evidence/exit-missing-overlay.json`. The private controller is
`guest-fault-watch.py`.

## Bounded limitation — application-directory churn

Publishing 5,000 synthetic desktop entries while Dispatch is closed produced
long whole-shell IPC silence on both versions. Atomic directory publication
on 4.5 did not avoid it. The fixture includes malformed entries and a 65,536
character Name. On 4.5, after removing the fixture files, an official shell
restart remained blocked; the precisely identified stalled VM shell was
terminated and the official restart recovered. This was confined to owned
VMs. No equivalent load or process termination was performed on kujira.

A fresh native 4.0.6 control without WULING accepted the same eleven hostile
fixtures plus 5,000 atomically published entries: all observed shell pings
succeeded through 60 s (0.257–0.384 s after publication). It did not reproduce
the stall. This narrows the observation but does not establish WULING-only
causation: session warmup, theme and earlier exercise differ. The next useful
comparison is the same warmed interaction sequence with and without WULING. Stable 5,000-entry observations on 4.0.6 did accept
and retain the complete real query, returning the unique result in
4.03 / 4.02 / 4.58 s from Super+D through typed query to ready result. Those
figures include approximately 1.65 s of keyboard pacing and SSH observation.
Intermediate old result counts were queued-input processing, not lost text.
A 1,000-entry observation took approximately 0.48 s to open and 3.02 s through
typing and query completion. These are bounded observations, not a responsiveness
pass for index churn.

Evidence: `vm406/dispatch-stable-observe-progress.json`,
`dispatch-stable-observe-r2-progress.json`, `dispatch-flood-progress.json`,
`app-churn-*`; `vm450/dispatch-stable-observe-r2.log`,
`guest/evidence/app-bulk-stall.json`, `app-bulk-shell-stop.json`;
`vm406/native-index-baseline/progress.json` for the native control.

## Passed E paths

- Both versions: eight short Enter presses do nothing; simultaneous Enter and
  pointer hold commits once; cancelling a mixed hold does not commit; restarting
  before confirmation commits nothing; restarting after confirmation commits
  once; concurrent Exit rejects the second request; missing visual still acts;
  preview acts zero times and allows OSD. Recovery permits a second operation.
- Power routes: Super+Esc, power key, bar cell, native System menu, and the three
  dangerous Terminal footer entries all open and cancel without action. On both
  owned VMs, native lock rejects Power open/toggle; one correct unlock restores
  the desktop. No lock or real power action was attempted on kujira.
- Dispatch: literal hostile Name/Exec arguments, terminal desktop field-code
  expansion, GUI launch, malformed/embedded/unknown field codes, empty Exec,
  invalid encoding, hidden/TryExec-missing/oversized files, long names, RUN size
  limit, exponent precedence, right associativity, floating-point formatting,
  modulo, non-finite/division-by-zero/semicolon/depth rejection. ASK was tested
  only with no configured agent; no external prompt was sent.
- Actual clipboard paste reached an owned foot receiver exactly; a sensitive
  native clipboard entry did not enter native history, and neither synthetic
  marker appeared in WULING configuration/state/cache files. No owner window
  received pasted text.
- Removing a compositor-created second output while Dispatch owned it moved
  the overlay to the remaining output, retained the query and accepted actual
  calculator input. This was virtual output removal, not physical cable testing.
- C collector sections change while Terminal stays open, and closing it retires
  its watcher. Disabled/missing native panels return structured errors. DND
  takeover preserves native On, then own Off survives native/own handoffs while
  native storage hashes remain unchanged. Clock, shortened Agent labels and
  bounded long labels were visually checked; positive short-viewport captures
  show the scroll fade at the appropriate end.

The 4.0.6 Dispatch functional runner initially reached the flood stage before
serializing its earlier assertions; that record is explicitly labelled
recovered assertions, not individual retained timing. The corrected 4.5 runner
retains each result. Escape first clears a nonempty Dispatch query; tools now
wait for actual closure instead of treating one Escape as unconditional close.

## Real Exit → Plymouth / SDDM

On the 4.0.6 VM, official `omarchy plymouth set-by-theme wuling` exited zero.
The UKI, boot configuration and selected assets changed as expected. Native
actions were restored before real logout, reboot and shutdown. Full 60 fps
external captures and extracted frames remain private for review.

| Comparison at 1280 × 800 | Observation |
|---|---|
| Exit vs actual Plymouth | Same visible mark bounds: x 470–809, y 233–526 |
| Exit vs SDDM | Same image; SDDM y 189–482, exactly 44 px higher |
| Raw Exit vs raw SDDM ground | Both RGB (14, 18, 17) |
| Video Exit vs Plymouth ground | Both RGB (13, 18, 16); encoding accounts for the raw/video difference |
| Plymouth and SDDM asset bytes | Identical SHA-256 |
| Corrected reboot / shutdown capture cadence | Maximum frame timestamp gap 17 ms; no gap over 50 ms |

Reboot includes the native display-output-inactive interval, firmware screen,
Limine menu, blank mode transitions, Plymouth and SDDM. Those intermediate
screens were not removed or attributed to WULING. Shutdown reaches actual guest
ACPI poweroff. The observer then holds the powered-off emulator for three
seconds solely to finalize recording; that retained final image is not a
product hang.

An initial observer configuration exposed a QEMU serial device. The installed
EFI stub automatically appended serial/tty console arguments despite the UKI
and Limine configuration lacking them, which prevented the expected graphical
boot evidence. Only the owned QEMU configuration was corrected (`-serial none`);
no product or Omarchy files were changed to hide console output. Reboot and
shutdown were then repeated on the same installed disk. Initial recordings
remain as observer diagnostics, not the accepted Plymouth result.

Evidence: `vm406/video/real-logout.mkv`, `real-reboot-no-serial.mkv`,
`real-shutdown-no-serial.mkv`, their frame directories/contact sheets;
`logout-mark-comparison.json`, `real-reboot-mark-comparison.json`,
`exit-raw-color-comparison.json`, `capture-timing-no-serial.json` and
`plymouth-{before,after,changed}.json`.

## E.1 writer and visual corrections

The original child-kill/send/dismiss/restart sequence passes on both versions:
zero persisted live entries, two history rows, a replacement writer, and no
resurrected dismissed notification after restart. A SIGSTOPed writer with an
unacknowledged update does not block shell teardown. Real child termination
uses exactly three recovery attempts, then a failed doctor result and one
low-priority transient warning. A nonexistent executable reaches `given-up`
with `ever_started: false` and `exit_code: null`. Repeating exhaustion after a
shell restart in the same compositor session does not repeat the warning.

Negative and malformed ACKs enter recovery with the newest state pending.
A delayed ACK cannot clear a newer snapshot: two intervening notifications and
a dismissal coalesce to zero live entries and two history rows, and a restart
does not resurrect them. Faults altered only the external writer command in
an owned VM, with original bytes, DND and clean doctor verified on restoration.
No in-process QML instrumentation was used.

| Omarchy | Recovery delays (s) | Stopped-writer shell restart (s) | Restored doctor |
|---|---|---:|---|
| 4.0.6 | 1.17 / 5.08 / 30.05 | 1.75 | PASS |
| 4.5.0-rc2 | 1.14 / 5.17 / 30.09 | 2.87 | PASS |

Final durable records: `vm{406,450}/e1/guest/evidence/writer-progress.json`,
`complete.json`, `doctor-restored.json`, and full host `e1-run-host.log`.


The ten-minute recovery-budget reset was not independently waited out in real
time. The native historical spontaneous writer disappearance remains
unexplained; injected termination is not evidence of its cause. Future F soak
monitoring is separate work.

Agent launch button, Hazard strips, selected dangerous-card subtitle and
RUN/ASK rows without query underlines were visually inspected. A real right
click on Night with its native panel disabled shows the new error line above
the Terminal footer; the panel was reenabled. These visual negative fixtures
were confined to VMs.

## Kujira update and retained resource observations

Kujira was updated directly from D.1 to ff501b4. Doctor passes; the installed
writer command and pinned product hashes match. Language, overrides,
background, the unowned binding prefix including the lid rule, and existing
owner-window metadata were preserved. The native shell configuration changed
only by the three expected independent E plugin registrations; the owned key
block added Super+D.

Real hardware checks pass: the Wi-Fi label matches the active connection's
SSID; the private frame shows Tailnet Connected, Night Off, the large clock
and real shortened Agent labels. Night's actual right click opens the native
Display panel without changing Night. A narrowly matched system-bus observer
saw **zero RequestScan method calls** throughout the behavior exercise; this
checks client requests, not autonomous radio activity. Network and Bluetooth
controller state were unchanged. The observer was stopped and verified gone.

All seven Power routes opened and cancelled. Actual Dispatch keyboard input
launched the uniquely named owned foot fixture; its window, desktop entry and
own frecency change were removed. Exit used preview only. The first still
caught the early wave, so a second bounded preview retained the later mark
frames. No real logout, reboot, shutdown, suspend, lock or PAM operation was
performed on kujira. Real boot and login remain **unverified on hardware**.

Every capture passed the empty-workspace, empty-activewindow, no-special-
workspace and no-real-notification gates before and after capture. Native
Night coordinates were reviewed against the private frame before right click.
The Terminal hardware frame contains the allowed local USER and SSID; it stays
private. Final audit: workspace 1, original owner address/workspace/mapped
unchanged, same boot, unlocked, no test overlay/foot/armed marker, healthy
writer with no pending or in-flight state, DND on, and clean doctor. Other
remote owner sessions were external and untouched. Kaede was not accessed.

The previously authorized 900 s idle, 300 s open and 20-cycle controller had
already completed when v171's cancellation was read. These existing data are
retained as context; no further strict memory gate or small-delta attribution
was performed. Idle shell plus writer was about 281 MiB PSS with 0.053% shell
CPU and no measured writer CPU. With Terminal open the three persistent
processes were about 311 MiB total; shell and status collector each used about
0.88% CPU. All 184 samples had one healthy, unchanged writer. Closed shell FDs
stayed at 137 and threads at 25; the 20 closed samples do not establish steady
growth. This short observation is not the future 24-hour F soak.

Evidence: `kujira/{upgrade-exit,doctor-after-upgrade,final-audit,doctor-final}.json`,
`evidence/{functional,preview-followup,capture-index}.json`,
`evidence/shots/terminal-hardware-e1.png` (private SSID), later
`exit-preview-v171-*.png`, and `evidence/budget/{samples.jsonl,summary.json}`.

## Method, evidence and cleanup

Private root: `~/.cache/wuling-build/we1/verifier-v167/`. Screenshots, videos,
SSID, account labels, credentials and raw native inventory are intentionally
excluded from this commit. The review contains no owner application contents.

E's `tools/check` passed 74 tests; E.1 passed 77 plus generation, metadata,
syntax and staged privacy checks. Test helpers are external processes. Real
credentials were used only once per visually verified own-VM login/unlock;
failed harness readiness gates sent no password. All native power operations
remain open/cancel or preview only.

Harness corrections are retained, not counted as product failures: waiting for
IPC registration after a restart; extending the host E.1 deadline beyond its
two recovery budgets; fixing the post-checkpoint evidence collector so a
missing old E directory cannot skip E.1 evidence. The first 4.0.6 E.1 pass lost
its guest export when that collection error was followed by checkpoint restore.
Its host assertion log was retained; a fresh complete E.1 pass was collected
before retiring the VM. The initial 4.5 host timeout left an armed marker after
byte restoration; a bounded delayed-ACK/restart continuation verified cleanup.
That continuation replaced its aggregate progress file, so a fresh complete
4.5 pass was also retained before final acceptance. The collector now appends
progress across continuations and the host log includes each complete result.

Both owned VM containers and the named runtime image were removed. The image's
reported size was 1.25 GiB; this is not a claim about reclaimed shared
layers. VM disk allocation is 10.12 / 10.31 GiB, each retaining its baseline
and only `verified-clean-b`. Private evidence and pinned check worktrees occupy
169.3 MiB after final native collection. Accepted D source copies had
already been removed (73.6 MiB). Reproducible source copies remain until this
report is accepted; raw captures are retained. The owned remote staging/evidence directory uses 41.1 MiB. Final native
restoration and owned-observer cleanup are recorded with the native result.
