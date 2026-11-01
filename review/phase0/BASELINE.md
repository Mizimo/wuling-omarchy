# Phase 0: unmodified Omarchy baseline

**Status: INCOMPLETE / STOPPED (2026-11-01 UTC).** Cleanup and inventory are complete. No uninterrupted 15-minute baseline was obtained, and the popup exercise was not started. These partial observations must not set a WULING resource budget.

## Scope and conditions

Measured on **kujira**, using the existing desktop session, without installing software, changing configuration, restarting the shell, or rebooting. The two existing remote sessions are **external, recorded only**. Their workloads were not inspected or controlled. Therefore this is an undriven desktop observation on a running system, not an isolated whole-machine idle benchmark.

At the start, the session already had stay-awake enabled and the idle service disabled. The observer requires that original condition and an unlocked session throughout; it never changes the idle or lock configuration. The planned menu and calendar popup exercise was withheld when the idle observation failed its safety conditions. No keys, pointer events, audio playback, power operations, authentication attempts, or network changes are used.

## Inventory

| Component | Observed version or state |
|---|---|
| Omarchy / settings | 4.0.6-1 / 4.0.6-1 |
| Hyprland | 0.56.2-4 |
| Quickshell | 0.3.2.r7.g2b4501a-1 |
| Qt base / declarative | 6.12.0-3 / 6.12.0-2 |
| Mesa | 1:26.2.5-1 |
| Running kernel | 7.2.8-9-omarchy |
| CPU / memory | Intel Core i5-6300U, 4 logical CPUs; 7.50 GiB kernel-reported RAM |
| Graphics | Intel HD Graphics 520, i915 |
| Display | One internal display, 1366 × 768 at 60.111 Hz, scale 1; DPMS on, VRR off |
| Theme | Tokyo Night |
| Font availability | Noto CJK present; Geist, Barlow, and Material Symbols absent from `fc-list` |
| Audio | PipeWire 1.6.9, built-in analog stereo input/output; `pw-play` available; no playback performed |

The current `shell.json` is version 1, with an opaque top bar and the clock as center anchor. The configured screensaver/lock delays are 150/300 seconds, with the pre-existing stay-awake state overriding idle activation. The plugin override array is empty. The bar contains:

- Left: menu, workspaces.
- Center: indicators, clock, keyboard layout, weather, system update.
- Right: tray, agents, Bluetooth, network, audio, monitor, power.

Plugin discovery uses `omarchy plugin list` with the existing shell's session environment, including `OMARCHY_PATH`. There are 37 discovered plugins, 31 enabled, all first-party. The complete raw list and config remain in private evidence; enabled plugins and mounted bar widgets are distinct concepts.

Current-boot timing from `systemd-analyze`: firmware **4.846 s**, loader **6.335 s**, kernel **21.085 s**, userspace **4.662 s**, total **36.929 s**. `graphical.target` was reached at **4.657 s** in userspace. `blame` and `critical-chain` were captured for this boot. The critical chain includes 1.132 s in network initialization and 289 ms in power-profile service startup; service durations overlap and must not be summed. These are system boot timings, not measurements of the shell's first usable frame. No reboot was performed to obtain them.

## Intended measurement protocol and collector

The observer runs over SSH from stdin and writes JSONL only to the collecting machine. It reads the existing shell and compositor's `/proc` records, uses read-only lock/idle IPC checks, and checks shell-owned layer namespaces. No library is injected into either process.

- Idle: 91 samples on a 10-second monotonic schedule, covering 900 seconds and 90 CPU intervals. PID start times, boot identity, original stay-awake state, unlocked state, and absence of shell popups are checked. CPU includes the small cost of servicing observation IPC; it is not an observer-free estimate.
- PSS: `smaps_rollup:Pss`; USS: `Private_Clean + Private_Dirty + Private_Hugetlb`. Swap PSS is kept separate. KiB are converted to MiB using 1024.
- CPU: differences of process user + system ticks divided by elapsed monotonic time. **100% means one core**. Means are duration weighted; p95 uses linear interpolation across the 90 interval values.
- GPU: fdinfo records are deduplicated by DRM device + client ID within each process. This i915 driver exports **`drm-total-*` and `drm-resident-*`, not `drm-memory-*`**. Missing legacy fields are not reported as zero. Regions and accounting categories remain separate. Shared buffers can appear in both processes or multiple clients; do not add these values together or add them to CPU PSS as a unique physical-memory total.
- Popup exercise: native `shell summon omarchy.menu '{"menu":"root"}'` / `shell hide omarchy.menu`, then `omarchy.clock open` / `close`, ten cycles each. IPC methods are enumerated first. The corresponding nonzero shell-owned layer must appear after every open and disappear after every close. Memory is sampled after 3 seconds open and 5 seconds closed, with a further 30-second settled sample after each group. Opening the menu does not select an action; opening the calendar does not edit its settings.
- Excluded captures are kept separately: a short initial collector capture omitted the driver's `drm-total-*` fields. It was stopped and excluded. A subsequent 350-second capture stopped when an extra shell layer appeared. The following audit observed a display scale change from 2 to 1; the actor and transient popup were not identified. Both partial captures are excluded. A fresh inventory and second observation at scale 1 required unchanged shell layer geometry, but that observation was also interrupted by a real session lock. The verifier did not alter the display or restart the desktop.

