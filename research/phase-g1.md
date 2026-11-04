# G, first installment: Comms, batteries and Signal

Implemented under inbox v436, design `a65ab81` and the Signal ruling `11c9521`.
Comms, battery cells and the full Signal presentation are included. No hardware
machine was accessed. The later Terminal pages are outside this installment.

## Native media boundary

The tested native `media status` exposes the selected player's identity,
desktop entry, metadata, artwork, playback state and transport capabilities.
It does not expose its MPRIS bus name, length or position. Third-party plugins
cannot use the first-party service facade to obtain them.

The adapter keeps selection and transport with Omarchy, reads public
MPRIS properties, and supplements time only when exactly one player matches
the native identity, desktop entry, track metadata and playback state. Both VMs
returned length 180 seconds and advancing position near 36 seconds for one
synthetic player. Adding an identical second player returned unknown values;
changing the D-Bus track without notifying the native service also returned
unknown values. A native next-track action restored the match. Ambiguous,
unreadable or inconsistent candidates show `--:--` and an empty progress line,
retaining native metadata and controls, as approved in v436. Time queries run
only in the open overview while playing; paused players retain their layout
without querying times. There is no private-object traversal or player choice.

## Implementation

- Comms overview: source, time, summary, two body lines, expandable full body
  and validated action buttons. `+N`, the history command and native
  `showHistory` enter the Comms page; `CLEAR ALL` uses the notification service.
  A disabled Comms section retains native history replay, including under DND.
- The detail frame retains the clock, adds back/crumb, keyboard navigation,
  scrolling/fade, watermark and bounded error feedback. Closing forgets the
  page. A failed action preserves the page and rows. Native contract-specific
  action execution remains in the notification service; executable arguments
  never enter the display model. Text comes from the normalized, redacted
  private history, with markup removed.
- Telemetry shows each UPower system battery, including low, charging and
  absent/zero-capacity packs. Battery navigation belongs to the next installment.
- Signal keeps paused and absent-player states visible, with 64-pixel art,
  native transport, crossfade and 20 jade cells. Optional cava runs at nice 19
  only while the overview is open and playback is active. Without cava,
  a uniquely matched stereo PipeWire stream supplies a peak meter; unsupported
  or missing streams use flat cells. Mono streams are excluded because the
  tested native peak monitor negotiates stereo and otherwise emits repeated
  channel-mismatch warnings. No audio is sent to physical hardware.
- Page changes stop the previous collectors; close cancels in-flight command
  groups and releases rows, art, spectrum and stream tracking. The Comms page
  requests only clock and history. Pending readers deliver promptly rather
  than waiting for the next polling period.
- English, Traditional Chinese and Simplified Chinese labels are included.
  The icon subset was regenerated to include the absent-player glyph.

## Verification

Private evidence is in `wg1/`; no raw capture, log or JSON is committed.
Both disposable VMs use Quickshell `0.3.2.r7.g2b4501a-1`, Qt base `6.12.0-3`,
Qt declarative `6.12.0-2`, Mesa `1:26.2.5-1` and PipeWire `1:1.6.9-1`.
Omarchy versions are `4.0.6-1` and `4.5.0rc2-1`. Optional cava `1.0.0-1` was
added in the VMs through `omarchy pkg add`; WULING does not install it.

| Check | Observation |
| --- | --- |
| Display-free checks | The candidate passed 91 tests and private-index privacy; delivery adds a unique/duplicate/inconsistent MPRIS test, including the paused/no-player query guard. Final check output is `check-delivery.log`. |
| Notification behavior | Real synthetic notifications, overview expand/collapse, `+N`, full page, native history routing, clear, default action and rc2 additional action passed. The long action label is bounded and elided. A stale action reports failure without leaving the page. |
| Pointer and keyboard | Page entry, up/down selection, Enter activation, Backspace/Left/Esc back and Esc close exercised. Final 4.0.6 smoke confirms Up from no selection reaches the last action. |
| Battery data | A real synthetic UPower D-Bus service supplies charging 78%, absent zero-capacity and low 8% packs. Parser tests cover invalid input and absent hardware. |
| Signal lifecycle | Playing, paused and absent players; artwork; native controls; cava frames/nice/exit; real stereo peak and mono flat fallback exercised. `media-accept-{406,450}.log` verifies progressing time, duplicate and stale-track fallback, native next/previous/play-pause, page exit and close. No spectrum or Terminal collector child remains after close. |
| Theme/language matrix | Both VMs: four themes by three languages, overview and Comms captures, with keyboard return/close. `vm406/matrix.json`, `vm450/matrix.json`. |
| Layout | Both VMs: 800x600, larger native text, 3840x2160, and 1920x1080 at scale 1.25. `layouts-406.log`, `layouts-450.log`. |
| Readable first row | After changing reader delivery from 50 ms polling to completion-driven wakeup, uncompressed captures requested at 250 ms show complete rows in field, HUD and reduced modes on both versions. Capture completion: 4.0.6 286.1/288.6/275.0 ms; rc2 291.2/280.7/286.7 ms (`first-row-event-{406,450}.log`). All six images were visually checked. These are capture upper bounds, not first-swap timestamps. Earlier empty captures and the earlier rc2 reduced capture completing at 321.8 ms are not counted as passes. |

## Repeated-page behavior

Each VM completed 200 Comms open/close cycles, with periodic overview visits
and observations while closed. Terminal state consistently returned to no
page, no requested sections, no rows and inactive spectrum.

| Run | Initial PSS | Final PSS | FD observation |
| --- | ---: | ---: | --- |
| 4.0.6, 200 cycles | 311.2 MiB | 314.0 MiB | 141 initially, then 144–145 |
| rc2, 200 cycles | 354.8 MiB | 373.9 MiB | 189 initially, then 190–192, ending 190 |

4.0.6 oscillated rather than steadily increasing. rc2 retained about 19 MiB;
its last three samples were 373.1, 373.2 and 373.9 MiB. A preceding second
200-cycle rc2 run ended only 2.5 MiB above its start. As context, 200 opens of
the native Audio panel retained about 11.2 MiB with a stable FD count. These
observations show allocator retention and tapering, not zero memory delta;
they do not establish behavior over an unlimited run. No forced GC is used.
An early 4.0.6 run interrupted by the harness's two-second native IPC timeout
is excluded; complete runs use the ten-second diagnostic timeout.

The final 4.0.6 reinstall initially stopped at the ownership check because a
private Python diagnostic had generated bytecode inside the installed tree.
Removing only that diagnostic cache restored an exact match with the recorded
manifest, and normal installation then succeeded. Product ownership checks
were not bypassed or changed.

## Review and follow-up

`vm406/review-shots.json` indexes representative captures in all four themes:
collapsed and expanded Comms lists, the Comms page, playing Signal with battery
cells, and no-player Signal. These use synthetic data and the supported section
setting to isolate clock/Comms or clock/Signal/Telemetry; the default section
list is restored afterward. The full default-layout and language matrix is
recorded separately above.

The next installment adds Performance, Power, Audio, System and Calendar.
Hardware verification remains with the independent verifier. The mono-stream
fallback and ambiguous media times are explicit limitations, not claims that
every stream or player can be identified.
