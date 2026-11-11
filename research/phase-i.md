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
timeout 10 s:

| Run | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| Idle median, MiB (323.9 before) | 358.0 | 382.8 | 410.1 | 433.6 | 450.8 |
| Last-100 slope, MiB per cycle | 0.18 | 0.10 | 0.09 | 0.11 | 0.15 |

File descriptors stay at 203–216. This is the rc2 shape (`phase-g.2.md`).

Whether the panel host builds a new window and scene graph for each open
without releasing the old: each open maps a new `omarchy-keyboard-panel` layer
surface, which is gone after closing, its address reused. One page for 200
cycles holds idle memory (464.0 → 460.3 MiB) and releases GPU buffer mappings
(393 → 189); Performance and Power alternating grows (466.0 → 492.9). The
panel host files are identical in rc2 and 4.5.0 and show and hide the window
the same way as 4.0.6's. So the host does build a fresh surface, and per
phase G.2's profile a fresh render context, on each open, and releases them;
the growth follows changing content, as G.2 found. No public path keeps the
panel's window alive across opens; keeping pages built roughly halved the rate
in G.2 and contradicts building a page only while it is open. G-V7 stays open
with this cause.

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
