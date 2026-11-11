# Phase I, first half: independent acceptance

Inbox v187; Claude verifier. Items a–f as delivered on main: a, b, c and d in
`fcda606`, e in `1de6536`, f in `a6a83c8`, with the design ruling `056ea04`.
I installed a clean `git archive` of `056ea04` (which excludes the later
`6916b61`) with `./install`. I read the implementer's notes in
`research/omarchy-shell-api.md` as claims only. Every result here comes from
my own runs with real QMP keyboard and pointer input, and I judged the
captures by eye. IPC and status output were used only to read counters.
kujira was not touched.

| | Fresh 4.5.0 VM | 4.0.6 VM |
|---|---|---|
| Base | installed by me from `omarchy-4.5.0-x86.iso` (sha256 `5d6288bc…`) in its own TUI; English, us layout, UTC, no disk encryption; I typed `sudo systemctl enable --now sshd` and `sudo ufw allow 22/tcp` at the console for the harness; checkpoint `verified-clean-b` | my verified clean checkpoint from earlier rounds |
| Omarchy | 4.5.0-3 | 4.0.6-1 |
| Hyprland / Quickshell | 0.56.2-4 / 0.3.2.r7 | same |
| Renderer, vCPU | virtio-gpu, llvmpipe in the guest; 8 (first written as 12; corrected in the second half) | same; 8 |
| Output | Virtual-1 1280×800, scale 1.25 where stated | same |

The raw records, captures and videos are kept privately (`wi2/verifier-claude-v186`).

## Result

All six items pass on 4.5.0, and e and f leave 4.0.6 as it was. There are no
findings against phase I. Three observations follow, two of them Omarchy's
own: the bar input after a shell restart under full screen,
4.0.6's selection keys removing a user's bind, and a 50 ms blank TERMINAL
label at hover start that already exists on 4.0.6.

## a, b, d — versions and contracts

`wuling doctor` exits 0 on both VMs.

| Check | 4.5.0 | 4.0.6 |
|---|---|---|
| `omarchy` | ok, 4.5.0-3, tested, `tested_versions` 4.0.6 and 4.5.0 | ok, 4.0.6-1, tested |
| `notifications:compatibility` | ok, contract 4.5.0 | ok, 4.0.6 |
| `session:theme-compatibility` | ok, contract 4.5.0 (the wave is on) | ok, 4.0.6 |
| `keymap:selection-keys` | ok, "Omarchy's screenshot selection keys are left out of the Keymap" | ok, "No screenshot selection table in this Omarchy" |

In the source, `TESTED_VERSIONS` is 4.0.6 and 4.5.0, the notification and
theme contracts are named 4.5.0, and the installer, doctor and plugin READMEs
agree. The root README still said 4.5.0-rc2 at `056ea04`; `f32d2d7` fixes
it on main.

## c — transient notifications

**4.5.0.** I made one migration pending by moving its done-marker aside and
restored it afterwards. I then ran Omarchy's own reminder
(`omarchy-migrate-notify.service`, the one the session starts) followed by
`omarchy restart shell` five times: three with DND turned on by the real
Super+Ctrl+Alt+comma key, two with it off.

- Each run showed one "Pending Omarchy Migrations" card (critical, from
  `omarchy-action`), with DND on too, as DESIGN §8.3 allows. The reminders
  never stacked; each capture shows exactly one card.
- The reminder never entered WULING's store (`live` or `history`) and never
  reached Comms, after any restart.
- A normal `notify-send` was kept as usual. It sat in `live` while shown,
  moved to `history` and Comms when it expired (6–10 s), and was still in
  Comms after a later shell restart.
- I also ran two real logouts and logins (WULING's power menu, LOGOUT held,
  password typed at the greeter) with the migration pending. The reminder
  showed once at each login, and the store held no copy of it.

**4.0.6** keeps the earlier rule (`kept()` is true). The same five runs left
five copies in `live`, stacked on screen. Omarchy 4.0.6's own shell does the
same: in a control after `wuling uninstall`, three runs gave three stacked
native cards and three files in its store. So WULING follows Omarchy on both
versions.

## e — the bar under a full-screen window, and tooltips

I made a foot window full screen with Super+F. The window ran a script that
logs mouse reports, so I could tell from the file whether a click reached it.
Each click below was a real pointer click on the bar's 02 workspace button.

