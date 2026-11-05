# H and G.1 independent verification

Inbox v182; product `eba807e` on main (H in `9bc3213`, G.1 in `f0db59c`,
design rulings `64239f4` and `eba807e`). Claude verifier. The implementer's
claims in `research/phase-h.md` and `research/phase-g.1.md` were read as
claims only. Every result below comes from my own run on my own disks: two
VMs restored from the verified clean checkpoint, one at a time, WULING
installed from a clean `git archive` of `eba807e`, real QMP keyboard and
pointer input, captures judged by eye. IPC answers were used to find views and
read counters, never as the verdict. kujira was not touched this round.

| | 4.0.6 VM | 4.5.0-rc2 VM |
|---|---|---|
| Omarchy | 4.0.6-1 | 4.5.0rc2-1 |
| Hyprland / Quickshell / Qt | 0.56.2-4 / 0.3.2.r7 / 6.12 | same |
| Renderer | virtio-gpu, llvmpipe in the guest | same |
| vCPU | 8 | 12 |
| Output | Virtual-1 1280×800 (1366×768, 800×600, 640×480, 3840×2160 and scale 1.25 where stated); a second output from `hyprctl output create headless` | same |

The raw records, captures and videos are kept privately outside the
repository (`wh3/verifier-claude-v182/vm406`, `vm450`).

## Findings

No H or G.1 acceptance point fails. One new P3, found while checking G-V5's
crumbs; it is older than G.1 and not caused by it.

### H-V1 — P3: a page opened directly can show a different section number

DESIGN §8.2: section numbers follow what is shown, and a detail page's crumb
carries its section's number (`03 LINK › WI-FI`). At 1280×800 with the default
sections, the overview numbers 03 LINK, 04 LEVELS, 05 SIGNAL, 06 TELEMETRY and
07 COMMS. Opened by real clicks from the overview, the crumbs agree: the Power
tile gives `03 LINK › POWER`, the Telemetry block `06 TELEMETRY ›
PERFORMANCE`, also when the click lands 0.15 s after Backspace. Opened with
`wuling terminal open <page>` from a closed panel, which DESIGN lists as a way
in, some don't:

| Page | Overview / by click | `wuling terminal open` |
|---|---|---|
| power | `03 LINK` (tile) | `04 TELEMETRY` |
| performance | `06 TELEMETRY` | `04 TELEMETRY` |
| comms | `07` (section) | `08 COMMS` |
| audio, wifi, system | `04`, `03`, `02` | same |

Identical on 4.0.6 and 4.5.0-rc2 (`crumb-*` records, by eye). Cause, read from
the source: `openPage()` in `plugins/terminal/Terminal.qml` takes the number
from `shown`, which drops `link`, `levels` and `comms` while there is no state
for them. A closed Terminal collects nothing, so on a cold open `telemetry`
sits at index 2 (`04`), and `comms`, missing from `shown`, falls back to
`sections.indexOf`, which also counts the hidden `agent` (`08`). The number is
not recomputed when the state arrives. G-V5's views, which went from page to
page this way, show the same crumbs.

## H — Keymap

Opened with the real chord Super+Ctrl+/ through QMP. The test bindings were
appended to the guest's own `bindings.lua` and removed afterwards: a user
binding with a description (`G182 user marker`, writes a marker file), an
undescribed Lua binding on F11, and an unnamed key `code:999`.

| Check | 4.0.6 | 4.5.0-rc2 |
|---|---|---|
| Rows listed | 231 | 247 |
| User's own binding | `G182 user marker`, in its group | same |
| OTHER: Copilot key | `◆ SHIFT code:201` (Omarchy menu) | same |
| OTHER: undescribed Lua | `Lua binding · 無描述` (zh-Hant), F11 and `code:999` | same |
| OTHER: unnamed key | `code:999` | same |
| Filter `code`, `lua`, `g182` | narrows to the matching rows | same |
| Esc | first clears the filter, second closes | same |
| Outside click, blank desktop and on the bar | closes | same |
| While open: the marker binding, then the volume key | marker absent, volume stays 0.40, no OSD | same |
| After close: same keys | marker written, volume 0.45 | same |
| After close | not loaded, 0 rows, not inhibited, no reader process | same |
| `omarchy plugin disable wuling.keymap` | chord does nothing, `wuling keymap` answers `panel_unavailable` rc 1; Terminal, Dispatch and Omarchy's own Super+K work; doctor ok; re-enable restores it | same |
| H-L1: bar top, bottom, left, hidden | head, filter and columns clear of the bar; no `06` in the head | same |
| Matrix: four themes, three languages, 3840×2160, scale 1.25, 800×600, 800×600 with text size 16 | 10 captures readable, nothing cut; PAPER's light overlay uses its `ink-0` | same |

