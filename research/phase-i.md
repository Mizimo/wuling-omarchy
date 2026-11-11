# Phase I — Omarchy 4.5.0

Inbox v449 to v452, on top of `c7f6d48`. A fresh 4.5.0 install in a disposable
VM, and the 4.0.6 VM from its clean checkpoint for regression. The update from
4.0.6 to 4.5.0 is the verifier's line and is not covered here. No real hardware
was operated.

## Environment

The signed x86 ISO (`omarchy-4.5.0-x86.iso`, signature by
`40DFB630FF42BCFFB047046CF0134EE680CAC571`) installs unattended from a `cidata`
drive: `omarchy 4.5.0-3`, the stable repository's version at the time, so no
`omarchy update` followed. Hyprland 0.56.2-4, Quickshell 0.3.2.r7, Qt 6.12.0
and Mesa 26.2.5, as on rc2 and 4.0.6. Eight virtual CPUs, 8 GiB, virgl over
host llvmpipe. Input is real QMP keyboard, pointer and wheel events; captures
of transitions are 60 fps recordings of the VM display taken outside the VM.
Batteries come from a synthetic UPower service and Tailnet from a fixture
`tailscale`. Idle was paused in the VMs for long measurements.

On this install the Limine menu waits for a key before booting.

## Comparison with rc2

`research/omarchy-shell-api.md` §17 records the review and the content gates.
Of the files in `/usr/share/omarchy` that are also in the `v4.5.0` tag, all
match it except an installer-only helper. What WULING imports or reads is
unchanged from rc2, except for these:

| Item | Change in 4.5.0 | WULING |
|---|---|---|
| `omarchy version` | Prints `4.5.0-3` | Tested versions are 4.0.6 and 4.5.0; a release candidate is untested |
| Notification modules | Unchanged | Contract renamed `4.5.0` |
| `omarchy-theme-set`, `Background.qml` | The intro's output goes to `/dev/null`; a video background keeps the last still until OWE takes over | Reviewed `4.5.0` theme contract; still-background timing is unchanged |
| Notification store | A `transient` card is neither restored nor recorded | The same on 4.5.0 |
| Native bar | No input under a real full-screen window; tooltips wait for the fractional scale | The same on 4.5.0 |
| Region selection | Eight keys bound for the selection, then left disabled | Left out of the Keymap through Omarchy's own table |

## Changes

**Versions and contracts.** Before the change the installer named 4.5.0-3
untested, and the theme gate failed, so the wave stayed off. After it,
`wuling doctor` passes on both versions with no part on Omarchy's own.

**Transient notifications.** A critical `--transient` card, sent as
`omarchy-migrate-notify` sends its login reminder, showed each time and was
never saved: after three shell restarts, and once under DND, the saved live
list and history held only an ordinary control card, which history kept after
it was dismissed.

**The bar under a full-screen window.** With a real full-screen terminal and a
click on the bar's `02` cell:

| | Plain full screen | After a shell restart | After the bar is hidden and shown |
|---|---|---|---|
| Native 4.5.0 bar | Covered, click to the window | Drawn above, click to the window | Drawn above, click to the window |
| WULING before | Covered, click to the window | Drawn above, **click to the bar** | Covered in this run, drawn above in another |
| WULING after | Covered, click to the window | Drawn above, click to the window | Covered, click to the window |
| Native 4.0.6 bar | Covered, click to the window | Drawn above, click to the bar | Drawn above, click to the bar |
| WULING on 4.0.6 | Covered, click to the window | Drawn above, click to the bar | Covered, click to the window |

Hyprland draws a full-screen window above the top layer, and lifts a
remapped layer back above it; the native 4.5.0 bar only drops its input there.
WULING does the same from 4.5, and nothing on 4.0.6. A control click with no
full-screen window still reaches the bar on both. At 1920×1080 and scale 1.25,
three tooltip appearances recorded at 60 fps: before, the second or third frame
of each was blurred; after, every frame is sharp.

**Keymap.** `hyprctl binds` lists none of the selection keys before the first
region selection in a session, then all eight until a configuration reload,
enabled or not, with no field that tells them from a user's own bare Lua bind.
After a real selection the Keymap lists none of them; a fixture bare RETURN bind
of the user's own is listed once; with one character of the installed table
changed the Keymap lists all eight and `wuling doctor` says so as information.
Hyprland reloads its configuration when that file changes, which drops the
selection binds until the next selection.

## Theme wave

Fifty switches rotating the four WULING themes on one shell, the last 25 with
four busy CPU workers.

| Host, code | Played | Skipped | Skip reasons |
|---|---:|---:|---|
| 4.5.0, before | 0 | 50 | 36 late palette, 14 late capture |
| 4.5.0, after, three runs | 9 / 4 / 2 of 50 / 20 / 50 | 41 / 16 / 48 | Late palette and late capture |
| 4.0.6, after | 50 | 0 | |

