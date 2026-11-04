# G verification: Codex partial results and handoff

Target: `ef45c12c224cf84a8ff4e95074b3dd16fb7c9c6b`. Tests were run by
the Codex verifier under inbox v175; work stops for the v177/v178 handoff.
This is a partial report, **not final G acceptance**. The receiving verifier
must independently review the original evidence before incorporating it into
the final report. No product code was changed. Neither kujira nor kaede was
accessed in this round.

All private evidence paths below are relative to
`~/.cache/wuling-build/wg1/verifier-v175/`. Raw captures, fixtures, credentials
and machine metadata are intentionally outside the repository.

## Findings for review

### G-V2 / P2: cold Night launch leaves the action queue waiting

On 4.0.6, with the native night-light daemon absent, click Night in Terminal.
The light turns on, but a second click does not turn it off during an observed
eight-second interval. The first WULING action is still waiting, blocking
subsequent queued actions. The daemon inherited the stdout/stderr pipes
captured by the command wrapper, although its launcher had already exited.

Independent controls on both VM versions:

| Observation | 4.0.6 | 4.5 rc2 |
| --- | ---: | ---: |
| Native cold launch with detached output returns | 0.514 s | 0.464 s |
| Warm WULING toggle | exit 0 | exit 0 |
| Cold WULING toggle after 5 seconds | still running | still running |
| Exit after stopping only the inherited-pipe daemon | 0.127 s, exit 0 | 0.135 s, exit 0 |

The wrapper's 120-second timeout is a source observation; the experiment
did not wait that entire duration. Actual cold pointer interaction was tested
on 4.0.6; the causal command/pipe control was repeated on rc2. Subsequent
unrelated tests used a warm native daemon at its Off temperature. This is a
fixture condition, not a repair, and no claim is made that G introduced the bug.

Candidate repair: detach the native daemon launcher's output instead of
capturing inherited pipes, while preserving checked results for bounded
commands. This has not been patched or validated.

Evidence: both `vm*/night-cold-control.json`,
`vm406/night-cold-hang-processes.json`, and the tile-switch records. Source:
the Night action in `bin/lib/wuling/actions.py` and the captured-output
command wrapper in `bin/lib/wuling/__init__.py`.

### G-V1 / P3: English Comms displays the literal translation key

The count contains `count-unit` in the overview and full Comms page on both
versions. Traditional and Simplified Chinese display the intended unit.
The English translation is legitimately empty; `Runtime.tr` uses truthiness
fallback and eventually returns the key. A presence check is a repair
candidate. No patch was applied.

Evidence: English Comms in both final visual manifests below, plus the
overview captures. Source: `kit/Runtime.qml` and
`plugins/terminal/i18n/en.json` at the pinned target.

### G-V3 / P3: Comms can scroll into an empty body after its last record

Confirmed in controlled 4.0.6 observations. At 640×480, visit Config, then
full Comms, scroll to the bottom and wait one second. The body is empty while
all 11 history records remain. The empty range varies with the preceding
page: after Tailnet, one upward wheel step exposes the last line and six
expose the final records; after Config, six still leave an empty body.
System, close/reopen and native text-size 16 at 800×600 also reproduce it.
This is not evidence of lost notification records.

`DetailFrame.qml` has an inactive Loader inside the content Column without
visibility tied to its active state. Retained geometry is consistent with
these observations, but that mechanism is a source inference, not an
instrumented or patched proof. Removing inactive layout contribution is a
candidate to test. Rc2 standard captures show extra empty space, but its
controlled narrow-viewport probe was **not run**.

Evidence: `vm406/comms-scroll-probe-1793813697992210208.json` and all 13
associated captures, inspected visually.

## Completed behavior

The following independent scenarios completed on **both** VM versions,
apart from the findings above:

- All ten detail pages through 28 pointer/keyboard entry routes, Backspace
  return and Esc close. The rc2 VM uses 12 virtual CPUs and visibly exercises
  the two-column Performance grid; 4.0.6 uses eight.
