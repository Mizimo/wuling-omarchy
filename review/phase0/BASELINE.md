# Phase 0: original Omarchy baseline

**Status: measurement complete under inbox v154.** The 900-second idle capture and both ten-cycle native popup exercises completed. Screenshot outcomes are listed separately below. This is a measured reference, not an approved WULING resource cap or a long-duration leak verdict.

## Conditions and inventory

The existing desktop on **kujira** was observed without installing software, changing configuration, rebooting, or restarting the shell. The two pre-existing remote sessions and their workloads were external, recorded only; their contents were not inspected or controlled. The desktop retained an existing visible application window. This is an undriven desktop observation on a running system, not an isolated whole-machine idle benchmark.

The design lead confirmed that the earlier scale change was made by the owner and the earlier lock was caused by closing the lid. Before this run, the owner unlocked the session and the design lead disabled the lid-close lock binding. The verifier confirmed the binding change, its backup, and empty compositor configuration errors. Restoration belongs to the design lead. Stay-awake remained enabled and idle activation disabled, as before; authentication configuration was not changed.

| Component | Observed state |
|---|---|
| Omarchy / settings | 4.0.6-1 / 4.0.6-1 |
| Hyprland | 0.56.2-4 |
| Quickshell | 0.3.2.r7.g2b4501a-1 |
| Qt base / declarative | 6.12.0-3 / 6.12.0-2 |
| Mesa / running kernel | 1:26.2.5-1 / 7.2.8-9-omarchy |
| CPU / RAM / GPU | Intel Core i5-6300U, 4 logical CPUs; 7.50 GiB kernel-reported RAM; Intel HD Graphics 520 / i915 |
| Display | One internal 1366 × 768 display at 60.111 Hz, scale 1, DPMS on, VRR off |
| Theme | Tokyo Night |
| Fonts in fontconfig | Noto CJK present; Geist, Barlow, Material Symbols absent |
| Audio | PipeWire 1.6.9; built-in analog stereo input/output; pw-play available; no playback performed |

`omarchy plugin list` was run with the shell session environment: 37 discovered plugins, all first-party, 31 enabled. The current `shell.json` has an opaque top bar, clock center anchor, an empty plugin override array, and configured screensaver/lock delays of 150/300 seconds overridden by the existing stay-awake state. Bar widgets: left menu/workspaces; center indicators/clock/keyboard layout/weather/system update; right tray/agents/Bluetooth/network/audio/monitor/power. Enabled plugins and mounted widgets are different sets.

The new inventory matches the earlier package, plugin, font, kernel, shell-config and theme inventory. Current-boot timing remains firmware 4.846 s + loader 6.335 s + kernel 21.085 s + userspace 4.662 s = **36.929 s**, with graphical.target reached at 4.657 s in userspace. Fresh blame and critical-chain outputs were retained privately. These are boot timings, not shell first-frame latency, and no reboot was used to obtain them.

## Idle: 900 seconds

Capture: **2026-11-01 13:03:29 UTC to 2026-11-01 13:18:29 UTC**, 91 samples on the 900-second schedule, 899.995 seconds between completed first/last samples, 90 CPU intervals. Observed wall-clock sample intervals were 9.990–10.010 seconds.

| Process | PSS median [min–max] MiB | USS median MiB | Swap PSS median MiB | CPU mean / p95 % | FDs [min–max] | Threads [min–max] |
|---|---:|---:|---:|---:|---:|---:|
| omarchy-shell | 304.46 [304.19–305.68] | 292.46 | 0.00 | 0.043 / 0.100 | 93–98 | 25–26 |
| Hyprland | 73.82 [73.82–73.82] | 67.20 | 27.73 | 0.136 / 0.200 | 134–140 | 16–16 |

| Process | GPU system0 total median [min–max] MiB | GPU system0 resident median [min–max] MiB | PSS last − first MiB |
|---|---:|---:|---:|
| omarchy-shell | 121.08 [121.08–130.47] | 113.60 [113.60–122.99] | -0.98 |
| Hyprland | 120.80 [116.73–121.11] | 111.03 [106.96–111.34] | +0.00 |

This driver exports `drm-total-*` and `drm-resident-*`, not `drm-memory-*`. Missing legacy fields are not zero. The stolen-system0 counters remained zero. DRM records are deduplicated by device/client within each process, but shared buffers can be charged to multiple clients or processes. Do not sum the GPU columns across processes or add them to PSS as unique physical memory.

## Native popup exercise

Ten main-menu cycles and ten clock/calendar-panel cycles completed. Every native IPC open was followed by a nonzero matching shell-owned layer, and every close by its disappearance. No key or pointer events were sent. The open point is sampled after 3 seconds; the closed point after 5 seconds; a further settled point follows 30 seconds after each group.

“First” means the first measured open in this run, not a cold process start. Values below are differences from the immediately preceding closed point for first/warm opens. Warm values are medians of cycles 2–10. The final column is measured against the start of that entire ten-cycle group.