| Case | 4.5.0 | 4.0.6 |
|---|---|---|
| Full screen | click goes to the window, workspace stays 1 | same |
| Full screen, after `omarchy restart shell` (the bar is drawn above the window) | click goes to the window | same |
| No window, a tiled window, after toggling full screen off (at once and at +3 s), after closing the window | the bar switches to workspace 2 | same |
| Full screen, shell restart, then full screen off (at once and at +3 s) | click still goes to the window until the window closes | same |

The last row is not WULING. With `omarchy plugin disable wuling.bar` on
4.5.0, Omarchy's own bar behaves identically (its "2" button at the same
step). On 4.0.6, where WULING's full-screen rule is off, it happens too.
After the restart, Hyprland seems to keep sending the pointer to the former
full-screen window. A user clicks the bar after closing or refocusing that
window.

**Tooltips at scale 1.25.** I recorded at 60 fps losslessly from outside the
VM, hovered every bar item with the real pointer and looked at every changed
frame. On 4.5.0, "Allow Idle Lock & Screensaver" and the world clock
tooltip appear complete and sharp in a single frame at about 0.52 s. There is
no partial, mis-scaled or mis-placed frame before them. On 4.0.6 the same
tooltips (plus "Pending Omarchy Updates") also appear whole in one frame, at
0.47–0.52 s.

## f — the Keymap and Omarchy's screenshot selection keys

On 4.5.0 I added three binds of my own to `~/.config/hypr/bindings.lua`: one
described (`SUPER + ALT + F12`) and two bare Lua binds (`ALT + F11` and
`CTRL + RETURN`, the latter on a chord the selection table also uses).

- Before any selection, the Keymap had 253 rows, and OTHER listed both bare
  binds as "Lua binding · no description".
- Then I made one real region selection: Super+Ctrl+Print (OCR, which uses
  slurp; plain Print uses omasnap and never opens a selection) and a real drag.
  Afterwards `hyprctl binds` holds Omarchy's eight selection binds, so
  CTRL+RETURN is there twice. The Keymap still had 253 rows. Its only bare
  rows were my `ALT + F11` and my `CTRL + RETURN`; none of the eight was
  listed. I checked this by eye in the overlay, filtering for "lua" and
  "return".
- **Gate mismatch.** I ran the Keymap and doctor against a copy of Omarchy's
  tree with one line of the `selection_keys` table changed
  (`OMARCHY_PATH` pointing at the copy). The Keymap then had 260 rows, with
  all eight chords under OTHER and CTRL+RETURN merged with my identical row.
  Doctor kept `keymap:selection-keys` ok, with the information message that
  the table differs and its keys are listed under OTHER.

On 4.0.6 nothing is skipped. The Keymap had 231 rows with both bare binds
listed. 4.0.6 also binds selection keys while slurp is open, but with
descriptions and not from a `selection_keys` table, so the gate never applies.

## Not WULING, but in the way of a user

- **Omarchy 4.0.6 removes a user's bind on a selection chord.** After one
  region selection on 4.0.6, my own `CTRL + RETURN` was gone from Hyprland,
  and pressing the real key did nothing until `hyprctl reload`. The
  control without WULING behaved the same. During the selection Omarchy added
  "Capture entire screen" on that chord; afterwards neither bind was left.
  Omarchy's comment in `utilities.lua` says the handles are removed one by one
  so that a user's same-key bind survives. Under Hyprland 0.56.2 they don't.
  On 4.5.0 my bind was still listed after the selection; I did not press it
  there.
- The bar input after full screen and a shell restart (e, above).

## Observation older than phase I

**P3: the TERMINAL button's label is blank for about 50 ms at hover start.**
At 1.25 the label and icon vanish for three frames, from about +0.05 s
until the highlight starts fading in at about +0.10 s. The same frames
appear on 4.5.0 and on 4.0.6, so this predates `1de6536`. The other bar
buttons don't do it.

## Limits

One output, llvmpipe in a VM, no hardware. The gate mismatch was made
with a copied Omarchy tree through `OMARCHY_PATH`, not a real later release,
so doctor's other checks under that override (the notifications writer
reads the copied tree) were not judged. Logout and login were tested on
4.5.0 only. The theme wave's play rate, G-V7 and the full G and H matrix are
left to the next round, as instructed.

