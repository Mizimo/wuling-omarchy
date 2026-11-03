# F: completed 24-hour soak and final native update

Inbox **v174**. The uninterrupted `e603ad3` run meets the measured WULING
shell/writer soak criteria: full duration, stable process identity, near-zero
shell CPU, bounded memory/resources and a continuously healthy sampled writer.
One separate observation remains unattributed: compositor CPU stayed around
2.72% of one core for roughly 7.66 hours, then returned to its earlier range.
This report does not certify whole-desktop idle CPU or identify its source.
No new product defect is established by that observation.

After preserving and auditing the original run, kujira was updated once to
shared main **`58056acb3ce34b0c8befb9971190a7887cea8e52`**. Installer and doctor
passed. The expected post-soak shell/writer replacement is separate from the
unchanged identities during the measured 24 hours. No test was restarted to
clear a failure.

## Duration, method and coverage

- Observer: **2026-11-02 18:36:55 UTC through 2026-11-03 18:36:55 UTC**,
  final `complete`, **86,400.064741 s**. Controller: complete,
  **86,402.088823 s**, no failure, successful retirement.
- **8,641** contiguous samples, indices 0–8640. Wall-clock intervals
  **9.902977–10.097373 s**, mean **10.000000 s**; no missing sample or
  unexplained sampling gap. Observer stderr is empty. Shell and compositor
  PID/start-tick identities and boot stayed unchanged. No observed process
  loss/crash; no claim about unrelated processes.
- **96** Terminal open/close and named synthetic critical-notification
  exercises; **24** hourly bundles of Dispatch open/close, Power open/cancel,
  OSD show/retire, Arrival preview and Exit preview. No real session action
  or keyboard input. All 384 boundary observations and 48 completed previews
  are present. DND kept notifications out of toasts; final history was cleared.
- Active groups include their 30-second settling period, totaling
  **4,220.574 s**. Every 10-second CPU interval intersecting an active group
  is excluded, along with sample zero. **8,136** eligible intervals cover
  **81,360.001 s**. “Controller-inactive” describes these rows; it does not
  mean all other clients or external workloads were idle.
- The external observer is the unchanged supplied `research/phase-f/soak.py`;
  the verifier independently drove IPC, checked actual surface state, marked
  activity, collected boundary data, and audited the result. No library was
  loaded into the shell. Raw collection hashes were checked against the
  completed remote files before deleting source copies.
- Run `01` is a separate **77.57-second incomplete harness run**: its Dispatch
  check incorrectly used the bar's active list for an overlay. Its evidence is
  retained. It contributes **zero** samples to this verdict; no stitching.

Conditions remain those recorded for the native F upgrade: Omarchy 4.0.6,
Qt 6.12, Intel HD 520, one 1366 × 768 internal output at scale 1, theme
`wuling`, `zh-Hant`, all WULING plugins enabled but sounds **off**, DND on.
The owner window and two external remote workloads were preserved and not
controlled or inspected. No native logout, reboot, lock, suspend or credential
operation occurred. Kaede was not accessed.

## Memory, CPU and resource interpretation

PSS alone is insufficient here: late swap-out reduces resident PSS. Both PSS
and **PSS + Swap PSS** were examined, along with all hourly and settled-cycle
values. DRM counters are separate and nonadditive; they must not be summed
with PSS or across processes as unique physical memory.

| Controller-inactive metric | Shell | Compositor |
|---|---:|---:|
| Mean PSS, MiB | 286.03 | 40.43 |
| PSS range, MiB | 249.66–335.13 | 35.26–41.12 |
| Weighted CPU, % of one core | 0.0523 | 0.9699 |
| FD median [range] | 144 [144–149] | 138 [134–143] |
| Thread median [range] | 25 [25–26] | 16 [16–16] |
| Mapping median [range] | 1717 [1641–1769] | 946 [944–950] |
| H7–H24 PSS slope, MiB/h | −1.1366 | −0.1509 |
| H7–H24 PSS + Swap slope, MiB/h | −0.0325 | −0.0621 |
| H7–H24 settled PSS + Swap slope, MiB/h | −0.1436 | −0.0613 |