| Surface / process | First open Δ PSS MiB | Warm open Δ PSS MiB | Warm closed Δ PSS MiB | After group +30 s Δ PSS / USS MiB |
|---|---:|---:|---:|---:|
| menu / shell | +7.56 | +6.31 | -0.41 | -3.29 / -3.31 |
| menu / compositor | +0.00 | +0.00 | +0.00 | -0.00 / +0.00 |
| clock / shell | +8.19 | +6.28 | -0.49 | -2.50 / -2.50 |
| clock / compositor | +0.00 | +0.00 | +0.00 | +0.00 / +0.00 |

| Surface / process | First open Δ GPU total / resident MiB | Warm open Δ GPU total / resident MiB | After group +30 s Δ GPU total / resident MiB |
|---|---:|---:|---:|
| menu / shell | +23.75 / +23.75 | +12.66 / +12.66 | +0.07 / +0.07 |
| menu / compositor | +16.03 / +16.03 | +11.96 / +11.95 | +4.07 / +4.07 |
| clock / shell | +23.25 / +23.26 | +12.38 / +12.38 | -0.39 / -0.38 |
| clock / compositor | +7.95 / +7.95 | +14.03 / +14.03 | -4.07 / -4.07 |

### Closed shell PSS by cycle

| Cycle | Menu: closed PSS MiB | Clock: closed PSS MiB |
|---|---:|---:|
| 1 | 306.22 | 303.74 |
| 2 | 303.46 | 302.06 |
| 3 | 303.04 | 301.56 |
| 4 | 303.72 | 301.43 |
| 5 | 302.76 | 300.55 |
| 6 | 303.12 | 298.95 |
| 7 | 303.56 | 300.21 |
| 8 | 302.99 | 300.13 |
| 9 | 302.03 | 299.09 |
| 10 | 301.60 | 300.21 |

In this run, warmed shell PSS rose by about 6.3 MiB while either surface was open and returned below its immediately preceding closed point at the median five-second closed sample. After each group settled, shell PSS was 3.29 MiB and 2.50 MiB below its respective group starting point. The closed samples do not show steadily accumulating retained PSS. Hyprland’s settled GPU allocation was 4.07 MiB higher after the menu group, then 4.07 MiB lower after the clock group; the final value matched its pre-menu value. These observations describe this short sequence and do not establish allocation ownership, long-term leak freedom, or a memory cap.

## Reference screenshots

**0 captured; all 15 requested reference views skipped under the v154 privacy rule.** Before measurement and again after the popup exercise, the privacy gate found one pre-existing visible application window. Its title and contents were not retained or inspected. The window was not moved, hidden, or covered to obtain a capture. No grim call, image file, reference OSD, notification, notification-history popup, or search typing was performed.

The skipped set is: desktop/top bar; menu root, Setup, System, menu search; audio, network, Bluetooth, power, clock and agents panels; volume OSD; neutral notification; notification history; and keyboard-shortcut overview. Each entry and its reason is recorded privately in `w0/ref/index.json`. Reference images remain outstanding; a later screenshot-only continuation needs a desktop without visible owner windows or personal data. No lock screen or authorization window was captured.

## Method, audit and limits

- The observer streams from stdin over SSH; evidence is written only to the collecting machine. No injection, settings change, remote helper installation, service, runtime directory, or armed marker is used.
- PSS comes from smaps_rollup; USS is Private_Clean + Private_Dirty + Private_Hugetlb. Swap PSS is separate. KiB → MiB uses 1024.
- CPU is process user + system tick change divided by monotonic elapsed time; 100% means one core. Means are duration weighted and p95 uses linear interpolation. Servicing the read-only observation IPC is included in measured CPU.
- PID start times, boot identity, unlocked state, existing stay-awake state and shell layer geometry were guarded. Environment variables for compositor IPC came from the active runtime instance.
- Menu IPC was shell summon omarchy.menu with the root route, then shell hide omarchy.menu. Calendar IPC was omarchy.clock open / close. Methods were enumerated first; no action inside either surface was selected.
- Final audit: unlocked; original process identities retained; no test popup; observer processes gone; shell config, theme files, relevant shell sources and the lead-owned lid binding fingerprint unchanged.
- Earlier incomplete captures remain separate and are excluded. The initial collector omission of drm-total fields was corrected before this accepted run. No values were stitched across interruption, lock, or scale changes.
- This is one long-lived session and one run, with external workloads retained. Prior cache residency and Swap PSS affect comparisons. Ten cycles and 30-second settling do not establish long-term leak freedom or a resource cap. Future incremental comparisons should match display scale, theme, session age, warmup and observation protocol.

`measure.py` provides inventory, idle and exercise modes; `summarize.py` rejects incomplete captures and missing transitions. Both the complete path and the earlier incomplete-capture rejection have been exercised. Supply verified current process IDs rather than reusing historical IDs. Raw inventory and screenshots are private, under `~/.cache/wuling-build/w0/`; accepted measurements are specifically in `kujira/v154/`. Only this sanitized report and generic scripts are committed.
