# Updating 4.0.6 with WULING to Omarchy 4.5.0

Inbox v186; WULING `a8edfaa` (the released state); Claude verifier. Question:
someone on Omarchy 4.0.6 with WULING accepts Omarchy's own update to 4.5.0
today. What happens to the desktop?

Method: the 4.0.6 VM restored from its verified clean checkpoint each time,
WULING installed from a clean `git archive` of `a8edfaa` with `./install`
(doctor clean), the update started the way a user does, with real QMP input:
Super+Space → Update → Omarchy, Enter on Omarchy's "Continue with update?",
the password typed at its sudo prompt. At each moment I captured the screen
and ran a checklist with real keys and pointer, read `wuling doctor`, and kept
a guest-side log every 3 s (layers, shell process and ping, Omarchy version,
pacman). An external 2 fps recording covered each update. Raw evidence is
private (`wi2/verifier-claude-v186`).

Three runs:

| Run | WULING | Network | Result |
|---|---|---|---|
| A | yes | direct | Omarchy 4.0.6-1 → 4.5.0-3, kernel 7.2.8 → 7.2.15, all 218 migrations; then "Something went wrong" in the last steps (below); rebooted by hand |
| B | yes | GitHub through the server's proxy | complete in 2.8 min, Omarchy's "Linux kernel has been updated. Reboot?", answered No (official shell restart), rebooted later |
| C (control) | no | direct | stopped after the packages and first migrations, to see Omarchy's own keys in the same window |

Hyprland (0.56.2-4) and Quickshell (0.3.2.r7) are unchanged by this update.

## Answer

**The desktop never breaks in a way that stays broken, and nothing in it is
WULING's.** The bar, the shell, lock and login, WULING's Terminal, Dispatch,
Keymap and notifications work at every step. There is one window, from the
moment pacman installs 4.5.0 until the shell is restarted or the machine
reboots, where three of **Omarchy's own** keys do nothing: Super+Space
(Omarchy menu), Super+Esc (system menu, which WULING's power menu answers) and
the volume keys. The control without WULING loses the same three keys at the
same point, so this is Omarchy's update, not WULING. Cause, from the files:
4.5's `bindings.lua` turns these keys into shell actions (`{ menu = "root" }`,
`{ menu = "system" }`, `{ audio = "raise" }`); Hyprland loads the new bindings
during the update while the shell still running is 4.0.6's, which doesn't
answer them. WULING's own keys are commands and keep working.

When the update finishes, Omarchy closes that window itself: Yes to its reboot
question reboots; No restarts the shell. Both end on a working WULING desktop.
When the update stops early (run A, a network failure), Omarchy doesn't
restart the shell and the window stays until the user reboots. Super+Esc
doesn't work then, but WULING's Terminal (Super+Ctrl+G) → REBOOT opens the
power menu, and holding REBOOT reboots.

