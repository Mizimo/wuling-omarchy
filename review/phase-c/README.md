# Phase C independent verification

Inbox v163, 2026-11-02. Both independent VMs tested `5cc562f8e4cc27db9e65ec071fecb40df9077bdf`; kujira received the permitted fresh C.1 install `e99afecf64c472265cc03568fa662b992ca4a7ec`. The C.1 layout-only change did not restart the completed VM matrix. Later implementation commits and the shared working tree are outside this pinned acceptance. The [three B fixes](../phase-b/RETEST.md) pass on both versions.

**Disposition:** no severe VM blocker; the three B fixes pass. The idle budget is met and the second cycle group does not continue the first increase. C is not an unconditional hardware/visual acceptance: the findings and explicit native test gaps below remain.

## Findings

### P3: successful JSON can mean no panel opened

On either supported version, disable the Terminal plugin, then invoke `wuling terminal open`. It exits zero with schema 1 and `ok: true`, while no panel exists. Direct native `shell summon` returns `unknown` with exit zero; `actions.terminal` discards this result. The analogous `wuling action panel power` case in a battery-less VM also returns success for an unavailable native panel: `actions.run` only rejects `unhandled`.

A caller cannot distinguish completion from unavailable UI. Check native response values in the command bridge and return the documented structured failure. Keep version-specific positive/negative controls; exit status alone is insufficient. Evidence: `vm{406,450}/c-disabled-control.json`, `c-failure-results.json`; the power case is recorded with the independent pointer validation. On kujira, the Tailscale tile is present and reports the running service, but right-click leaves Terminal active; no `omarchy.tailscale` IPC target is mounted. The Wi-Fi/BT/profile states were not changed. This is the same missing-panel boundary exposed in real hardware, not proof that the underlying service is unavailable. No product edit was made.

### P3: changing visible sections does not update the running collector

Open Terminal with all sections; set `terminal.sections` to `clock` while it remains open. The UI reduces to clock-only, but the same `status --watch` process retains all original section arguments. Closing retires the helper; reopening starts clock-only; empty sections launch no helper. Both versions behave alike.

`Process.command` changes while `Process.running` remains true. A fix needs to restart the collector on an effective section change while retaining zero closed-panel collection. This is excess open-panel work, not an observed idle leak. Evidence: `vm{406,450}/c-lifecycle.txt`, `c-live-sections-clock.json` and corresponding private captures. Twelve rapid open/close cycles per VM leave no watcher.

### Integration limit: one-click Terminal-to-calendar handoff

With Terminal open, one click on the native clock closes Terminal; a second opens the calendar. The same sequence under Omarchy's original bar reproduces it on both versions, with a successful closed-state click control. Native `PluginBarApi` scopes third-party click targets and `KeyboardPanel` handles the overlay input mask. This is a native integration boundary rather than a newly introduced WULING bar regression. Tab/Shift+Tab handoff and Escape work. Do not bypass the boundary by exposing arbitrary native QObjects. Evidence: `c-input-result.json`, `c-native-handoff.json`, `c-clock-handoff-confirmed.json` on both VMs.

## VM acceptance

Own exported bases and clean checkpoints, one VM at a time, 8 vCPU/8 GiB, nice 15 and idle I/O. Guest versions: Omarchy 4.0.6 and 4.5.0-rc2. QEMU 11.1.3, virgl with host llvmpipe; these are interaction and layout results, not physical GPU or battery claims. Input uses QMP key/button/wheel events, with state and private compositor captures. The separate native pointer tool uses the public virtual-pointer protocol outside the shell process; its no-connection negative control sends no input, and left/right/drag positive controls passed in the VM.

Both versions passed:

- Real Terminal shortcut; native clock right-click format persistence; Tab/Shift+Tab/Escape; one active panel; moved-anchor reopening and native empty-bar double-click transparency.
- Width boundaries 1280/1279 and 1024/1023; fractional scale 1.25; all four edges including native vertical clock; two compositor outputs with focused-output routing, removal of the owning output and reopening on the remaining output.
- Shell-hidden dismissal; independent Terminal disable leaving the native clock usable; missing bar host fallback with Terminal still working. The host file was restored byte for byte and doctor passed.
- Four palettes in zh-Hant (effective canonical zh-TW); comparison with DESIGN and mockups; 20 px body scrolling with fixed header/footer; Exit/Reboot/Off only open the native System menu. No power action was selected.

