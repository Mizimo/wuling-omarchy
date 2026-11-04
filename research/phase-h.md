# Phase H — Keymap and theme wave

Implemented against DESIGN sections 8.10 and 8.11, including the approved
native timing bound. Config also displays localized names for WULING's three
backgrounds. The implementation is ready for independent review. No physical
machine was operated; the results below are disposable-VM observations.

## Keymap

The ninth independent component reads `omarchy-menu-keybindings --print` on
open. It retains native descriptions and alternative chords. Installed
translations recover classification only; displayed descriptions stay intact.
A raw `hyprctl binds` snapshot supplements missing chords into OTHER. Active
XKB/platform names deduplicate code and symbol forms. Physical Copilot remains
`code:201`; unknown codes remain `code:N`. Undescribed Lua entries have a
localized generic description, and lid switches are excluded. No listed action
is executed or inferred from a Lua closure.

The responsive overlay has six groups, a filter, scrolling and two-stage
Escape. Its data, reader, view and stock Wayland ShortcutInhibitor disappear on
close. Exclusive focus alone was insufficient; a real test binding and volume
key confirmed inhibition and restoration. Super+Ctrl+/ is checked for symbol
and physical-code conflicts before installation. Updates adopt the component
once, preserve subsequent disablement, and remove only owned resources.

Config resolves Survey line, Thin band and Wide band through locale catalogs.
External backgrounds retain the native `omarchy theme bg current` name.

## Theme wave

Both native theme setters create `current/next-theme` before applying the new
palette. The session plugin watches that directory and requests one capture
per output. It checks the installed theme-set, Color, Style and Background
contents against `plugins/session/native-theme.json` at startup and before
each cover. Unknown contracts disable only the effect. No native code is
copied, modified, wrapped or delayed, and no standing capture runs.

All captures and two cover swaps per output must precede palette arrival.
A changed theme name is an additional early cutoff. A late capture cancels the
whole effect, preserving the native transition. A covered old scene waits for
a different theme name and palette application. From the last palette
assignment it waits the contract's 420 ms (4.0.6) or 840 ms (rc2, through native
`Style.duration`), plus 67 ms. The overall preparation/hold deadline is 1.5 s,
then a 420 ms, 16 by 9 cell wave reveals the new scene. This is a bound derived
from native implementation contents, not an observed background completion
signal. The owned no-animation layer rule avoids compositor fades.

Same-theme refresh, abandoned preparation, background-only changes, reduced
motion, disabled `session.theme`, lock, Arrival, Exit, output changes and visual
failure cancel or bypass the effect. Covers accept no input. Captures, surfaces,
mask effects and active timers unload afterward. Only counters and the last
timing record remain. Idle operation has a directory watcher and no wave poll.

## Environment and checks

Both VMs have eight virtual CPUs and 8 GiB RAM, with virgl backed by host
llvmpipe. Versions: Omarchy 4.0.6-1 / 4.5.0rc2-1, Hyprland 0.56.2-4,
Quickshell 0.3.2.r7.g2b4501a-1, Qt base 6.12.0-3 / declarative 6.12.0-2,
Mesa 26.2.5-1. `tools/check` passes 122 tests, generation/metadata/syntax
checks and staged-file privacy checks. The final run also exposed an existing
spectrum-test race: its PID file could precede output. The test now waits for
readable output before termination; the spectrum product code is unchanged.

Keymap checks on both versions:

- Real QMP shortcut, typed filter, PageDown, Escape and outside click; ordinary
  binding and volume-key inhibition, then restoration after closing.
- Four themes by three languages, 1366 by 768, 4K, 1.25 scale, and 800 by 600
  with 16 px type. The initial narrow-header collision was fixed and recaptured.
- Focused second output, unplug, reduced motion, reader failure, independent
  disablement and the unchanged native Super+K entry point.
- Native snapshots contain 229 / 245 rows after Copilot supplementation.
  Adding synthetic undescribed Lua and unknown-code bindings produces 231 / 247
  rows, with generic Lua text and `code:999` visible. A fixture chord that
  collided with a native alternative was correctly omitted and replaced for
  this test.
- Three owned background names and an external name, including the actual
  Config surface. Final doctor passes on both hosts.

