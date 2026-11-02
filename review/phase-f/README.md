# F independent verification

Inbox v173; product `e603ad371c54fd3150d89377aebd8cd183884a59`.
This is the VM report. Kujira's separate 86,400-second run is still in
progress; this report does not award a soak pass. Later main commits are
outside the pinned test target.

## P2 — native bar precedes Arrival ink on 4.0.6

All four externally recorded cold-cache 4.0.6 logins show a dark top strip
and a brief central indicator before Arrival's opaque ink. This violates the
BRIEF F first-frame gate. It occurs with both MIST and PAPER, in ordinary
logout/login and in full cold boot. No wallpaper-before-ink frame was observed.
The two corresponding 4.5.0-rc2 recordings did not show an early bar or
wallpaper. These are bounded captures, not a guarantee about every login.

Reproduction: install the pinned release on the clean 4.0.6 VM; select
`wuling` or `wuling-paper`; log out; clear the owned user's Mesa/Qt shader
caches; record the emulator externally before entering the correct fixture
password once; inspect every captured change between SDDM and the first
opaque Arrival frame. Do not use an ink classifier as the verdict.

The full-boot layer observations identify a 26 px `omarchy-bar` before
`wuling-session-arrival`; the 30 px `wuling-bar` appears afterward. Native bar
creation leads Arrival by 0.847 / 0.799 s (MIST / PAPER), and its first observed
fully opaque state leads Arrival's by 0.915 / 0.874 s. The visible strip,
dimensions and layer ordering support attribution to the native startup bar.
They do not establish which startup-order change is the correct repair. An
earlier hypothesis about WULING Host's initial hold state is superseded by
these observations. No product patch or in-process instrumentation was used.

Private evidence root for this report: `~/.cache/wuling-build/wf1/verifier-v173/`.
See `vm406/first-frame-attribution.json`, `first-layer-times.json`,
`first-opaque-layer-times.json`, full-boot `*-layers.jsonl`, and the recordings
below. Each movie's sibling directory contains full-resolution before/first
ink frames, every distinct captured pre-ink frame, timestamped contact sheets,
timeline overviews, statistics and a manual-review record.

| Version / route | Movie basename under `vmVERSION/video/` | First ink PTS | Maximum capture gap |
|---|---|---:|---:|
| 4.0.6 MIST login | `cold-406-wuling-1793644835002010138.mkv` | 7.233 s | 34 ms |
| 4.0.6 PAPER login | `cold-406-wuling-paper-1793644930696666415.mkv` | 7.100 s | 17 ms |
| 4.0.6 MIST full boot | `full-boot-mist-r2-1793645897251130157.mkv` | 99.683 s | 34 ms |
| 4.0.6 PAPER full boot | `full-boot-paper-1793646050427579588.mkv` | 65.667 s | 17 ms |
| 4.5.0-rc2 MIST login | `cold-450-wuling-1793647272058704984.mkv` | 7.600 s | 33 ms |
| 4.5.0-rc2 PAPER login | `cold-450-wuling-paper-1793647322589048679.mkv` | 7.583 s | 50 ms |

## Full cold boot recordings for the final review

The two full-boot movies above start with the emulator paused before firmware
execution and continue through cold power-on, actual LUKS unlock, SDDM,
Arrival and desktop. Official `omarchy plymouth set-by-theme` succeeded for
each palette; UKI and Limine configuration hashes changed. Every distinct
pre-ink captured frame was inspected by eye, including dim transitions.

The baseline has an **unencrypted root**. A private 64 MiB LUKS2 data-volume
fixture, ordered before Plymouth quit and SDDM, supplies the real cryptsetup
password challenge. Each accepted run used one correct QMP password and
verified the mapper before login. This proves the displayed unlock route,
not encrypted-root boot. The fixture was detached, disabled and deleted.
No lock, login or reboot was performed on kujira.

Recordings are lossless RGB at a requested 60 fps, retaining original PTS and
scheduling gaps. Full-boot duration includes pauses for visual inspection of
the password and greeter surfaces; it is not boot latency. The movies and
frames stay private for the design lead to select; none is committed or
uploaded through HAPI.

## Passed supported-version paths

Both independent VMs began at their own clean checkpoint: Omarchy 4.0.6-1
and 4.5.0rc2-1. They used KVM/virgl and an llvmpipe host renderer, 1280 × 800
for the recorded login route. These are not physical GPU measurements. Real keyboard and
pointer tests used QMP after checking the intended focus surface. Test audio
used an owned null sink; the emulator also had no physical audio backend.