Private evidence: `wb1/verifier-v162/vm{406,450}/c-*.json`, `c-lifecycle.txt`, `shots/c-*`. The second output is compositor-created headless. Selected captures were inspected for the four palettes/edges, width boundaries, scale, output routing, fallback and scrolling; not every raw frame is claimed as a manual visual review.

## Font observation

Each VM completed five fresh logins plus just-installed and official-shell-restart cases. Each series changed the native text size to 16 and captured at 0.2/0.5/1/2/3/5 seconds after the open command returned, with unique immutable names: **42 frames per VM, 84 total**. Cold cases span Field, HUD and HUD Paper. Every non-0.2-second frame has clock/header OCR; each series' 0.5-second frame and selected early/late frames were manually inspected. No sustained selective missing glyph was reproduced. Some 0.2-second frames precede or overlap panel entry; that is not evidence of missing glyphs.

Maximum capture invocation lateness was 3.78 ms on 4.0.6 and 4.23 ms on 4.5. These are invocation times relative to CLI return, not measured physical presentation times. Raw files and timing/OCR data: `vm{406,450}/font-series/` and `font-ocr.json`. Earlier overwritten implementer evidence was not used.

On kujira, official shell restart, text size 16, six observations and restoration completed without logout. Exact original font-config bytes/modes and dconf scaling were restored; the bar returned to its original size. All six native captures were skipped because an existing owner window remained. IPC state cannot establish whether glyphs rendered: the native visual result is **unverified**, not pass. Evidence: `kujira/font-after-shell-restart/`.

## Native installation and hardware

C.1 fresh installation, `wuling config set language zh-Hant`, and doctor passed. The original bindings prefix matches its preinstall hash after subtracting only the owned appended block; the lead-owned lid rule remains. Theme is Wuling. Existing external remote sessions were recorded only; their workloads were not inspected or controlled. No native logout, lock, authentication attempt, suspend, reboot, display-mode change, package update, or radio/network/profile change was used.

| Item | Observed result and limit |
|---|---|
| Two batteries | sysfs and UPower enumerate BAT0 and BAT1; native power widget loaded/visible and right-click opens its single panel. BAT0 reports 95%; BAT1 is present but has zero current/full energy in UPower and no sysfs capacity/full fields. Do not invent a useful second-battery percentage or claim a visual two-row check without a capture. |
| Wi-Fi / Bluetooth | Availability and current enabled state read successfully. No toggles. Their native panels automatically enable scanning/discovery, so right-click opening was skipped under the read-only radio rule. |
| Tailscale | Real running state is exposed; right-click fails to open a matching panel (finding above). No network/tailnet change. |
| Night | Missing native temperature initially hides the tile. After an owned native service was started, real pointer clicks switch 4000 → 6500 → 4000; right-click opens the native monitor panel. The sole owned process was retired and the original absent-service state restored. |
| Power | Real profile state read; right-click opens native power with exactly one panel; no profile action selected. |
| Brightness | Actual slider drag changes raw 68 → 545 (1% → 8%), volume remains unchanged. Original raw 68 restored through the existing monitor brightness IPC. OSD rendering is unverified. |
| Brightness keys | Skipped: the keyboard-focus gate did not establish focus. No virtual keyboard events were sent on the native desktop. Pointer-only continuation is a separate group with owned-layer/topology checks. |
| Tray application | Independent synthetic SNI registers, appears in the native drawer, is identified by its exact tooltip, receives an actual Activate callback after a pointer click, and retires. Native tray width returns after cleanup. No icon from another application was clicked. |
| Agent | Two real usage display rows available, with agent collection disabled. No credentials or agent sessions inspected, no collector or agent launched; visual rendering remains unverified. |