## Cleanup

On both VMs I restored `bindings.lua`, the migration markers and the scale,
and ran `wuling uninstall --yes`. The fixture-teardown step of my cleanup
script did not apply on these disks, since no hardware fixtures were started.
4.5.0 returned to Omarchy's bar, notifications and Tokyo Night. On 4.5.0 the
uninstall kept the release directory as changed: one of my own probes had
imported WULING's modules from the release without `-B` and left `.pyc`
files. WULING's entry points set `dont_write_bytecode` and didn't do this.
I removed that directory by hand. The inventory then differed from
before-install only in the harness's sound override, my bindings fixture
(restored) and session logs. Each VM ended with a normal shutdown, my
container removed, the verified checkpoint and firmware restored, and
`verified-clean-b` the only snapshot. The runtime image
`wuling-verifier-c186-runtime:1` is kept.

# Second half

Inbox v188; WULING `462e9c7` (the theme wave's per-switch recheck is
`6916b61`). Later commits on main (`8031022`, `dde370e`, `89ee3bd`) are not
included. Same two VMs, each from its verified checkpoint, one at a time,
WULING from a clean `git archive` with `./install`, doctor clean on both.
Real QMP keyboard and pointer. Wave recordings are 60 fps lossless x11grab
of the VM display from outside the guest, analyzed as in phase H: the bar is
cut into 16 cells, each frame's cells are classed old or new, and any old cell
after a new one counts as a violation. Strips and full frames were checked
by eye.

## Result

- **Theme wave on 4.5.0: safe, and it rarely plays.** It played 6 of 117
  switches (5%): 4 of 100 in a run of switches and 2 of 17 recorded on the
  four routes. Every skip is clean: the switch is Omarchy's own, no WULING
  cover is drawn, no wave layer stays, and no old frame appears after the new
  one in any recording. The per-switch recheck runs in the shell in 3–10 ms
  as claimed; a changed byte makes the full gate run and turns the wave off.
  The implementer saw a higher rate (15 of 120); in my VM the native palette
  usually arrives before the cover is up.
- **4.0.6:** the wave played 50 of 50 in the run and 15 of 16 on the routes.
  The one skip, through Omarchy's picker, was clean.
- **G-V7:** the shell still grows by about 0.05–0.07 MiB per Terminal open on
  4.5.0. The two key points from `research/phase-i.md` hold only in part: with
  battery fixtures, one page is flat and Performance/Power alternating grows,
  but slowly (+4.5 MiB in 200, not +27). Without batteries, one page grew as
  much as alternating. The panel host maps a fresh `omarchy-keyboard-panel`
  layer on every open and releases it on every close.
- **G/H matrix on 4.5.0:** no finding. Every reachable page was entered and
  left by keyboard and by mouse. The views are uncut in four themes, three
  languages and text size 16. Keymap, notifications, OSD, Dispatch and the
  power menu work by real input, and the same real-input pass on 4.0.6 also
  passes.

## Theme wave on 4.5.0

**Rate.** 100 `omarchy theme set` switches rotating the four WULING themes on
one shell, 2.5 s apart:

| | Played | Skipped | Skip reasons | Played per 25 | Switch time |
|---|---:|---:|---|---|---|
| 4.5.0 | 4 | 96 | late palette 50, late capture 46 | 1, 2, 0, 1 | 3.125 s median, max 3.307 |
| 4.0.6 (50 switches) | 50 | 0 | | 25, 25 | 3.362 s median, max 3.408 |

Timing from each switch's own record on 4.5.0 (17 recorded switches): the
gate recheck finished at 3–10 ms (median 4), the lock check at 30–93 ms and
the capture at 34–81 ms. A skip was decided at 81–241 ms. In the two played
switches the palette arrived at 151 and 195 ms, the wave started at 235 and
295 ms, and the switch was done by 661 and 720 ms. On 4.0.6 the palette
arrives at 400–830 ms, which leaves the cover plenty of time.

**Routes, recorded.** Omarchy's picker (Super+Shift+Ctrl+Space), the theme
menu (Super+Space), Config's THEME and `omarchy theme set`, by keyboard,
landing on WULING and native themes:

| Route | 4.5.0 played | 4.0.6 played | Old after new (both) | Largest frame gap |
|---|---:|---:|---:|---|
| Picker | 0 of 3 | 7 of 8 | 0 | 24 ms / 35 ms |
| Theme menu | 2 of 3 | 2 of 2 | 0 | 55 ms / 34 ms |
| Config THEME | 0 of 3 | 2 of 2 | 0 | 22 ms / 17 ms |
| `omarchy theme set` | 0 of 8 | 4 of 4 | 0 | 22 ms / 17 ms |

By eye:

- **Played.** The 16 × 9 cells sweep down with the yellow ghost outline, and
  the bar ends fully new; this is the same as phase H's 4.0.6 wave.
- **Skipped on 4.5.0.** The bar flips in one or two frames, then the
  background changes in one frame. No WULING cover is drawn and no old frame
  returns.
- **Control.** With `session.theme false`, which gives Omarchy's own path,
  the change has the same shape: background in one frame, bar after, 0
  violations.
- **The 4.0.6 skip.** The capture was ready only at 489 ms, because Omarchy's
  picker was still on screen. The switch then fell back to Omarchy's slanted
  wipe, with no cover and no old frame after the new.

**Content gate.** With the shell running, I changed one character of the
installed `/usr/share/omarchy/bin/omarchy-theme-set` (`theme` to `thEme` in
its summary comment), as root in the VM:

1. `wuling doctor` at once: `session:theme-compatibility` fails, "Installed
   theme modules do not match a tested contract".
2. First switch: the in-shell digest differed, so the full gate started.
   That switch was skipped as late palette at 158 ms, before the gate
   answered, and no cover was drawn.
3. Second switch: skipped `unknown-contract`.
4. Every later switch: no attempt at all. Omarchy changed the themes, with
   no wave.
5. With the byte restored (same SHA-256 as the contract), doctor passes. The
   wave stays off until the shell restarts; after `omarchy restart shell` it
   attempts again, with the fast recheck at 3–7 ms.

**Memory over the 100 switches (4.5.0):** 312.6 MiB before; medians per 25
switches 339.0, 351.5, 352.7, 356.6; idle after 355.6. FDs 209–211, one
shell process throughout. This is the warm-up shape phase H measured on 4.0.6.

## G-V7 on 4.5.0

Each cycle runs `wuling terminal open PAGE`, waits 0.45 s, checks the page
and the `omarchy-keyboard-panel` layer, closes, and 0.3 s later samples the
shell's PSS+SwapPSS. Idle is 21 s of samples after the last close. Two
sessions, each on a freshly restarted shell:

| Session | Run | Before | Medians per 50 cycles | Idle after | Slope, last 100 (MiB/cycle) |
|---|---|---:|---|---:|---:|
| No battery fixture | Performance ×200 | 321.2 | 321.9, 325.4, 327.7, 330.8 | 331.5 | 0.055 |
| | Performance/Power ×200 | 337.3 | 336.0, 335.7, 338.2, 339.6 | 342.2 | 0.037 |
| | Power ×200 | 347.9 | 343.9, 342.8, 344.9, 345.9 | 353.1 | 0.025 |
| | Performance/Power ×200 | 360.5 | 350.3, 360.1, 363.2, 364.2 | 365.1 | 0.027 |
| | Performance ×200 | 372.4 | 369.2, 371.7, 373.5, 375.1 | 376.7 | 0.037 |
| Synthetic UPower, three packs (as the implementer's) | warm-up Performance/Power ×50 | 325.9 | 334.1 | 344.7 | |
| | Performance ×200 | 344.3 | 349.5, 353.0, 352.8, 353.2 | 359.1 | 0.009 |
| | Performance/Power ×200 | 358.6 | 356.0, 355.5, 358.5, 360.5 | 366.9 | 0.043 |
| | Power ×200 | 370.7 | 362.6, 366.0, 365.6, 365.2 | 372.2 | 0.027 |

- **One page flat.** Yes with batteries: Performance and Power each hold
  after their first 50 cycles. Without batteries, a warm Performance run grew
  about as much as alternating did, so I can't confirm that one page is
  always flat.
- **Two pages alternating grow.** Yes, but slowly: about 4.5 MiB in 200
  cycles (0.03–0.04 MiB per cycle). The implementer's 466 → 493 MiB did not
  reproduce here.
- **Overall.** The shell went 321 → 377 MiB over 1,000 opens in the first
  session and 326 → 372 MiB over 650 in the second, about 0.05–0.07 MiB per
  open. Each run's idle sat 5–8 MiB above its last cycles, so the growth
  doesn't show only right after a close. G-V7 stays open on 4.5.0, with
  roughly the rc2 rate.
- **The panel host.** In all 1,650 opens of complete runs, exactly one
  `omarchy-keyboard-panel` layer was mapped while open, and none was left
  after closing. Two addresses alternate. FDs stayed 203–209, and the
  shell's GPU buffer mappings went down as well as up (for example 252 →
  212). This matches the implementer's finding: a fresh surface per open,
  released on close.