- Virtual NetworkManager/hwsim/hostapd secured and open Wi-Fi: wrong then
  correct passphrase, saved reconnect, disconnect, active/inactive forget,
  radio off/on, pointer/key hold and release cancellation. Opening the page
  does not request a scan; explicit S does. No real network was modified.
- BlueZ/btvirt discovery and stop-on-leave, pairing, connection with 76%
  fixture battery, disconnect/reconnect, forget, and soft-rfkill Off tile
  with in-page recovery. Synthetic peer trust was removed before the
  disconnect observation to avoid immediate native auto-reconnect.
- Fake Tailnet start/guarded stop, failure and false-success retention of
  old state, login handover, missing executable, and direct-route Wi-Fi badge
  versus relay. Wi-Fi/Bluetooth/Tailnet/Power tiles navigate; DND and warm
  Night toggle and restore.
- Unique MPRIS timing and transport controls, unknown timing for duplicate
  indistinguishable players, no-player state, PipeWire peak fallback and
  optional cava at nice 19 with retirement.
- Comms bodies, expansion, pointer/keyboard More, actual synthetic action
  execution and stale-action rejection after clearing fixture history.
- Weighted battery percentage, native power profiles, process sorting and
  native btop/fastfetch, system clipboard projection, leap February and Today.
  Private audio output selection/level/mute and playback stream level/mute.
- Config native writes observed, denied write preserves old hash/value,
  sections and clock-off header access, missing/non-audio/FIFO music rejected,
  valid music path without preview, clearing and subsequently missing music.
  Seven real native settings handovers. Git, release-metadata archive and
  metadata-free archive installations produce the expected version fields.

Additional **4.0.6-only completed** scenarios: private audio input
selection/level/mute with fixture capture streams accounted for; four Config
language choices and native showHistory; every page collector retires when
leaving, and no WULING watcher/cava remains while closed; external motion
timing; complete 200-cycle resource run.

Credential scans found no passphrase matches:

| Complete network run | Root process scans | Maximum gap | File reads | Journal bytes | Observed nmcli PIDs |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4.0.6 | 4,174 | 63 ms | 88,672 | 194,974 | 9 |
| 4.5 rc2 | 3,358 | 71 ms | 75,696 | 53,273 | 7 |

Coverage includes readable argv/environments, the journal interval, WULING
config/state/share/cache, installed themes/plugins and Quickshell cache.
Sampling cannot exclude processes shorter than a sampling gap; source review
also checks stdin delivery. Private audit files are
`vm406/wifi-actions-1793809341425042336-credential-audit.json` and
`vm450/wifi-actions-1793814987132846432-credential-audit.json`.

## Visual and resource evidence

4.0.6: `vm406/visual-1793811414535428932.json` records 208 final captures,
all visually inspected: four themes, three languages, ten pages plus bottom
views, and separate narrow, 4K, fractional-scale and text-size-16 groups.
Twenty additional bottom captures and the corrected Audio margin-scroll
supplement were inspected. G-V3 is the noted exception.

Rc2: `vm450/visual-1793815562437502719.json` contains **156**, all inspected:
the twelve theme/language groups at verified 1366×768. This is not completion
of the requested resolution matrix. The remaining four layout groups and
the later batch stages were not executed.

4.0.6 motion: `animations-channel-1793813816418211851`, 6,993 externally
recorded frames, median gap 16.667 ms and maximum 33.421 ms. For all ten
pages under Field/full, HUD/full and PAPER/reduced, first-row content is
visually readable in the last captured frame at or before 320 ms. Timing
starts before the request on an established SSH channel, including helper
latency (median 38.67 ms, maximum 52.39 ms). System open/back strips were
also inspected. The earlier connection-setup film is excluded from timing.