Evidence: `kujira/hardware-readonly-final.json`, `hardware-events-pointer-r3.jsonl`, `hardware-pointer-controller-r3.txt`, `hardware-pointer-r3-restored.json`, `tray-controller-r2.txt`, `tray-events-r2.jsonl`. All raw evidence is private. The unavailable Tailscale route and the explicitly skipped inputs keep the full hardware matrix from an unconditional pass.

## Resource measurement

The phase-0 method was retained: smaps_rollup PSS/USS, process ticks over monotonic time (100% = one core), and per-process DRM clients deduplicated by device/client. Settings, boot/process identities, unlocked state and layer geometry were guarded. Stay-awake remained as it was. This is the existing desktop with external workloads retained, not an isolated machine benchmark.

| State / process | PSS median [min–max] MiB | CPU weighted mean / p95 % | FD range | Thread range |
|---|---:|---:|---:|---:|
| Idle 900 s / shell | 267.96 [267.47–274.53] | 0.057 / 0.200 | 105–111 | 25–31 |
| Idle 900 s / compositor | 41.50 [41.49–41.50] | 0.127 / 0.200 | 134–138 | 16–16 |
| Terminal open 300 s / shell | 280.58 [279.84–282.75] | 0.847 / 1.000 | 110–110 | 30–30 |
| Terminal open 300 s / compositor | 39.79 [39.78–39.79] | 0.260 / 0.400 | 138–144 | 16–16 |

There are 91 idle samples/90 CPU intervals and 31 open samples/30 intervals at ten-second spacing. Against the accepted 304.46 MiB shell baseline, the measured idle median difference is **−36.50 MiB**, within the +40 MiB limit; average shell CPU is below 0.2%. Baseline and this run differ in session/process age and cache/swap residency, so the negative difference is not a causal claim of memory savings. Shell swap PSS is zero; compositor median swap PSS is 59.94 MiB versus the baseline's 27.73 MiB. Read-only observation IPC is included in CPU.

The persistent status helper was sampled for 100 seconds within the continuous-open capture: median PSS 15.19 MiB, mean CPU 0.80%, 3 FDs and 6 threads. This is separate from the shell numbers. Short-lived child commands are excluded; the figures are not a complete process-tree cost or a unique-physical-memory total. No helper runs while closed at the final audit.

| Terminal exercise | Shell PSS before → after 30 s MiB | Δ PSS / USS MiB | Closed PSS range MiB | Closed FD / thread range |
|---|---:|---:|---:|---:|
| First 20 cycles | 266.27 → 270.31 | +4.04 / +3.77 | 268.58–272.23 | 105–105 / 25–25 |
| Second 20 cycles | 267.21 → 266.72 | −0.49 / −0.83 | 265.50–268.41 | 106–106 / 25–25 |

Every cycle verifies a shell-owned nonzero open layer and its disappearance; open sampling follows 3 seconds, closed sampling 5 seconds, then each group settles 30 seconds. The first group's increase is retained rather than called zero. After the intervening native hardware checks, a second identical 20-cycle group did not repeat it. No sustained accumulation was established over these short sequences; the one-time difference in closed FD count is across hardware work, not a per-cycle rise. This is not long-duration leak proof. Compositor settled PSS changed by 0.00/−0.003 MiB in the two groups. DRM buffers are reported separately in private summaries; shared allocations must not be added to PSS or summed across processes as unique memory.

Evidence: `kujira/{idle,open,exercise,exercise-r2}.jsonl`, exit records, `resource-summary.json`, `exercise-r2-summary.json`, `open-helper.jsonl`, `helper-summary.json`. Incomplete attempts are never stitched together. The summarizer rejects incomplete captures; an early aggregation attempt encountered the still-empty open file and was excluded.

## Boot assets

After resource measurement, the explicitly authorized official `omarchy plymouth set-by-theme wuling` completed once with exit zero in about 17 seconds. No retry was needed. Before/after `/boot` inventories record types, permissions, sizes and SHA-256 with stability checks. Only the active UKI and `limine.conf` changed content; no boot file was removed. The build log confirms successful initcpio and unified image generation, installation and configuration update. It also retains possible-missing-firmware warnings for `xhci_pci_renesas` and `qat_6xxx`; no manual repair was attempted.