| Check | Independent observation |
|---|---|
| Session gate | Fresh real logins play; first install and first enable on an older compositor mark without playback. Restart, theme switch, pinned-release update and correct unlock do not replay. |
| Input | Key and click skip; three held-key controls per version establish actual key receipt in an owned terminal before Arrival and do not skip at one second. Native Super+Space still opens its menu. |
| Lock cancellation | A real own-VM lock request during Arrival removes it; one correct unlock returns without replay. |
| Layout | en, zh-Hans, zh-Hant, reduced motion, two virtual outputs, removal of the focused primary output and hot-add. Contact sheets were inspected; no missing final heading or clipping was found. Physical cable behavior is not established. |
| Retirement | Full previews inactive by 3477 / 3420 ms on 4.0.6 and 3373 / 3401 ms on rc2, from reported first swap. Reduced: 1027 / 953 ms. Visual/controller/watchdog retire; these are observation upper bounds, including polling. |
| Sound | Essential/full/off, mute, DND, four voices with overflow dropped, repeated-cue throttling and disabling with active children. Captured PCM gain is 0.600000024 on both, RMS residual about 1.35e-9. |
| Login music | Empty by default. Private synthetic PCM plays once on a fresh login into the verified null sink; repeat request is `seen`; shell restart and preview do not replay. Fixture and configuration reference removed. |
| Independent parts | Each of the eight parts disabled and reenabled separately. Other enabled flags survive; native bar, notifications, OSD and System fallback were seen. Disabled custom bindings do not open their removed UI. |
| 300 normal entries | Atomic publication of 300 ordinary desktop entries with Dispatch closed and open leaves shell pings responsive. Maximum observed ping: 79 / 67 ms on 4.0.6, 174 / 161 ms on rc2. Entries removed afterward. |

The 300-entry result addresses v172's daily-use follow-up; it does not erase
the previously accepted 5,000-entry limitation. E's excluded Exit-worker
SIGKILL case was not repeated.

Evidence: `vm{406,450}/guest/evidence/` for sound, entry and layout records;
`held-input-host.log`, `lifecycle-*.json`, `no-replay-observers.json`,
`update-observer-summary.json`, `partial-*.json`, `layout-contact.png`,
`partial-contact.png`, lock/unlock and music records. Actual native fallback
screens are retained, not inferred solely from a successful IPC return.

## Resume remains visually unverified

On 4.0.6, real S3 suspend reached QMP `suspended` and woke once. Shell IPC then
reported no Arrival replay and the same first-swap value, but Hyprland blocked
in `drm_atomic_helper_swap_state`; output stayed inactive and capture/control
timed out. Restarting the own-VM display manager also left its native greeter
blocked in DRM. No password was sent to an unseen surface. Normal shutdown
then stalled; a documented emulator reset recovered the owned working disk.

A separate s2idle attempt did not wake through its RTC, Shift or ACPI power
button and also required a reset. These are retained VM failures, not a
visual-resume pass or an established WULING defect. There is no clean-native
resume control establishing causation. The unstable sleep route was not
repeated on the second VM. Final ordinary shutdown is checked separately.
Evidence: `vm406/resume-*`, `gpu-reset-recovery.json` and `s2idle-*`.

## Update, removal and cleanup

Official `omarchy update -y` completed successfully from 4.5.0rc2-1 to
4.5.0rc3-1. Overrides hashes and the entire shell configuration were identical,
including deliberate sound-plugin disablement. Doctor passed, explicitly
reported `tested: false`, and matched notification contents to the rc2
contract. This is a userspace compatibility observation, not a new support
promise; the newly installed kernel was not booted before cleanup.

Interactive installation on rc3 named the untested version, both tested
versions and possible native-notification fallback. Declining cancelled;
accepting completed. Overrides and independent disablement were unchanged.

Appending a harmless comment to the VM's native notification `Markup.js`
changed its hash while retaining valid JavaScript. On reload, doctor failed
with that module named, WULING notifications disabled themselves and native
notifications became the provider. A real synthetic native toast and a
working WULING Terminal were captured separately and visually checked. Exact
module bytes were restored, WULING notifications reenabled and doctor passed.
The first fault attempt's restart returned nonzero and the harness restored
immediately; its output was not retained. Two later attempts returned zero
and established fallback. The first transient's cause is unproven and is not
silently converted into a successful restart.

