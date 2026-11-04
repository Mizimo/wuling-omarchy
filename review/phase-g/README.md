# G independent verification

Inbox v175–v181; product `ef45c12c224cf84a8ff4e95074b3dd16fb7c9c6b`
(the Terminal's detail pages). This report is by the Claude verifier, who
took over from the Codex verifier at inbox v178. It combines three sources and
says which one each result comes from:

- **Claude, kujira** (read-only, 4.0.6, real hardware), inbox v178.
- **Claude, 4.5.0-rc2 VM**: a new run from the clean checkpoint that adds what
  the Codex run did not reach, plus independent reproductions of the findings.
- **Codex, both VMs**: the earlier v175 run, summarised in
  [CODEX-HANDOFF.md](CODEX-HANDOFF.md). It is cited here only where I reviewed
  the raw evidence (records, captures, process dumps) myself; the remaining
  Codex results are marked as Codex-reviewed.

Later main commits, including the H work and design changes made after these
findings, were not part of these pinned tests. No product code was changed.

## Findings

### G-V2 — P2: a cold Night toggle holds the Terminal's action queue

With the native night-light daemon not running, clicking Night turns the light
on, but the `wuling action night` process does not exit. Every later Terminal
action (another tile, a level, a page action) queues behind it until the
command wrapper's 120 s timeout or until `hyprsunset` exits.

Cause, read from the source and confirmed by process state: `command()` in
`bin/lib/wuling/__init__.py` runs `subprocess.run(..., capture_output=True,
timeout=120)`, which waits for end-of-file on its pipes. Omarchy's
`omarchy-toggle-nightlight` starts `hyprsunset`, which inherits those pipes.
The helper itself exits, the daemon keeps the pipes open.

Reproduced independently on 4.5.0-rc2 (Claude, `vm450/night-cold-control.json`):

| | 4.5.0-rc2 (Claude) | 4.0.6 (Codex, raw files reviewed) |
|---|---:|---:|
| Native helper, cold, output detached | 0.464 s, exit 0 | 0.514 s, exit 0 |
| `wuling action night`, warm daemon | exit 0 | exit 0 |
| `wuling action night`, cold, after 5 s | still running, light on | still running, light on |
| `hyprsunset` fd 1 and 2 | the action's capture pipes | the action's capture pipes |
| Action exits after stopping only the daemon | 0.131 s, exit 0 | 0.127 s, exit 0 |

In the 4.5 UI (`vm450/night-queue-ui-*.json`, two captures): cold Night click,
then a DND click two seconds later. DND stayed On for the full 8.7 s observed,
with `wuling action night` still pending; 0.52 s after only the daemon was
stopped the queued DND toggle applied. Codex saw the same queue on 4.0.6 with
a second Night click. Candidate repair: don't capture output for this
launcher, or launch it detached. Not patched or validated.

### G-V7 — P2: on 4.5, the shell's memory grows with every detail-page visit

BRIEF G asks that 200 page cycles show no steady growth. On 4.5.0-rc2 they
don't level off. Five separate 200-cycle runs on one shell, each opening the
next of the ten pages and closing the panel, end at an idle PSS+SwapPSS of
478.6, 499.0, 501.5, 518.6 and 530.5 MiB, from 463.8 before the first. Every
run's last 100 cycles climb 0.04–0.06 MiB per cycle, about 50 KiB per visit.
FDs (190), threads (21) and idle CPU (≈0.1 %) stay flat, and no collector is
left after any close, so this is memory held inside the shell, not a leaked
process or handle.

Two controls on the same shell right after: 200 toggles of Omarchy's own audio
panel (547.3 → 545.9 MiB) and 200 Terminal open/close cycles on the overview
without a page (549.4 → 550.3 MiB) do not grow. The growth comes with opening
detail pages. The 4.0.6 run (Codex) warmed by about 12 MiB and held flat over
its last 75 cycles, but it was a single 200-cycle run, so I can't say 4.0.6 is
free of it. The VM renders with llvmpipe, which inflates absolute numbers;
the trend is what matters. Numbers: [resources-450.json](resources-450.json).
Not instrumented; which page or object holds the memory is not established.

### G-V1 — P3: English Comms shows the literal key `count-unit`

In English the Comms count reads `8 count-unit`, in the overview head and on
the Comms page, on both versions (seen in my 4.5 captures and in Codex's 4.0.6
and 4.5 matrices). Traditional Chinese shows `8 則`. `plugins/terminal/i18n/en.json`
sets `"count-unit": ""` on purpose, and `Runtime.tr()` is
`translated[key] || english[key] || key`, so the empty string falls through to
the key. A presence check instead of `||` would keep the empty translation.

### G-V3 — P3: Comms scrolls into an empty body below its last record

At 640×480, and at 800×600 with Omarchy's text size 16, scrolling the Comms
page to the end leaves the content area completely blank. Every record is
still in history (`count` unchanged). One wheel step up brings back only the
last line after Tailnet; six steps still show nothing after Config; System and
a fresh open after closing the panel are blank too. Taller outputs
(1366×768 and up, fractional, 4K) show the last record correctly.

Seen by me in the controlled 4.5 probe (`vm450/comms-scroll-probe-1793818391803278613.json`,
13 captures), in the 4.5 narrow and text-size-16 matrix and bottom groups, and
in Codex's 13 4.0.6 probe captures, which I reviewed. `DetailFrame.qml` keeps
an inactive `Loader` in the content `Column` without tying its visibility to
its state; retained geometry from the previous page would explain the
observations, but that is a reading of the source, not an instrumented proof.

### G-V4 — P3: the System page's emblem renders as noise

The System page draws `plugins/terminal/emblem.svg`, the full Endfield mark
with 1.45-unit strokes, at about 44 px. At that size the fine contour lines
turn into a blotchy pattern inside the yellow square. Seen on kujira and in
every System capture on both VMs (Codex did not report it). The design has
since been changed so small marks use the plate (main `64239f4`); not retested.

### G-V5 — P3: labels cut at the 372 px panel width

In zh-Hant on kujira, Power's `Health · 健康度` shows as `健康…` with the value
pressed against it, and Performance's `LOAD 1 · 5 · 15` and `Frequency · 頻率`
are cut the same way. The same cuts are visible in the VM captures at the same
372 px width (Codex's 4.5 `wuling-en` sheet shows `LOAD 1 · 5 ·…`). The design
now says labels are never cut (main `64239f4`); not retested.

### G-V6 — P3: a muted input keeps the normal mic glyph

On kujira's Audio page the muted output shows the crossed-out speaker, but the
muted input keeps the plain mic icon. Its UNMUTE button and level are correct
(`wpctl` reported the source muted). Seen on kujira only; not reproduced in a VM.

## kujira — read-only, Claude, inbox v178

Omarchy 4.0.6-1, Hyprland 0.56.2, Quickshell 0.3.2, one 1366×768 output,
WULING installed by the design lead at `ef45c12` (version record shows the
commit). Worked only on empty workspace 9 with the gate before and after every
capture (workspace 9, no windows, no special workspace, unlocked, no toast).
Captures stay in private evidence because they show network, tailnet and
device names. Input was real: a Wayland virtual keyboard with the evdev keymap
(wtype's chords don't trigger Hyprland bindings) and a Wayland virtual pointer,
both without root, copied to a private directory and deleted afterwards.

- **Watcher at 03:00 JST (asked in v178):** not a leak. On arrival the
  Terminal was open on the Comms page (`open: true, page: comms`), drawn on the
  full-screen `omarchy-keyboard-panel` layer; its `wuling status --watch
  --sections clock comms` had run for 680 s as a child of the shell. Closing the
  panel removed both the layer and the watcher. Cause, confirmed by the design
  lead (v180): the design lead's read-only check at 03:00:08 called
  `omarchy-shell wuling.terminal.eDP-1 history`, which is `history() →
  openPage("comms")`, so it opened the Comms page by mistake. Not a product
  problem: the watcher ran only while the panel was open and stopped on close.
- **Routes:** keyboard Super+Ctrl+G → ↓ (user plate) → Enter (System) →
  Backspace → Esc. Pointer: bar cell; Wi-Fi, Bluetooth, Tailnet and Power tiles;
  the clock (Calendar) and `⋮` (Config), back with BACK each time. Audio,
  Performance and Comms through `wuling terminal open`, back with Backspace.
- **Data:** every page showed real values. Bluetooth is rfkill soft-blocked: the
  tile stays and shows Off, the page shows the radio Off and no devices, and
  the block was left in place. The Wi-Fi page opened without a scan (its list
  was 11 hours old). Its `TAILNET` badge matched `tailscale status`: two active
  direct peers route over the Wi-Fi interface. Power: one pack full, the empty
  pack muted as `N/A`. Calendar: Monday first, ISO week 45, day 309/365.
  Comms: history had 0 rows and showed the empty state.
- **Read-only held:** a process sampler over the whole session saw no
  `wuling action`, no rescan or Bluetooth discovery, and no set command for
  profile, volume, radio or tailnet. Profile, volume, mute, rfkill and the
  overrides hash were unchanged; no files or processes of mine remain.
- **Idle memory, same shell, before and after opening all ten pages once:**
  PSS+SwapPSS 295.0 → 315.5 MiB, CPU 0.033 % → 0.033 % of a core, 144 fds and
  25 threads both times. One tour is first-load cost, not a growth test. While
  closed for 3.5 minutes no WULING process started.

## 4.5.0-rc2 VM — Claude, new run

Fresh from `verified-clean-b`, 12 vCPU, 8 GiB, virgl on llvmpipe, physical
audio disabled and every sink private. Omarchy 4.5.0rc2-1, Hyprland 0.56.2-4,
Quickshell 0.3.2.r7. Installed from a metadata-free archive of the pinned tree.
Two fixture start-up races (an early Wi-Fi rescan, a BLE fixture started before
BlueZ registered the adapter) were completed by hand; both are recorded.

- **Matrix, the four groups Codex didn't reach:** narrow 640×480, 4K, 1920×1080
  at 1.25 and 800×600 with text size 16, ten pages each plus the System,
  Comms and Config bottoms (52 captures, output mode asserted per capture). All
  reviewed by eye: every page renders and reads; text size 16 grows the panel
  from 372 to 496 px. Exception: G-V3 in the narrow and size-16 groups.
- **Bottoms:** 20 captures; at size 16 the harness's margin wheel missed the
  scroll area on six pages, so a supplement scrolled them from the centre
  (Audio with ↑ instead, to leave the levels alone): every bottom is reachable,
  Comms excepted (G-V3).
- **Language:** all four choices set from the Config page by keyboard; Omarchy's
  `showHistory` lands on the Comms page.
- **Audio input:** two private inputs; keyboard level Home/→/End, mute, and
  selection; no capture stream added by the page. The first attempt timed out
  waiting for Home; repeated by hand and in a full rerun it passed. The failed
  attempt's log is kept; I could not reproduce it.
- **Motion:** externally recorded at 60 fps (4,593 frames, median gap 16.7 ms,
  max 60 ms). For all ten pages in field/full, hud/full and PAPER/reduced the
  first row is readable in the last frame at or before 320 ms after the request
  (requests include 83–101 ms of channel latency).
- **Retirement:** every page's collector is a new process that exits on
  leaving; closed, there is no watcher or `cava`.
- **Resources:** see G-V7 and below.
- **G-V2 on 4.5:** the native/WULING Night control and the UI queue (above).
- **Cleanup:** fixtures stopped and original services restored, `wuling
  uninstall`, inventory compared with the one taken before installation. The
  only differences were Omarchy's ibus runtime files and
  `~/.config/wuling/overrides.toml`, which I created before installing (sounds
  off) and then removed; one orphaned fixture player was stopped after checking
  its exact argv. Normal poweroff (exit 0), container removed, `verified-clean-b`
  and firmware restored, `qemu-img check` clean.

## Resources

4.0.6 (Codex run, recomputed by me from the raw JSONL): one 200-cycle run,
same shell throughout, no collector left after any close. PSS+SwapPSS medians
per 25 cycles 579 → 584 → 587 → 590 → 592 → 599 → 598 → 598 MiB: it warms by
about 12 MiB and then holds flat. FDs 141–145.

4.5.0-rc2 (Claude): five separate 200-cycle runs and two controls, all on one
shell; see G-V7 and [resources-450.json](resources-450.json). Detail-page
cycles keep growing; the native-panel and overview-only controls don't.

kujira, 4.0.6 real hardware: one tour of all ten pages, see above
(295.0 → 315.5 MiB, CPU unchanged). That is not a cycle test.

## Covered by Codex only

Reviewed by Codex, not repeated by me; I checked the raw records named here:
Wi-Fi with hwsim and hostapd (wrong then right passphrase, disconnect and
forget holds, release cancels, radio), Bluetooth with btvirt (discovery stops
on leaving, pairing, 76 % battery, forget, rfkill recovery), the fake Tailnet,
MPRIS with two identical players showing `--:--`, Comms actions with
revalidation, Config failures and music-path rejection, and the three install
origins (`vm450/versions-1793815354507541420.json`: git, release.json and
no-metadata produce distinct records). Passphrase scans: no match in either
version (`matches: []`, 4,174 and 3,358 root process scans, max gap 63 and
71 ms); sampling cannot exclude a process shorter than the gap. The 4.0.6
208-capture matrix and Codex's 156 4.5 standard captures (I reviewed two of
the twelve 4.5 sheets myself, wuling-en and hud-paper-zh-Hant).

## Evidence

Private, never committed: kujira `~/.cache/wuling-build/wg1/verifier-claude-v178/`;
4.5 run `~/.cache/wuling-build/wg1/verifier-claude-v179/`; Codex
`~/.cache/wuling-build/wg1/verifier-v175/`. Captures carry immutable
timestamped names with a state file each.
