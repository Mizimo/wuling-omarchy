# G, second installment: five Terminal pages

Implemented under inbox v436 and DESIGN §8.2. This installment adds
Performance, Power, Audio, System and Calendar. Wi-Fi, Bluetooth, Tailnet and
Config remain the following installments. No hardware machine was accessed.

## Behavior and native boundaries

The user label and clock enter System and Calendar; CPU, memory and temperature
enter Performance; each battery and the Power profile tile enter Power; the
volume icon enters Audio. The tile's right button still asks for Omarchy's
native panel. `wuling terminal open PAGE` reaches the same pages. Pointer and
keyboard share the detail frame, back/close behavior, clock, crumb, watermark,
scroll/fade, HUD scan and reduced motion. A page loader is explicitly released
on Terminal close; hidden compositor animations cannot keep it alive.

- Performance samples `/proc` once a second while open. CPU and process CPU
  need a previous sample and initially show an unknown value. PID/start-time
  identity prevents reuse from producing a false CPU spike. History is bounded
  to 60 samples. Used/cache/free sum to total; swap is separate. `S` sorts the
  top process list, and Enter opens the native `btop` launcher.
- Power uses UPower batteries and 24-hour history. Combined percentage weights
  energy by full capacity, excluding absent/zero-capacity packs. History is
  refreshed at most once a minute; state is refreshed every two seconds.
  Public PowerProfiles properties provide the same available/active profiles
  read by installed `powerprofilesctl`; mutations use
  `omarchy-powerprofiles-set autodetect`, retaining native AC/battery memory.
  Left/right selects an available profile and scrolls it into view; Enter
  applies it. Failed changes stay on the page with an error.
- Audio projects public `pw-dump` output, native sink availability and native
  DSP volume targeting. PipeWire channel volume is converted with the cube
  root, matching `wpctl`. Native helpers choose defaults and move streams;
  `wpctl` adjusts individual levels and mute. Actions revalidate node ID and
  serial. Stable delegate identities keep controls in place during a drag.
  Slider actions coalesce by identity, preserving discrete actions in order.
- System shows local identity immediately while bounded native version probes
  finish, then disk, displays, input method and release metadata. Installation
  owns a small projected `release.json`, derived from a Git checkout or archive
  metadata; missing archive metadata remains unknown. COPY sends current JSON
  to `wl-copy` on stdin. COPY and native TUI launches do not capture a surviving
  child's output pipes, which would stall subsequent actions.
- Calendar is Monday-first with ISO week numbers, actual month rollover,
  leap-year and local-zone handling. Previous/next month, PgUp/PgDn and Today
  work without a background calendar process.

Each page is an opt-in `wuling status` section. The default overview set is
unchanged. Leaving a page cancels its in-flight process groups and joins its
bounded probe scope; closing Terminal stops collection and releases the page.
No new runtime dependency, daemon, private native-object lookup or cache file
is introduced. The approved vector mark is packaged for System.

### Input meter deliberately omitted

A disposable `PwNodePeakMonitor` attached to the default input created an
unmuted Quickshell capture stream. Omarchy 4.0.6's native microphone indicator
includes that stream; rc2 filters shell meters. Following the explicit design
exception, the live input meter is omitted on both versions. Input selection,
volume and mute remain. Evidence: `vm406/mic-indicator.txt`. The diagnostic
capture process was stopped; product code never starts it.

## Verification

Private evidence is in `wg2/`; no raw logs, JSON, screenshots or videos are
committed. Both VMs started from their clean F checkpoints. Omarchy versions
are `4.0.6-1` and `4.5.0rc2-1`; Quickshell `0.3.2.r7.g2b4501a-1`, Qt base
`6.12.0-3`, declarative `6.12.0-2`, Mesa `1:26.2.5-1`, and PipeWire `1:1.6.9-1`.
A real synthetic UPower service supplies three packs: charging, absent and low.
Audio uses private null sinks, a remapped silent input and a silent playback
stream. QEMU has no physical audio output.