Fifty open/close cycles (4.0.6, same shell): PSS+SwapPSS 384.1 MiB before,
ten-cycle medians 392.9, 393.1, 391.2, 391.4, 393.2, idle 399.5 after; FDs 157
and threads 17 steady. On 4.5 (`km-latency`): 0 non-responses in 50 cycles,
median open 0.44 s (max 0.57), close 0.465 s (max 1.96), ten-cycle medians
413.9, 420.8, 427.0, 428.7, 428.3, FDs 202 steady.

Observation, not a finding: in an earlier 4.5 attempt one `omarchy-shell`
call around open/close took just over the command's 2 s limit and answered
"omarchy-shell is not responding" (cycle 9 of 50). The Keymap itself opened
and closed. Fifty more cycles with timing found no repeat; the slowest state
call was 1.69 s. This is llvmpipe in a VM; I can't say whether hardware shows
it.

Minor notes for design, not tested defects: native descriptions stay English
in zh (as the README says); the workspace group lists "Switch to workspace 10"
before 1; the README's list of parts for `omarchy plugin disable` doesn't name
`wuling.keymap`.

## H — Theme wave

Recording: ffmpeg x11grab of the VM window outside the guest, 60 fps
lossless, frame timestamps from showinfo. Each frame's bar is split into 16
cells and each cell is classed old/new/unknown against the bar before and
after; any old cell after a new one is a violation. Strips of every switch and
full frames at the wave's middle were checked by eye. A theme switch resets
Virtual-1 to its configured 1280×800, so the wave videos are at 1280×800.

### Routes, themes and outputs

| | 4.0.6 | 4.5.0-rc2 |
|---|---|---|
| Routes: `omarchy-theme-set`; Omarchy picker, theme menu and Config THEME by keyboard; all four WULING themes and native themes | 8/8 played | 2/8 played (menu, Config); 6 fell back: `late-capture` 4, `late-palette` 2 |
| Bar violations (old after new) | 0 (max frame gap 31 ms) | 0 (max gap 56 ms) |
| Timing after the switch starts | capture 51–73 ms, palette 521–679, wave 1016–1172, finished 1436–1606 | — |
| By eye | wave sweeps 16×9 cells with the yellow ghost outline; bar flips under it | played: same; fallback: Omarchy's own slanted wipe at ≈0.8 s, no WULING cover, no old frame after the new |
| Two outputs (Virtual-1 and a headless output) | 3/3 played, swaps on both | 0/3 played, `late-capture`; native change on both, no return to the old bar |

The headless output is captured in the guest by `grim -o` at about 200 ms
intervals, so it shows sequence, not smoothness. A theme switch also resets
the headless output's size, which blacks it for one or two captures in the
first switch; that is the harness.

On 4.5.0-rc2 the wave mostly does not play, as the implementer reported and
inbox v182 accepts as a safe fallback. What I checked is that the fallback is
clean: in every fallback, by bar cells and by eye, the old theme never comes
back after the new one, no WULING layer is left, and the switch is Omarchy's
own.

### The switch doesn't wait

Median of 12 `omarchy theme set` calls, each:

| | 4.0.6 | 4.5.0-rc2 |
|---|---:|---:|
| Native, before installing WULING | 3.359 s (3.339–3.400) | 3.123 s (3.107–3.143) |
| WULING installed, native themes, wave on | 3.408 | 3.141 |
| WULING themes, wave on | 3.394 | 3.143 |
| WULING themes, wave off | 3.394 | 3.123 |

The 4.0.6 difference of 35–49 ms is within the spread of the switch itself
and the same with the wave off, so the wave doesn't add to the switch.

### Failure, off, and skips

| Case | 4.0.6 | 4.5.0-rc2 |
|---|---|---|
| Overlay fails (`ThemeWave.qml` hidden, fresh shell with `omarchy restart shell`) | theme changes in 3.52 s, `overlay-failed`, no cover | changes in 3.28 s, `overlay-failed`, no cover |
| `session.theme false` | 0 played, bar flips at ≈0.7 s | 0 played |
| Reduced motion | 0 played | 0 played |
| Same theme | skipped `unchanged-or-failed`, no cover | same |
| Background only | no bar change, no cover | same |
| Locked | skipped `locked-or-unavailable`; real unlock OK | same |
| During Arrival | 0 played (`locked-or-unavailable`) | 0 played |
| During Exit | skipped `disabled` | skipped `late-capture` |
| Wave layer after each case | none | none |

The first overlay-failure attempt on 4.0.6 still played: Qt had the component
cached in the running shell. The case is only valid on a freshly started
shell, which the rows above are.

### Fifty switches