Once in about 2,250 state calls, `omarchy-shell`'s 2 s IPC timeout expired.
The shell logged the peer closing, and kept running as the same process. I
added one retry and reran; the rerun had no miss.

## G and H on 4.5.0, reduced to what differs from rc2

**Ten pages by real input.** Each page was entered from the overview opened
by Super+Ctrl+G, by keyboard (Down to the control, Enter), and left with
Left or Backspace, then Esc. Each was also entered by mouse, from the
overview opened by clicking the bar's TERMINAL cell: a click on the control,
a click on BACK, and an outside click to close.

| Page | Entry | Crumb | Keyboard | Mouse |
|---|---|---|---|---|
| System | user name chip | 02 TERMINAL › SYSTEM | ok | ok |
| Config | ⋮ | 02 TERMINAL › CONFIG | ok | ok |
| Calendar | clock | 02 TERMINAL › CALENDAR | ok | ok |
| Power | LINK's POWER tile | 03 LINK › POWER | ok (Left selects a profile, Backspace returns, as documented) | ok |
| Audio | volume icon | 04 LEVELS › AUDIO | ok | ok |
| Performance | CPU | 06 TELEMETRY › PERFORMANCE | ok | ok |
| Comms | "+N more" | 07 COMMS › HISTORY | ok | ok (after scrolling) |

Each entry opened the named page, with the crumb matching the overview's
section number. Each return reached the overview, and each Esc or outside
click closed the Terminal. The VM has no Wi-Fi, Bluetooth or Tailscale, so
their overview controls are hidden, as DESIGN says. `wuling terminal open
wifi` and `bluetooth` show "Unavailable" and "No devices". `tailnet` refuses
with "Tailnet is not installed". These pages were verified with fixtures on
rc2, and 4.5.0 didn't change them.

**Themes, languages, text size.** At 1366×768 I captured the ten views
(Tailnet excluded, plus the bottoms of System, Comms and Config) in all four
themes × English, Traditional and Simplified Chinese: 144 captures. I also
captured 640×480, 3840×2160, 1920×1080 at 1.25, and 800×600 at text size 16:
192 views in all, checked by eye on contact sheets, with no overlap,
overflow or misplaced control. Separately, the Terminal's own `truncated()`
over the overview and every page, field and HUD presets, text sizes 12 and
16, three languages at 1366×768: 0 of 120 views cut. At size 16 the panel
grows to 496 px, so the size does apply.

**Real input, once each (4.5.0 and 4.0.6):**

- **Notification:** a card shown, then dismissed with Omarchy's Super+comma;
  `live` went 1 → 0.
- **OSD:** the volume keys show WULING's OSD.
- **Dispatch:** Super+D opens it; typing filters; the first Esc clears and
  the second closes; Enter on "Foot" launches it and closes Dispatch.
- **Power menu:** Super+Esc opens it; Right moves the selection; Esc closes.
- **Keymap:**
  - Super+Ctrl+/ opens it, and typing filters ("volume" leaves the four
    volume binds).
  - Super+Return while it is open runs nothing (no window).
  - Esc clears, then closes.
  - An outside click closes it.
  - After closing, Super+Return opens a terminal.

## Limits

One output, llvmpipe in a VM. The wave rate depends on how fast this VM
renders the cover against Omarchy's palette; the implementer's VM and real
hardware may differ, and kujira's rate is still unknown. The G-V7 runs use
`wuling terminal open`, as G-V7 always has, with the panel layer and the
pages checked on every cycle. The keyboard and mouse pass covers the seven
pages this VM can reach. The gate change was made as root inside the VM to
stand in for a changed Omarchy file.

## Cleanup