| Check | Evidence and result |
| --- | --- |
| Display-free | Final `tools/check` covers 100 runtime tests, generated kit equality, command metadata, syntax and staged privacy. New tests include CPU/PID reuse, battery weighting/history/profile projection, volume curve and stale node identities, native failure postconditions, clipboard pipe handling, opt-in collection, cancellation of running and pending probes, immediate System identity, leap dates and DST. |
| Entries | `entries-406-r6.log`, `entries-450-r5.log`: five pointer routes and the same five keyboard routes, each with Backspace and Esc. An earlier harness run misdirected pointer coordinates after unlocking; the final fixture verifies actual compositor cursor position before clicking. Earlier failed runs are excluded. |
| Actions | `actions-{406,450}-r2.log`: real keyboard profile changes, copied System JSON, native About/Fastfetch and btop launches, sort, month change and Today. `smoke-*-final-r3.log` repeats profile focus/selection and Comms/back/close on the final candidate. |
| Audio | `audio-{406,450}.log`: real pointer/wheel output, input and stream level changes, mute/unmute, default output/input selection, native stream movement and no collector after close. Only silent VM devices were changed. |
| Failures | `error-{406,450}.log`: temporarily unavailable PowerProfiles service rejects the action while the Power page and battery data remain; the service is restored in a finally block. Native helpers returning success without changing the default audio device are also rejected by a postcondition test. |
| Theme/language | `vm406/matrix.json`, `vm450/matrix.json`: four themes × three languages × five pages, 60 captures per VM with real keyboard back/close. |
| Layout | `layouts-{406,450}.log`: all five pages at 800×600, larger native text, 3840×2160, and 1920×1080 at scale 1.25. Long pages scroll; profiles selected by arrows are brought into view. Representative captures were visually inspected; `vm406/review-shots.json` indexes all five pages in four themes in Traditional Chinese. |

### First readable content

Captures are requested 250 ms after the native page request. Capture completion
is an upper bound for the visible image, not a first-swap measurement.
`first-row-*-r4.log` covers field, HUD and reduced motion, five pages each.
The System sample from 4.0.6 field still contained placeholders and is excluded.
The final System change publishes real local identity before external version
commands finish; `first-row-system-*-final.log` replaces all six System cases.
CPU's first percentage remains unknown until the second sample; actual load,
frequency and uptime are already readable. Earlier serial/slow-profile runs
are retained as diagnosis and are not counted as passes.

All 30 accepted captures were visually checked. Completion bounds are
277.8–300.2 ms on 4.0.6 and 275.2–294.8 ms on rc2, below 320 ms.
`shots/review-first-row-system-final.png` combines the six replacement System
captures; the original immutable captures and timings remain alongside it.

### Repeated-page behavior and idle

`cycles-406-r13.log` and `cycles-450-r13.log` contain 200 mixed-page cycles
per VM (40 per page), with periodic overview visits and closed-state samples.
Every sample has no page, no requested sections, no loaded detail and inactive
spectrum. The rc2 transport returned 143 after recording cycle 200 and its
completion marker; the same native shell then completed another 200 cycles
with a normal harness exit (`cycles-450-r13-continuation.log`).

| Run | Initial PSS | Final PSS | FD during closed cycle samples |
| --- | ---: | ---: | ---: |
| 4.0.6, 200 cycles | 448.8 MiB | 458.6 MiB | 145 |
| rc2, 200 cycles | 376.1 MiB | 411.6 MiB | 190 |
| rc2, another 200, same shell | 420.3 MiB | 414.8 MiB | 186 initially, then 190 |

The 4.0.6 final four samples span 456.6–460.1 MiB; the rc2 continuation
oscillates rather than steadily accumulating. These are allocator-retention
observations, not a zero-delta claim or an unlimited-duration guarantee. No
forced GC or numerical memory budget was introduced.

After closing, both VMs have no Terminal watch/spectrum process, no loaded
page and no retained rows. A ten-second observation records zero additional
shell CPU ticks, with FD counts 141 and 186. This is a short idle observation,
not a long soak. `vm*/idle-final.json` and the rc2 continuation observation
retain the measurements. Both final `wuling doctor` results are successful.
Shell logs contain the existing startup/service and deprecated native API
warnings, with no new detail-page QML error during the cycles.

## Limits and follow-up

VM batteries and silent audio devices exercise protocols and input behavior;
they do not establish physical hardware support, hotplug timing or vendor DSP
behavior. The independent verifier owns hardware acceptance. A source archive
without release metadata displays unknown release fields rather than invented
values. The input-meter exception is the only intentional omission from these
five pages. No DESIGN change is requested.

The round occupies about 554 MiB. Both VMs were shut down normally, restored
to their clean F disk/firmware checkpoints and passed `qemu-img check`; only
the baseline and latest clean checkpoint remain. Both G2 containers and their
image tag were removed. The same runtime image is retained under the G3 name
for the next installment, avoiding a duplicate download or build. Raw evidence
is retained for review; no new VM checkpoint or release tar was created.
