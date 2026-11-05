# Phase G.2 — page numbers and detail-page memory

Inbox v445 and v446, on top of `a316056`. Both disposable VMs from the clean
checkpoints: Omarchy 4.0.6-1 and 4.5.0rc2-1, Hyprland 0.56.2, Quickshell
0.3.2, Qt 6.12.0, Mesa 26.2.5 (llvmpipe). Synthetic UPower batteries and a
fixture `tailscale`. No real hardware was operated.

## H-V1 — a page's number matches the overview

Opened with `wuling terminal open <page>` or through Omarchy's `showHistory`,
a page numbered its head from what the Terminal had collected so far. While a
page is open the collector reads only the clock and that page, so the
overview's optional sections (Link, Levels, Agent, Comms) were unknown:
Telemetry's pages said 04 where the overview says 06, and Comms 08 where it
says 07. Reproduced on both versions.

The number now counts the sections the overview shows before the page's own.
`wuling status` has a `layout` section, read once per collection, reporting
which optional sections would show; a page reads it only when one of them
comes before its section, so Clock and Link pages (02, 03) need nothing extra.
Opened from the overview the number is known at once. Otherwise the head shows
no number until it is known, then the right one: it never shows a guess that
changes. Terminal `state` reports it as `number`.

Polled every 50 ms for 3 s after each route, both versions: Power and
Performance `06`, Comms `07`, Wi-Fi `03`, System `02`, Power from an open
overview `06`. Comms through `showHistory` shows no number for about 0.1 s,
then `07`. No route showed any other value.

## G-V7 — memory while moving between pages on 4.5

Accepted for the release candidate and left open until Omarchy 4.5 is stable
(BRIEF, Verifying). This records what is known.

**Method.** The verifier's cycle: on one shell, each cycle opens the next of
the ten pages with `wuling terminal open`, waits 0.45 s, closes, and records
the shell's PSS+SwapPSS; separate 200-cycle runs, 21 s of idle samples before
and after. The only change is a 10 s IPC timeout, because the VM's renderer
occasionally stalls past Omarchy's default 2 s. Product `eba807e`.

**Reproduced.** MiB, idle median after each 200-cycle run, and the slope of
its last 100 cycles in MiB per cycle:

| Version | Before | After each run | Last-100 slopes |
|---|---:|---|---|
| 4.5.0-rc2 | 401.4 | 414.8, 450.3, 474.2, 495.4, 511.6 | 0.16, 0.11, 0.11, 0.11, 0.10 |
| 4.0.6 | 335.5 | 334.6, 339.7, 343.5 | 0.10, 0.02, 0.02 |

FDs and threads stay flat on both; no collector survives a close.

**What makes it grow** (all on one 4.5 shell):

- Each page alone, 100 cycles: flat, slopes −0.02 to 0.04.
- Performance and Power alternating, 200 cycles: flat (557.4 → 557.4).
- The full rotation again on that shell, already at 570 MiB: 577.0 → 602.0,
  slopes 0.12 and 0.15. So it is not a warm-up that levels off.
- The first five pages rotating: 605.0 → 636.8; the last five: 642.0 → 658.0.

Growth comes from moving between several pages with different content, not
from any one page.

**Where the memory is not.**

- A `gc()` called through a diagnostic IPC in the VM's installed copy (never
  in the product) leaves a grown shell where it was. It is not uncollected
  JavaScript.
- heaptrack, 200 against 800 cycles: PSS rises by 121 MiB while live malloc
  memory goes from 75.5 to 80.3 MiB. It is not heap objects, WULING's or
  Qt's.
- jemalloc's own statistics over 400 cycles stay at 126–142 MB allocated and
  158–179 MB resident while PSS rises 324.5 → 387.5. It is not memory the
  allocator keeps.

**Where it is.** Large anonymous mappings outside the allocator grow
(236.8 → 272.1 → 316.6 MiB over 400 cycles) while the JavaScript heap stays
near 20 MiB. A 200-cycle rotation adds 599 mappings on 4.5: 468 GPU buffer
objects of the render node, 89 JIT code segments, CJK font files and a few
regions of 3–16 MiB. On 4.0.6 the same rotation adds about as many (459
buffer objects, 91 JIT segments) but PSS rises only 13 MiB. Running one page
afterwards releases most of them. `mmap` call stacks, recorded with strace on
the shell's own threads over about 75 cycles, attribute what stays mapped to
FreeType reopening the CJK font files (`FT_New_Face`, about 85 MB of file
mappings) and its tables, a 14.7 MB Mesa context region, a 4.2 MB
`QDistanceField` and 5.2 MB of Qt Quick glyph data, and a 4 MB JavaScript heap
chunk. heaptrack also shows one GL context created per panel open and still
alive afterwards, on both versions alike.

**Changes tried, none of which stopped it** (fresh shell, two runs each):

| Change | After each run | Last-100 slopes |
|---|---|---|
| None | 340.2 → 365.9, 388.0 | 0.11, 0.12 |
| One `Component` per page, so Qt's type cache can't drop and reload pages | 324.1 → 365.4, 394.7 | 0.18, 0.13 |
| Visited pages kept, hidden, instead of rebuilt (five runs) | 337.3 → 382.3, 396.3, 404.5, 421.6, 428.8 | 0.06 to 0.10 |
| No 150 px watermark glyph | 317.5 → 368.7, 385.2 | 0.19, 0.10 |

Keeping pages roughly halves the rate but does not stop it, and contradicts
building a page only while it is open. None of these changes is in the
product.

**Judgement.** The memory is Qt Quick's text and rendering resources (render
contexts, glyph caches, font faces, GPU buffers) rebuilt as pages with
different text come and go, under the VM's Mesa renderer. No WULING object
holds it.

**Not known.** Why 4.5 keeps so much more than 4.0.6 with the same Qt, Mesa
and Quickshell; the leading suspect is how 4.5's panel host treats its window
and scene graph between opens. Whether real graphics hardware shows it at
all. `ef45c12` was not measured separately; G.1 changed only the Loader's
visibility, and the shape matches the verifier's numbers.

Captures, profiles and logs are in private round `wh2`; none are committed.