After 4.5.0, `wuling doctor` exits 1 with one failing check,
`session:theme-compatibility`: the theme wave is off because 4.5.0's theme
modules match no tested contract. Omarchy changes themes at once, with no
wave, no cover and no wave attempt counted. No other part falls back:
the bar, Terminal, notifications (its gate matches the 4.5.0-rc2 contract),
OSD, Dispatch, power menu, Keymap, session and sound all stay WULING's.
The `omarchy` check reports 4.5.0-3 as not tested but passes. `wuling
uninstall` on the updated system gives back a clean native 4.5.0 desktop
(Omarchy's bar, menu, OSD and system menu, theme restored to Tokyo Night).

So kujira could take Omarchy's own update now, with this one caveat: until it
reboots or the update ends normally, Omarchy's menu, system menu and volume
keys are dead, as they would be without WULING. The reboot is the owner's.

## Each moment

| | Before (A) | During pacman (A) | During migrations, 4.5.0 installed (A) | Update stopped, no reboot (A) | Reboot prompt (B) | After No: shell restarted (B) | After reboot (A, B) |
|---|---|---|---|---|---|---|---|
| Bar | yes | yes | yes | yes | yes | yes, after a gap (below) | yes, plus 4.5's dock layer |
| Super+Return (Omarchy) | yes | not tried | not tried | yes | not tried | yes | yes |
| Super+Space Omarchy menu | yes | yes | **no** | **no** | not tried | yes | yes |
| Terminal Super+Ctrl+G | yes | yes | yes | yes | not tried | yes | yes |
| Notification popup | yes | yes | yes | yes | not tried | yes | yes |
| Volume key and OSD | yes | yes | **no** (volume unchanged) | **no** | not tried | yes | yes |
| Dispatch Super+D | yes | yes | yes | yes | not tried | yes | yes |
| Power menu Super+Esc | yes | yes | **no** | **no** (Terminal's REBOOT opens it) | not tried | yes | yes |
| Keymap Super+Ctrl+/ | yes, 228 rows | yes | yes, 246 rows (4.5 bindings) | yes | not tried | yes | yes |
| Theme switch | wave plays | not tried | not tried | changes, no wave | not tried | changes, no wave | changes, no wave |
| Lock and unlock (real password) | yes | not tried | not tried | yes | not tried | yes | yes |
| Arrival and Exit previews | yes | not tried | not tried | yes | not tried | yes | yes; real Arrival after login |
| `wuling doctor` | ok | ok | theme-compatibility | theme-compatibility | theme-compatibility | theme-compatibility | theme-compatibility |

"Not tried" during the update means keys that could close the update window,
answer its prompt or switch themes under pacman were left alone; at the
reboot prompt any stray Esc would have answered it. "No" was seen on screen
and in the layer list; the same three keys also failed in control C at that
point, and worked in C before the update.

Over run A's 51 minutes the guest log never saw the bar missing or the shell
failing to answer, and the shell was the same process throughout. pacman
had installed 4.5.0 about 25 s after the password; the doctor's check turned
about 50 s after it.

**Reboots.** Run A rebooted through WULING's power menu, run B through
Super+Esc after the shell restart. Both recordings show the power menu, a
dark Exit frame, firmware and Omarchy's boot logo, Omarchy's greeter
(unchanged), the typed login, about 2.5 s of black, then WULING's Arrival and
the desktop.

**Shell restart (run B, answering No).** Omarchy prints "Restarting shell"
and the update ends with status 0. The recording shows the update window on
black for about 0.5 s, then about 2.5 s of black, then the WULING desktop at
about 3.5 s. Timed afterwards on the same VM with `omarchy restart shell`:

| | Background back | Bar back |
|---|---:|---:|
| With WULING (3 runs) | 0.71, 0.77, 1.36 s | 2.37, 2.37, 4.40 s |
| Native, after `wuling uninstall` (3 runs) | 0.66 s | 0.66 s |

WULING's bar comes back 1.7–3.7 s after Omarchy's would. Not broken, but the
user sees a background without a bar for that long on each official shell
restart, every update included.

## Not WULING, but in the way of a user

- **The update stops if a tool download fails.** In run A, Omarchy's last
  steps ("Update mise tools") spent 30 minutes downloading `codex` from GitHub
  at 34 kB/s, timed out, and ended the update with "Something went wrong":
  no orphan cleanup, no reboot question, no shell restart. That speed is this
  server's direct route to GitHub. Run B, with the guest's user environment
  pointed at the server's proxy (`~/.config/environment.d`; pacman, which runs
  through sudo, still went direct), finished the same step in about a minute. A
  user with a failing network ends where run A did, with the three dead keys
  until a reboot.
- 4.5's bindings for Super+Space, Super+Esc and the volume keys depend on the
  new shell; Omarchy's own update leaves them dead until the restart.

## Limits

One output, llvmpipe in a VM, no hardware fixtures (no battery, Wi-Fi or
Bluetooth). The harness set WULING's sounds off before installing. The
recording is 2 fps, so short frames between samples are not seen; the guest
log samples every 3 s and missed the 2–4 s bar gap at the restart. The
reboot-prompt state in run B was recorded but not driven with keys (run A's
stopped state is the same shell with the same files and was driven).
The VM runtime image was rebuilt from the same Dockerfile this round
(QEMU 11.1.3, Mesa 26.2.6). kujira was not touched.

## Cleanup

Each run ended with a normal shutdown, my container removed, the verified
checkpoint and firmware restored, `qemu-img check` clean and
`verified-clean-b` the only snapshot. Run A and B uninstalled WULING first on
the updated system; run C never had it. The guest proxy file existed only in
run B's discarded state.