Slopes are descriptive ordinary least-squares fits, not leak proofs. Shell
memory has rises and falls through the run; the hourly PSS + Swap means and
all settled cycles do not show sustained growth. The final Swap PSS is
22.46 MiB, so the lower final PSS is not used alone to award a pass.
The final matched PSS + Swap mean is 18.34 MiB above the early window, still
within the warmed range and below the original short baseline's 304.46 MiB
resident PSS. Different warmup, theme/plugins, swap and uncontrolled external
workloads prevent treating that older baseline as a matched A/B result.
Per v171, small differences alone are not findings.

At group +30 s, shell FDs are 144–145 and threads 25–26, both ending at
144/25. Mapping counts warm from the initial 1643 to an oscillating range:
settled maxima by six-hour block are **1764, 1761, 1771, 1770**. The settled
median shifts upward later (1725, 1726, 1758.5, 1765), while low points recur
and the upper range stays bounded; this is not a constant mapping count,
nor evidence of one retained allocation per cycle. Settled PSS + Swap means
by the same blocks are **277.72, 299.13, 297.93, 299.41 MiB**. Compositor FDs,
threads, mappings and PSS + Swap similarly remain bounded.

Shell DRM system0 total allocation is 75.56–102.30 MiB across eligible rows;
its hourly means settle around 79 MiB after the first hour. Compositor DRM
total is 116.73–121.31 MiB. Resident DRM varies with memory pressure; no
inference about unique GPU allocation ownership is made.

### Matched 15-minute windows

The same phase of the 15-minute schedule is compared: elapsed 900–1800 s
and 85500–86400 s, each containing an ordinary Terminal/notification cycle.
These are **900-second wall windows with activity removed**, each leaving
84 full intervals, approximately **840 s**. Continuous 900-second idle
segments do not exist in this workload schedule.

| Window / process | Mean PSS, MiB | Mean PSS + Swap, MiB | Weighted CPU, % |
|---|---:|---:|---:|
| Early / shell | 265.29 | 265.29 | 0.04762 |
| Final / shell | 261.18 | 283.63 | 0.04881 |
| Early / compositor | 40.89 | 100.82 | 0.11786 |
| Final / compositor | 35.67 | 99.99 | 0.15119 |

The first/last hourly-bundle windows were also retained (cycles 4 and 92,
830 eligible seconds each); shell CPU is 0.05783/0.04940%, with PSS + Swap
265.00/302.01 MiB. They are not substituted for the final ordinary window.

### Compositor CPU observation — cause not established

Eligible samples from elapsed **15.508–23.167 hours** form one elevated
segment: **2,595 samples**, mean **2.7237%** of one core. H17–H23 means are
2.706–2.766%; the final ordinary window is back at 0.1512%. Shell CPU stays
near zero throughout (hourly means 0.042–0.063%). The elevation persists
outside marked test activity, so excluding only the IPC groups cannot turn
it into an idle pass. Existing client/background work was not quiesced; no
client-specific activity trace was collected. The cause cannot be assigned
to WULING, a client, or the platform from these data. No owner process was
inspected or stopped to manufacture an attribution, and no extra soak was
run. This limitation is carried explicitly to the design lead.

Full hourly summaries are in [soak-hourly.csv](soak-hourly.csv); all
before/open+3/close+5/group+30 rows are in [soak-cycles.csv](soak-cycles.csv).
[soak-summary.json](soak-summary.json) contains numeric summaries and limits.

## Writer events and retirement

**10,466 health observations** (8,641 regular + 1,440 controller heartbeats +
384 boundaries + final retirement) all show the same running, ready writer.
There are **zero** PID transitions, recorded exits, never-started/given-up
states, recovery attempts, retries, or pending/in-flight observations during
the run. The 384 writer process snapshots also retain one PID/start identity,
FD count 3, thread count 1 and 201–202 mappings. Writer PSS is bounded at
11.66–14.75 MiB, with Swap PSS up to 2.73 MiB.