4.0.6 resource source: `vm406/cycles-1793813430372214553.jsonl`; numerical
summary is [resources-406.json](resources-406.json). It contains one complete
200-cycle run over 265.911 s with unchanged shell identity, maximum sample
gap 2.105 s, and no closed collector descendants. PSS+SwapPSS medians are
585.959 MiB before and 598.002 MiB after. Ten-cycle medians warm to about
598 MiB and then plateau; last-50 slope is −0.00431 MiB/cycle. FD stays
141–145, threads settle at 20 after the first cycle, and mapping counts
remain bounded. Idle CPU changes from 0.048% to 0.097% of one core; active
cycles use about 29%. This short run does not establish long-term behavior.
There is **no rc2 resource result** and no cross-version memory comparison.

Both guests use Hyprland 0.56.2-4, Quickshell 0.3.2.r7.g2b4501a-1,
Qt 6.12.0-3 and Python 3.14.8-1; Omarchy packages are 4.0.6-1 and
4.5.0rc2-1. Rendering is virgl backed by llvmpipe. Guests have 8 GiB RAM;
containers have eight-CPU/12-GiB limits. Physical QEMU audio is disabled and
all playback uses private null sinks. No instrumentation is loaded into Qt.

## Interruptions, cleanup and remaining work

Harness events are retained, not counted as product passes or crashes:

- An early Comms focus/count error invoked Sleep in the owned 4.0.6 VM.
  Virtual S3 recovery did not restore a responsive display. Restart/reboot
  attempts were preserved, then only that VM was cold resumed from its
  current disk. This preceded the resource run; no run was stitched across it.
- Theme changes reset resolution in the first matrix attempt. The corrected
  harness reapplies and asserts the actual output mode for each capture.
  A later controller exit 143 interrupted one group; completed groups were
  retained, the partial group repeated, and provenance saved.
- Initial audio-input accounting counted the fixture's own remap streams;
  the baseline was corrected. A narrow Audio wheel hit a volume control;
  a margin-scroll supplement establishes bottom reachability without it.
- Rc2 BLE discovery failed in the native control too. Scheduling the
  external fixture's advertisement-renewal callback restored native
  discovery; synthetic device cache was cleared before UI retest.
- At the v178 stop boundary, the rc2 matrix logged an IPC non-response while
  leaving the completed standard groups. The next cleanup controller could
  close/check the original shell and proceed. Preserve
  `vm450/visual-final-visual-matrix.log`, `handoff-runtime-v178.txt` and
  `visual-final-batch.json`; cause is unestablished. No later batch stage ran.

Both installations were uninstalled and inventories compared. Removed only
verifier-created cava and override directories, absent before installation.
Remaining differences are native Chromium/ibus activity: 213 paths on
4.0.6 and 211 Chromium paths on rc2. These were preserved in
`vm*/post-test-artifact-cleanup-diff.json`, not erased to manufacture equality.
An orphaned owned player on rc2 was stopped after checking its exact command.
Final rc2 shell ping succeeded, lock was false, and no owned fixture/WULING
process remained in the final check.

Both guests were powered off normally, named containers removed, and
`verified-clean-b` plus original firmware restored; image checks passed.
The 4.0.6 container's exit 127 was a post-QEMU shell-script artifact caused
by editing its running launcher; its log records the truncated command.
Rc2 container exit is 0. Never edit a running VM's launcher.

The owned runtime image (reported size 1.34 GB; shared-layer reclaim is not
asserted) was removed by exact name. Retained evidence/tools/source occupy
about 1.1 GiB; each baseline/checkpoint directory occupies about 11 GiB.
No unrelated containers or images were pruned.

Remaining rc2 work: narrow/4K/fractional/text-size-16 matrix and bottom
reachability, language/showHistory, audio inputs, motion timing, all-page
collector retirement, a fresh uninterrupted 200-cycle run, and controlled
G-V3 reproduction. Then complete the final report using independently
reviewed evidence. Kujira work belongs to the receiving verifier under the
latest inbox. No new testing was started after the handoff decision.

Private `HANDOFF-v178.md` documents rebuilding the removed runtime, starting
from the clean disk, fixture setup, safe input gates, immutable evidence and
cleanup. The old `report-draft.md` is superseded by this partial report.
Pinned-target `tools/check` passed; report privacy and whitespace were checked
separately without testing or staging another contributor's in-progress work.