Evidence: `vm450/official-update-1793647812287901861-*`,
`official-update-summary.json`, `untested-consent-1793647960686505668-*`,
`consent-after.txt`, `module-fault-1793648053516325944-*` and
`module-fault-1793648125537252952-*`. The first fault's restoration and nearby
journal are also retained.

Complete removal restores the original native theme, menu, bar and visible
notification toast on both VMs. Owned release, command, plugins, fonts, skills,
private state and the new Arrival layer rule are absent. User overrides are
retained intentionally. The 4.0.6 inventory differs only in those overrides and
two native ibus runtime files. On rc3 there are also a native herdr log and a
different dconf database hash. A separate read-only boot of the clean checkpoint
confirmed the original database hash and **identical values for every dconf
key**; the difference is database representation, not retained theme settings.
That audit needed no graphical login and was followed by normal shutdown.

Private audio defaults were restored; only owned null-sink modules, music and
PipeWire drop-in were removed. The persistent module's JSON omitted its numeric
index, so cleanup initially stopped before uninstall; the corrected helper
obtained the owned module ID from `pactl list short modules`. Nothing unrelated
was unloaded. Module fault backups and the boot unlock fixture are absent.

Both VMs finished with normal guest poweroff. Both containers and the named
runtime image were removed; its reported size was 1.25 GiB, not a claim about
reclaimed shared layers. Each disk retains its baseline plus only
`verified-clean-b`, with the working disk restored: allocation 10.12 / 10.31 GiB.
Private evidence and pinned source occupy about 570 MiB. Accepted E source
copies were removed earlier in the round (74.8 MiB). Reproducible F source stays
until acceptance; raw recordings are retained. The native soak controller and
its completion watcher remain active independently of these VM containers.

Evidence: `vm{406,450}/uninstall-*-{diff,result,owned-check}.*`, native UI shots,
`vm450/dconf-semantic-audit.json`, final normal-shutdown/clean-restore records
and `cleanup-summary.json`.

## Kujira soak in progress

The authorized update ff501b4 → e603ad3 passed doctor. Sounds were prearmed
off before installation, reasserted afterward, and remain off with the sound
plugin enabled and no `pw-play`. Language, overrides apart from that explicit
sound choice, background, owner-window metadata, lid rule and unowned bindings
were preserved. Empty-workspace privacy gates passed before and after both
Arrival/Exit preview captures; workspace 1 was restored.

`soak-v173-02` began at epoch 1793644615.513740 with unchanged shell/compositor
identities and an already healthy writer. The supplied observer records every
10 s; a separate IPC-only driver marks 96 light-use groups and 24 hourly
bundles, including boundary measurements. It never sends keys, restarts the
shell or completes a Power action. Natural writer failures are preserved.
End-of-run cleanup clears synthetic history and keeps DND on and sounds off.

The earlier `soak-v173-01` stopped after 77.57 s because the harness checked
Dispatch through a state list that excludes overlays. Its owned overlay was
closed; writer and desktop were unchanged. The corrected run uses actual
component state and namespace checks. Run 01 is retained separately and will
never be joined to run 02. Final completion, full-series growth/CPU/handle
analysis and every writer transition are deferred to the separate soak report.

## Evidence integrity

No product changes were made. Initial cold-login IPC polling on 4.0.6 used an
invalid GNU timeout duration, so those polls provide no lifetime evidence;
their external movies remain valid. Later observers use a valid duration.
The first unanchored held-key probe was inconclusive; positive controls above
record key receipt before the overlay. An initial sound helper used an absent
method; it was corrected to the installed API. The first full-boot fixture
lost its password forwarder before input and is not an accepted unlock run.
The initial 4.0.6 music parser failed on adjacent JSON values; the original
recording established the correct null-sink stream after parser correction.
The 4.0.6 update observer's initial active samples belong to the already-running
fresh-login animation, with first swap preceding the update request; no new
playback occurred. Original failed attempts and corrections remain private.

Raw logs, account labels, native inventories, canon, credentials, music and
captures are excluded from git. Kaede and other remote owner sessions were
untouched. The report claims only the versions and paths actually exercised.

`tools/check` passed on the pinned product with this review staged: 84 tests,
generation, metadata, syntax and staged privacy checks.