The observer's writer journal event set is empty. A separate final filtered
query over the entire run is also empty; a positive retention check retrieves
the initial pre-run writer-start event from the same shell, establishing that
the journal is readable and covers the start. No absence claim relies solely
on missing crash text. Health samples cannot prove every instant of pending
state; no sampled pending state or uncleared final snapshot occurred, and the
journal covers child start/exit events between the 10-second health samples.
The historical writer disappearance was not reproduced; its cause remains
unproven. No recovery was induced on the native desktop.

Before update, controller and observer were gone, the armed marker was absent,
history/toasts were zero, Terminal/Dispatch/Power and both previews had retired,
and the writer remained healthy. The local completion watcher was also gone.
Only the persistent notification writer remained among owned shell children;
there was no status watcher or session worker. Normal once-per-session Arrival
and login-music markers and an empty `exit.lock` were retained as product
state, not confused with an armed test or active Exit lease.

## Authorized update and final state

The exact update target was the latest **shared local main** at the time of
installation. The checkout has no configured Git remote, and the private
remote query was unavailable; independent remote freshness is not claimed.
Compared with e603ad3, the only runtime code change is the HUD header Hazard's
`ground: header.color`; other changes are documentation/assets/review. No
new 24-hour claim is made for that post-soak commit.

One normal `install --yes` update completed, with no additional restart or
reinstall. All **328 installed payload files** match the target archive.
`wuling doctor --json` returned success. The shell and writer changed once
as expected for the official restart after the soak; compositor, compositor
start identity and boot are unchanged. Final checks establish:

- unlocked, workspace 1, original owner window address/workspace/mapped state;
- sounds off, sound plugin enabled, no voices/music or `pw-play`;
- DND on, zero history and toasts, no active test surface or preview;
- healthy ready writer, no pending/in-flight snapshot;
- byte-identical overrides, shell configuration and full bindings, including
  the design lead's no-lock-on-lid-close block; language/theme/background,
  text size, display settings, volume and brightness unchanged;
- no surviving owned controller/observer/armed marker or completion watcher.

The lead's lid block remains for the lead to restore. No native boot test or
visual resume claim is added. VM report `1573921` was already delivered and
accepted: F-1 is an accepted 4.0.6 native-bar limitation, and visual resume
remains unverified. Neither was rerun.

## Evidence and disk

Private root: `~/.cache/wuling-build/wf1/verifier-v173/`.

- `kujira/soak-final-v174/`: raw `soak-v173-02/` samples/activity/start/result,
  observer stderr, controller log, as-run controller/helper/observer,
  collection hashes, remote hash match, analysis and pre-upgrade audit.
- `kujira/post-soak-before-update-v174.json` and
  `kujira/final-upgrade-v174/`: original final snapshot, target/archive hashes,
  installer log, all installed file hashes, before/after checks and final audit.
- `soak-method/`, `analyze-soak-v174.py`, `journal-audit-v174.py`,
  `cleanup-summary-final-v174.json`, completion event and prior VM delivery
  receipt; separate incomplete `kujira/run01/` retained.

Accepted local source copy removed: **38.30 MiB**. After collection, the old
remote source and temporary update source were removed: **77.36 MiB** total.
Private round evidence is **555.29 MiB** at the final size audit; remote raw
run evidence is **22.68 MiB**. All raw recordings and captures remain private.
Owned F containers and runtime image are absent. Both VMs remain normally
shut down at their retained baseline plus sole clean checkpoint; no VM was
started for this completion audit. No public raw log, address, account,
notification content, credential or canon image is included.

Validation: `tools/check` passed on the update target, including all **84**
runtime tests, generation, metadata, syntax and staged privacy checks.
The public CSV counts and writer states were independently checked against
the retained raw rows; all committed additions received a manual privacy review.