Timed from the `next-theme` directory, medians on 4.5.0: the capture is ready
at 64 ms and the native palette arrives at 166–175 ms. Before, the per-switch
content gate was a Python process taking 112–126 ms. The startup gate now also
returns each gated file's digest and a switch rereads the files in the shell,
in 4 ms, running the full gate only on a difference. What remains is the lock
query (66 ms) and the two frames that put the cover on screen, 40 ms to more
than 130 ms under llvmpipe. Thirty recorded MIST/PAPER switches, four of them
played, show no frame of the old bar after the new one; one played sequence was
inspected frame by frame.

## G-V7 on 4.5.0

The verifier's 200-page cycle, five runs on one freshly restarted shell, IPC
timeout 10 s, with synthetic batteries and the Tailnet fixture:

| Run | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| Idle median, MiB (323.9 before) | 358.0 | 382.8 | 410.1 | 433.6 | 450.8 |
| Last-100 slope, MiB per cycle | 0.18 | 0.10 | 0.09 | 0.11 | 0.15 |

File descriptors stay at 203–216. This is the rc2 shape (`phase-g.2.md`).

Single pages and two alternating pages, measured twice: here on that same
grown shell, and by the verifier on freshly restarted shells
(`review/phase-i/README.md`, "G-V7 on 4.5.0"). MiB, idle after each 200-cycle
run against before it:

| Run | Here (batteries) | Verifier, batteries | Verifier, no batteries |
|---|---|---|---|
| One page | System: 464.0 → 460.3 | Performance: 344.3 → 359.1; Power: 370.7 → 372.2 | Performance: 321.2 → 331.5 and 372.4 → 376.7; Power: 347.9 → 353.1 |
| Performance and Power alternating | 466.0 → 492.9 | 358.6 → 366.9 | 337.3 → 342.2; 360.5 → 365.1 |

The two sets agree that the shell grows on 4.5.0 and that, with batteries,
alternating grows more than one page. They disagree on the rest: the verifier
saw alternating grow by about 4.5 MiB per 200 cycles where this run grew by
27, and, without batteries, one page grew about as much as alternating did.
Over all of the verifier's runs the shell grew by about 0.05–0.07 MiB per open.

The panel host maps a new `omarchy-keyboard-panel` layer surface on each open
and releases it on close, here and in all 1,650 of the verifier's opens. Its
files are identical in rc2 and 4.5.0 and show and hide the window the same way
as 4.0.6's. During the single-page run above, the shell's GPU buffer mappings
fell from 393 to 189.

What is established: the memory is held in Qt's rendering and text resources
(render contexts, glyph caches, font faces, GPU buffers, per `phase-g.2.md`),
not in a WULING object, and it accumulates with Terminal opens. The panel host
does not keep old surfaces. The exact condition that makes an open leave memory
behind is not known: it is not only a change of content. No public path keeps
the panel's window alive across opens; keeping pages built roughly halved the
rate in G.2 and contradicts building a page only while it is open. G-V7 stays
open.

## The bar after a shell restart

The verifier found WULING's bar back 1.7–3.7 s after Omarchy's on each
official shell restart (`review/phase-i/upgrade-from-4.0.6.md`). Timed from
`omarchy restart shell` to each layer mapping, polled every 20 ms in the guest,
with real restarts only:

| Host | Omarchy's bar | Empty fixture bar plugin | WULING's bar, only the bar enabled | WULING's bar, all parts |
|---|---|---|---|---|
| 4.5.0 | 0.63–0.78 s | 1.80–2.21 s | 1.97–2.01 s | 2.05–2.79 s, median 2.14 |
| 4.0.6 | 0.54–0.66 s | 1.37–1.57 s | | 1.76–2.10 s |

The shell builds its built-in bar before anything else. A bar from a plugin
waits for the plugin registry's scan, and on 4.5.0 that scan's result also
starts Omarchy's first-party services, about 1.2 s of main-thread work in the
journal, while the plugin bar's loader is asynchronous. Meanwhile Omarchy maps
its own bar layer, empty, from about 0.7 s until the plugin bar replaces it, so
a 60 fps recording shows the background without a bar. The registry's two
scripts take 17 and 38 ms when timed alone. An empty one-window bar plugin,
installed only for this test, arrives within 0.2 s of WULING's on 4.5.0 and
0.4 s on 4.0.6, so nearly all of the wait is the plugin-bar path that any
replacement bar takes. WULING's own share, its host's widgets and its other
parts, is 0.1–0.5 s. Nothing was changed: what WULING could shorten is small
against the rest.

## Matrix

- Cut text: the overview and all ten pages, two presets, three languages, text
  sizes 12 and 16, 1366×768: 132 views on 4.5.0. No label is cut. One value
  elides: a long kernel worker name in the Performance process list, at size 16.
- Real input on both versions: Super+Ctrl+G, Down to Calendar, Enter (number
  `02`, page loaded), Left back, Escape closes, a click on the bar's Terminal
  cell opens it; Keymap by Super+Ctrl+/, a typed filter, Escape clears then
  closes, an outside click closes, nothing stays loaded, shortcuts inhibited
  while open.
- 4.0.6: `wuling doctor` passes, the bar's 4.5 rules stay off, the Keymap has no
  selection table and reads 228 rows, the wave plays 50 of 50.

Captures, recordings and logs are in private round `wi1`; none are committed.