## Stop evidence and partial results

1. The scale-2 observation recorded 36 samples spanning 350.007 seconds (06:42:02–06:47:52 UTC). The next observation encountered an additional shell layer and stopped. The following audit showed normal background/bar layers at scale 1. The transient layer and actor were not identified; the capture is not usable as a fixed-condition baseline.
2. After a fresh scale-1 inventory, 25 samples spanned 239.998 seconds (06:49:12–06:53:12 UTC). The next guard detected a real lock. The shell reports `locked=true`, `requested=true`, `sessionLocked=true`, `secure=true`, with the secure event at **06:53:22.679 UTC**. The idle service still reports stay-awake enabled and idle disabled.
3. `loginctl` concurrently reported `LockedHint=no`. That hint does **not** override the shell's actual secure lock state. The observer sent no lock, unlock, key, pointer, authentication, power, or settings command. The trigger is outside the observer's command sequence; its source has not been established.
4. The final read-only audit still found the session locked. The observer exited, its controller PID was absent, and the original shell/compositor start times were unchanged. Shell configuration, current theme files, and the four audited shell source files matched their earlier fingerprints. No popup was opened by this task and no owned UI required dismissal.

The following table describes **only the interrupted 240-second scale-1 observation**. It is included to preserve useful measurements, not as the requested idle baseline. Memory columns are medians; CPU is the duration-weighted mean, with 100% equal to one core.

| Process | PSS MiB (range) | USS MiB | Swap PSS MiB | CPU % | GPU total system0 MiB | GPU resident system0 MiB |
|---|---:|---:|---:|---:|---:|---:|
| omarchy-shell | 295.48 (295.42–299.21) | 282.88 | 0.00 | 0.346 | 121.15 | 120.89 |
| Hyprland | 84.34 (84.33–84.34) | 77.07 | 27.73 | 1.550 | 120.80 | 111.04 |

During that partial interval the shell had 93 file descriptors and 25 threads; Hyprland had 135–142 file descriptors and 16 threads. The driver's stolen-system0 counters were zero. GPU values are per-process DRM-client accounting, with the sharing limitations described above.

**Not measured:** a complete 900-second stable idle interval; the ten main-menu cycles; the ten calendar-panel cycles; open deltas; closed/settled return. The partial intervals are not concatenated. There is no pass claim, leak conclusion, or resource-cap recommendation.

## Required continuation

The design lead must coordinate the locked session and a stable measurement window before another run. This read-only round does not authorize an unlock workaround, credential use, display restoration, or changes to idle configuration. Once the session is available and the lead resumes the round, capture a fresh inventory and the full 15-minute interval, then perform and verify the two native popup sequences. Do not reuse these partial values as the baseline.


## Reproduction and evidence

`measure.py` contains the observer and the staged bounded popup exercise. Inventory and interrupted observer paths were exercised on the host; the popup branch has only been syntax checked and remains unexecuted. `summarize.py` aggregates complete local JSONL evidence and refuses incomplete captures or missing cycles. Its rejection of the current incomplete capture was verified; no complete-run summary was produced. Supply the two verified current process IDs explicitly; never reuse IDs from an old report. The script deliberately refuses to run unless the session already has stay-awake enabled and is unlocked. It does not establish those conditions.

For an authorized continuation, run `inventory`, then `idle`, then `exercise`, streaming each invocation over SSH and saving its stdout locally as `inventory.jsonl`, `idle.jsonl`, and `exercise.jsonl`. The raw inventory contains machine-specific information and must remain private. The collector creates no remote source file, runtime directory, background service, or armed marker. Its popup error handler closes only the popup it opened; it never unlocks or restarts anything.

Private evidence is under `~/.cache/wuling-build/w0/`; it is not committed. Public records include only this sanitized report and generic scripts. The final inventory reads the current state-directory theme name. Separate theme/source fingerprints support the post-run audit.
