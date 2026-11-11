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
| Renderer, vCPU | virtio-gpu, llvmpipe in the guest; 12 | same; 8 |
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