The installed Plymouth logo matches the pinned C.1 unlock asset byte for byte, and the default Plymouth theme is `omarchy`. The original boot identity is unchanged. **No reboot or real boot-visual claim.** Evidence: `kujira/boot-before-plymouth.json`, `boot-after-plymouth-1.json`, `plymouth-attempt-1.txt`, `plymouth-result.json`, `boot-assets-and-final-doctor.txt`.

## Privacy, recovery and cleanup

One pre-existing owner client remained at the capture gates. It was not moved, hidden or closed. No native screenshot was taken, including the eight requested owner views (four themes, empty desktop and Terminal); C.1's real-hardware visual comparison therefore remains outstanding. No owner screenshot or canon is included here or sent through HAPI. Known clock digit spacing is intentionally excluded under v163.

Harness corrections are not product findings: separated QMP pulses fixed an ineffective initial click/double-click; native theme switches reset the VM's dynamic mode, so later palette/footer controls assert geometry; the initial overflow wheel hit volume and does not prove scrolling (the later `c-body-scroll-*` sequence does); native focus-dispatch syntax was corrected; canonical locale is zh-TW and shell ping returns `ok`. VM volume and temporary fonts/settings were restored.

Native Night startup initially inherited a subprocess output pipe, causing a controller timeout. The sole newly created process was identified by PID/start/executable/cgroup, terminated, and absence restored. A corrected controller then stopped before input because its keyboard-focus predicate did not establish focus; its finally path restored Night, brightness and overrides. The keyboard group was not resumed on that evidence. A separate pointer-only group completed the available tile routes and brightness drag, then the harness incorrectly expected JSON from OSD state. Its direct SSH brightness cleanup was denied; the official script also returned success without restoring the device in that SSH context. Independent recovery used the already installed monitor brightness IPC from the native shell and verified exact raw 68, original override bytes and absence of the owned Night process. No root workaround was used. This is a controller/SSH-context defect, not a failed WULING slider. All attempts retain separate logs. The first tray fixture assumed icon targets were in the host's button registry; installed Tray.qml shows they are separate drawer items, so that attempt produced no click and its owned process retired.

VM C cleanup restored font files/overrides and removed WULING. Remaining C inventory changes are native cold-login log/ibus churn and dconf serialization; 4.0.6 also retains the native CLI's shell-config mode change from 644 to 600 with identical content. On 4.5 the native transparency schema migration was identified semantically and restored. This is not a zero-diff claim for C; the B final inventories are exactly equal. Both guests were normally powered off and both own containers removed. The immutable bases and sole `verified-clean-b` checkpoint remain.

Final native audit: unlocked, same boot and expected shell, Wuling/zh-Hant, original font size 12, exact original binding prefix/lid rule, raw brightness 68, original volume, no owned Night process, no status helper, no test popup/armed marker, and native tray width restored. Installed bar and Terminal source hashes match C.1, and doctor passes. The owner client is still present, so the screenshot gate remains closed. WULING stays installed as requested.

Only the verifier's native cache/source/fixtures (37.35 MB) were removed after every retained evidence file matched its archived hash. Its installed product is self-contained. Both own VM containers and the unused runtime image were removed by exact name (image logical size 1.43 GB); the failed-build download cache removed was 83.68 MB. Retained own VM bases/work disks allocate 23.15 GB total (21.56 GiB), each with only the immutable baseline and latest clean checkpoint. Current-round private evidence and pinned check/source trees occupy about 0.32 GB, retained pending report acceptance; no shared pruning or implementer storage was touched.

`tools/check` passed for both pinned product revisions; the final reports were also staged and checked in the isolated C.1 worktree. Only sanitized review text is committed. Next verification gaps are the guarded native brightness-key route, the read-only radio-panel boundary, the unavailable Tailscale panel, and eight owner views/native font visuals when the screenshot privacy gate is clear.