Shell PSS+SwapPSS in MiB, sampled 2.5 s after each switch, rotating the four
WULING themes, one shell throughout each version:

| Run | Played | Before | Medians per 10 switches | Idle after | FDs, threads |
|---|---:|---:|---|---:|---|
| 4.0.6 wave on | 50/50 | 398.4 | 429.6, 431.3, 435.1, 439.2, 442.1 | 442.0 | 159→161, 19→21 |
| 4.0.6 wave off | 0/50 | 446.7 | 446.8, 447.9, 447.4, 448.6, 447.9 | 449.7 | 161, 21 |
| 4.0.6 wave on again | 50/50 | 447.4 | 445.4, 447.3, 455.8, 455.8, 455.5 | 452.9 | 161→162, 21→22 |
| 4.5 wave on (fallback) | 0/50 | 404.7 | 402.1, 405.6, 404.9, 410.5, 410.2 | 411.2 | 215, 28 |
| 4.5 wave off | 0/50 | 414.2 | 415.5, 412.9, 412.7, 412.9, 412.2 | 410.7 | 215, 28 |
| 4.5 wave on again (fallback) | 0/50 | 404.0 | 410.8, 412.5, 412.4, 415.9, 414.7 | 416.8 | 215, 28 |

The 4.0.6 runs rose while the wave played and stayed flat while it was off,
and 100 played switches couldn't tell a plateau from slow growth. So I ran a
longer check on a fresh 4.0.6 install (same checkpoint, fixtures and Comms
rows): 300 switches with the wave on, then 100 with it off, same shell.

| Run | Played | Before | Medians per 25 switches | Idle after | FDs, threads |
|---|---:|---:|---|---:|---|
| 4.0.6 wave on, 300 | 300/300 | 428.6 | 455.0, 471.0, 469.9, 469.6, 470.6, 471.1, 471.7, 472.8, 472.9, 474.0, 473.8, 474.9 | 474.5 | 160→162, 19→21 |
| 4.0.6 wave off, 100 | 0/100 | 476.7 | per 10: 482.5, 483.8, 482.1, 482.0, 483.0, 482.2, 482.9, 483.2, 482.3, 482.6 | 481.6 | 162, 21 |

The first ≈50 played switches warm up by about 42 MiB; after that the trend
is 22 KiB per switch (least squares over switches 50–299), 5 MiB in 250
switches, and off is flat. Switch time stayed 3.41 s median (max 4.16). I
don't count this as steady growth in BRIEF's sense, and it is far inside what
the owner called a reasonable range. If the owner means no persistent residual
at all, this slow trend is the one to look at. The implementer's own numbers
(4.0.6, 300.2 to 450.1 MiB over 50, most of it in the first 10) show the same
warm-up.

## G.1

Each finding re-run with the method that found it.

| Finding | 4.0.6 | 4.5.0-rc2 | Verdict |
|---|---|---|---|
| G-V1 count in three languages | `8`, `8 則`, `8 则` | same | fixed |
| G-V2 cold Night by pointer | on in 0.88 s, no `wuling action` left; second click off in 0.64 s; daemon stays | 0.85 s, none left; 0.62 s | fixed |
| G-V2 Lock action | `wuling action lock` returns in 0.27 s, locked, none pending, real unlock | 0.33 s, same | fixed |
| G-V3 Comms bottom after Tailnet, Config, System and direct, 640×480; 800×600 text size 16 after Config, System, Tailnet | ends on `Matrix content 0` above the foot | same | fixed |
| G-V4 System emblem | on the plate, no dark corners | same | fixed |
| G-V5 labels at 1366×768 | see below | see below | fixed |
| G-V6 muted input | crossed-out mic; plain when unmuted | same | fixed |
| H-L1 | see Keymap | see Keymap | fixed |

G-V5: 132 views per version, overview plus ten pages (Comms counted once),
`wuling` and `wuling-hud`, text size 12 and 16, English, zh-Hant and
zh-Hans. `truncated()` reports only the long notification bodies on the
overview and Comms (24 views), which are cut on purpose. By eye, every label
is whole, including the ones G-V5 found: `LOAD` / `1 · 5 · 15`,
`Frequency · 頻率`, `Health · 健康度` (stacked at size 12 in `hud`), and the
crumbs. At size 16, 1366×768, the overview and some pages are taller than the
panel and scroll, as DESIGN and the owner's 2026-11-05 decision say.

Regression: the DetailFrame layout at 640×480 and 800×600 size 16 reaches the
end of every page with the keyboard and returns; the translation fallback
shows the right words in all three languages. The Config page's FONT row
captured blank at 640×480 was a frame mid-selection; the settled capture is
complete.

G-V7 (P2, memory per detail-page visit on 4.5) was not part of G.1 and was not
measured again.