Fifty ordinary theme switches on each version rotate all four themes. The
first 25 run without synthetic load; the remaining 25 run with four busy CPU
workers on the eight-vCPU guest, at the same scheduling priority as the shell.

| Host | Played, unloaded | Safely skipped | Skip reasons |
|---|---:|---:|---|
| 4.0.6 | 50 | 0 | None |
| 4.5 rc2 | 0 | 50 | 28 late captures, 22 late palettes |

The rc2 result is native fallback, not successful wave playback. Separately,
a synthetic WULING theme with 4,500 small files lengthens the unmodified native
preparation stage: rc2 plays a wave, and 4.0.6 captures, swaps and reveals both
outputs. These renderer fixtures are excluded from the ordinary playback rate.
Ordinary two-output trials also exercise safe whole-effect cancellation.

External 60 fps recordings cover PAPER and MIST on both hosts, with and without
CPU load. Inspected scene sequences and bar-frame strips show the held old
scene followed by the wave on 4.0.6, and native transitions on rc2. The eight
recordings' per-frame bar comparison finds no return to the old bar after the
new one is visible. This supports the observed sequences, not an unlimited
scheduling guarantee. At 1920 by 1080 and scale 1.25, a stationary wallpaper
region is pixel-identical before and during the frozen cover on both hosts.

Negative tests cover settings/reduced motion, same-theme/background-only and
abandoned staging, the 1.5-second incomplete-preparation expiry, input through
the cover, native picker, lock/unlock, Arrival/Exit exclusion, and output changes.
Hiding only WULING's visual file produces `overlay-failed`; the native theme
still changes and no cover remains. The file is restored afterward.

## Resource observations

Every sampled closed Keymap state has no view, rows, reader or inhibitor.
Fifty open/close cycles give these shell PSS values in KiB:

| Host | 0 | 10 | 20 | 30 | 40 | 50 |
|---|---:|---:|---:|---:|---:|---:|
| 4.0.6 | 314226 | 337726 | 335298 | 334262 | 328122 | 334818 |
| 4.5 rc2 | 342789 | 363097 | 361729 | 353421 | 361577 | 368009 |

FD counts end below their initial values, 151 to 148 and 201 to 193. Final
ten-second idle samples record zero shell CPU ticks on 4.0.6 and one tick
(100 Hz accounting) on rc2, with no Keymap reader, Terminal collector or wave
query process. The existing notification writer remains healthy.

Theme-switch PSS in KiB, including native theme and scene caches:

| Host | 0 | 10 | 20 | 30 | 40 | 50 | FD start/end |
|---|---:|---:|---:|---:|---:|---:|---|
| 4.0.6 | 307429 | 439258 | 447360 | 455130 | 457808 | 460888 | 159 / 164 |
| 4.5 rc2 | 333481 | 352239 | 360795 | 361796 | 360267 | 371171 | 211 / 212 |

Initial warm totals rise, so additional same-process controls were taken.
Twenty switches with the wave disabled give 469485 to 466922 KiB (4.0.6) and
382807 to 383847 KiB (rc2). After other edge tests, twenty more with it enabled
give 502533 to 498584 KiB and 451589 to 445424 KiB. Thus the continued runs do
not sustain the earlier increase. All effects unload and FDs stabilize. These
are bounded VM observations, not allocator attribution or a hardware budget.
No forced GC or product memory workaround was added.

## Evidence and limits

Raw logs, immutable captures, recordings and local harness scripts remain in
private round `wh1`. Final wave evidence is the `wave-soak-*-r2` runs, normal
`wave-record-*-r3` recordings and `wave-record-*-load` recordings. Early r1
capture crops and superseded r2 staging/gate candidates are excluded. The
first multi-output fixture sampled a stale last-result record and is excluded;
the later synchronous fixture records both output swaps. The private handoff
index identifies exact captures and reproduction commands.

The timing gate recognizes only tested module contents. Hardware timing,
physical multi-monitor capture, and independent acceptance remain unverified.
No DESIGN or BRIEF change is requested. VMs are shut down and restored to the
existing clean checkpoints at handoff; no new checkpoint is retained.