The battery fixture was stopped and UPower restored, the gated file's
original byte restored (checked by hash), and text size, language and theme
returned. WULING was uninstalled on both VMs; the inventories differ from
before-install only in the harness's sound override and dconf's user
database. Each VM ended with a normal shutdown, my container removed, the
verified checkpoint and firmware restored, and `verified-clean-b` the only
snapshot. The runtime image is kept. kujira was not touched.

## Button hover (inbox v189, `89ee3bd`)

`dde370e` turns a flat plate's ink at the fade's midpoint. Chamfered plates
keep the immediate change. Method:

- WULING `89ee3bd`, installed fresh on each VM.
- Recorded at 60 fps from outside the VM. The pointer was moved by real QMP
  events to a corner of each button, clear of the label, held 0.7 s, then
  moved away. Each transition was repeated three times.
- In every frame I measured the label's contrast against its own plate: WCAG
  luminance ratio of the label's most distinct 6% of pixels against the
  box's median. For comparison, I measured the same buttons on `462e9c7`
  (before the fix), updated over the top on the same 4.5.0 VM.
- I also looked at zoomed strips of every distinct frame.

Lowest contrast during the 300 ms after the pointer enters or leaves, with
rest values (rest → lowest → hovered):

| Button | Before the fix, 4.5.0 `wuling` | After, 4.5.0 `wuling` | After, 4.0.6 `wuling` | After, paper themes (both versions) |
|---|---|---|---|---|
| Bar TERMINAL cell, in | 9.5 → **1.0** (4 frames under 1.6) → 12.3 | 9.5 → 2.0 → 12.3 | 9.5 → 2.0 → 12.3 | 7.7 → 3.3 → 12.0 |
| Bar TERMINAL cell, out | 12.3 → 1.2 → 9.5 | 12.3 → 2.7 → 9.5 | 12.3 → 2.7–4.6 → 9.5 | 12.0 → 2.9 → 7.7 |
| Terminal BACK, in / out | 1.0 / 1.2 | 2.1 / 2.8 | 2.1 / 2.8 | 3.3–3.6 / 3.1 |
| Config segments, in / out | 1.1 / 1.2–1.3 | 2.1–2.3 / 2.7–2.8 | 2.1–2.3 / 2.7–2.8 | 2.9–3.6 / 2.8–3.0 |
| Bar workspace 02, in | 3.5 → **1.0** (5 frames) → 2.2 | 3.5 → **1.2–1.4** (1–2 frames) → 2.2 | same | 2.5–2.7 → 1.4 → 1.9 |
| Bar workspace 02, out | 2.2 → 1.6 (0–1 frame) → 3.5 | 2.2 → **1.3–1.5** (1–2 frames) → 3.5 | same | 1.9 → 1.4–1.6 → 2.5–2.7 |

By eye, the TERMINAL cell, BACK and the Config segments now show their label
in every frame: as the plate fades, the label stays light until the plate is
mid-gray, then turns dark. The before-fix blank frames are gone. HUD themes
give the same result for BACK and the segments, which are flat there too.

**Unchanged, as intended.** The HUD TERMINAL cell and the menu cell are
chamfered accent plates, and hovering doesn't change them at all, before or
after: the label holds 12.2:1 (HUD) and 11.6:1 (HUD paper) in every frame.
Dispatch's tabs and rows and the power cards aren't `Kit.Button`s and don't
react to hover on either version; the only change on screen is the cursor
itself.

### P3: a workspace cell's label still nearly disappears for a frame or two

**Workspace cells are only partly fixed.** An unfocused workspace's label is
dim at rest (3.5:1), and its hover plate settles at mid-gray, not paper, so
hovered it reads only 2.2:1. When the ink turns at the fade's midpoint, that
plate is still dark. In all four themes, on both versions:

- In, "02" falls to 1.2–1.4:1 for one or two frames (about 0.10–0.12 s after
  the pointer arrives).
- Out, it falls to 1.3–1.6:1 for one or two frames (about 0.07–0.09 s).

Before the fix, hover-in was worse (1.0:1 for five frames). Hover-out was
slightly better (one frame at about 1.6:1). The zoomed strips show the same
thing: at those frames, "02" is a dark shape on a dark plate, hard to make
out. It lasts 17–33 ms, so it's a P3, but the rule "the label is visible in
every frame" isn't met for workspace cells.