## Cleanup

Both VMs: the test bindings, text-size files and bar position restored byte
for byte where a test changed them; `wuling uninstall --yes`; the inventory
of the home directory afterwards differs from before installation only in
`~/.config/wuling` (`overrides.toml`, the verifier's settings), which I
removed. The fixture
player each run started was stopped after an exact argv check; the private
work directory in the guest was removed. Normal shutdown, my containers
removed, the original verified checkpoint and firmware restored;
`qemu-img check` clean, sole snapshot `verified-clean-b`. During the first
4.0.6 run, my use of `omarchy bar position` left `shell.json` at mode 0600
with unchanged content; the inventory caught it and I set it back to 0644.

## H-V1 retest

Inbox v184; product `3ba6c49` on main (the fix is `4f41f22`). The same
method: both VMs restored from the clean checkpoint, one at a time, WULING
installed from a clean `git archive` of `3ba6c49`, real QMP input, an
external 60 fps recording of the whole run, a guest-side poller reading the
Terminal's `state` and the collector's argv every ≈50 ms. Theme `wuling`,
English, 1280×800, default sections, the synthetic fixtures and 8 Comms rows,
so the overview numbers 02 TERMINAL, 03 LINK, 04 LEVELS, 05 SIGNAL,
06 TELEMETRY, 07 COMMS. **H-V1 is fixed on both versions.**

### Every route

| Route | Pages | 4.0.6 | 4.5.0-rc2 |
|---|---|---|---|
| `wuling terminal open <page>`, panel closed and collector gone | power, performance, comms, wifi, system, audio, calendar, bluetooth, tailnet, config | 06, 06, 07, 03, 02, 04, 02, 03, 03, 02 | same |
| `wuling terminal open <page>` over an open Performance page | power, comms, wifi, system, audio | 06, 07, 03, 02, 04 | same |
| Real click on a settled overview | Power tile, Telemetry, Wi-Fi tile | 03 (the tile's own section, as before), 06, 03 | same |
| Real click about 0.5 s after a cold open, the overview still fading in | Telemetry | 06 | same |
| Omarchy's notification key Super+Shift+Alt+comma (`showHistory`), panel closed | comms | 07 | same |
| Same key over an open Performance page | comms | 07 | same |

Every head matches the overview, by eye on the settled captures and in
`state.number`.

### Never a wrong number

For each of the 21 opens per version I cropped the head row from the
external recording, every frame from 0.1 s before the request to 1.75 s after,
and read the strips by eye; yellow-pixel masks against the settled number
pointed out every frame where the number area changed. In all 42 opens the
head shows either no number or the right one. Frames classed "other" by the
mask are the slide-in and fade (the right number, partly drawn) or the
previous page and the overview behind the new page. Where a section before the
page can be hidden, the head waits without a number for 0.15–0.28 s after
the page is readable: Comms, Audio, Power and Performance opened directly,
and the notification key (4.0.6 0.17 s, 4.5 0.18 s). Wi-Fi, System and the
other pages with no optional section before them, and every click from the
overview, show their number with the page.

### What is read, and when

| Check | 4.0.6 | 4.5.0-rc2 |
|---|---|---|
| Collector on a directly opened Performance page | `wuling status --watch --sections clock performance layout` | same |
| After Back to the overview | overview sections, no `layout` | same |
| Panel closed | no collector | same |
| `RequestScan` calls to NetworkManager (D-Bus monitor) in 30 s idle; 12 opens of Performance, Power, Comms, Audio; 6 of System, Calendar; 3 overviews; 2 Wi-Fi pages | 0 in every phase | 0 |
| Control: `nmcli device wifi rescan` | 1 caught | 1 caught |

NetworkManager's `LastScan` also changed a few times in these runs, every
64–95 s and with no request on D-Bus: those are its own background scans
while the fixture radio is not connected, not WULING's. From the source,
`layout` asks `nmcli` only for device status, radio state and the active
connection, and is read once per collector (its next read is due in an
hour); I didn't count reads from outside.

### Regression

Comms count `8`, `8 則`, `8 则`, with `07 COMMS` in the head in all three
languages; the Keymap head has no `06` and starts below the bar; Comms scrolled
to the end after Tailnet, Config, System and a direct open ends on
`Matrix content 0` above the foot. Both versions, by eye.

### Cleanup

As above, on both VMs: the inventory after `wuling uninstall --yes` differs
from before installation only in my `~/.config/wuling`, removed; fixture
player stopped after an exact argv check; normal shutdown, containers
removed, checkpoint and firmware restored, `qemu-img check` clean, sole
snapshot `verified-clean-b`. 4.0.6 was booted twice; the second boot only ran
the D-Bus scan check.
