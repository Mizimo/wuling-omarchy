# WULING for Omarchy — brief

How WULING gets built after the owner approved the design. What it looks like is in
[../design/DESIGN.md](../design/DESIGN.md); the owner's decisions are in [../design/DECISIONS.md](../design/DECISIONS.md),
and those bind everything here.

## Rules

- **Only Omarchy's extension points.** No edits to `/usr/share/omarchy`, no copied or forked Omarchy code, no sudo in
  the installer. Importing an installed module at runtime is allowed where this brief says so, behind a version check.
- **No Omarchy key is rebound.** The only additions are Super+Ctrl+G and Super+D.
- **Authentication stays Omarchy's.** Lock and polkit are themed, never replaced, never scripted around.
- **Clean public history.** No canon art, music, addresses, tailnet names, account names, credentials or personal data.
  Machine nicknames are fine. Evidence stays outside git.
- **English** in code, docs and commits.
- **Nothing to install.** At runtime use only what stock Omarchy ships: bash, Python 3 standard library (Omarchy's own commands use
  it, and it has `tomllib`), jq, Quickshell. `design/` and `tools/` may need more; a user never runs those.

## Repository

```text
AGENTS.md, CLAUDE.md     entry point for agents: ownership, rules, how to verify
agents/skills/           repository task guides: plugins, themes, verification
skills/wuling/           the skill installed for the user's own agents
tokens/                  the one source: palettes, type, spacing, motion, sound, presets
tools/                   generate themes and style data, check everything, package
theme/<name>/            generated themes, committed so a clone needs no build step
kit/                     WULING's shared QML components
plugins/<part>/          one plugin each: manifest, entry points, README, i18n
bin/                     `wuling` and its commands, with `# omarchy:`-style metadata
sounds/                  cues
fonts/                   the fonts Omarchy doesn't ship, with licences
install                  the installer
tests/                   checks that need no display; VM acceptance
```

Decide how plugins get the kit (a plugin's symlinks fail `omarchy plugin validate`) and say why in `agents/skills/plugins.md`.

Each plugin's README states: entry points, state it owns, messages, settings, fallback, versions, how to remove it.

## Phases

Each phase ends with: checks green → the verifier tests in a VM and on kujira → the design lead approves → pushed.
The owner sees the result after C and F. **kujira is not rebooted** (DECISIONS, 2026-11-02): the boot screen and real logins are judged in VMs and reported as unseen on real hardware.

### B — Theme and foundations

- `tokens/` from `design/src/tokens.css`. Generation is deterministic; a check regenerates the text files into a temporary directory and compares bytes, and compares
  images through a manifest of hashes. Contrast is checked at generation and printed: primary and selected text at least 4.5:1; a
  row's detail text, which Omarchy always draws at 52 % of the text colour, at least 3:1, computed the way it is drawn.
- `theme/` with the four themes of DESIGN §2: `colors.toml`, `shell.toml`, `icons.theme`, `light.mode` for PAPER,
  `backgrounds/` with all three images of DESIGN §2 (`design/assets/bg-*.jpg`). Name them so Omarchy's sort puts that preset's first
  image first, and differently in each theme: Omarchy moves to the next image when the current file's name also exists in the new
  theme, so shared names would turn the survey line into the thin band on a palette switch. `unlock.png` (`design/assets/unlock-*.png`), `preview.png` and `preview-unlock.png` from real captures, and the
  preset's values for plugins. Confirm that file survives Omarchy's git-install filter.
- `wuling` command: `commands --json`, `theme resolve`, `config get|set`, `status --json` (stub), `doctor`. Stable JSON with a
  schema version.
- `fonts/` with their licences: Geist, Geist Mono, Barlow Condensed, and Material Symbols Sharp cut down to the glyphs WULING
  uses. CJK comes from Omarchy's own `noto-fonts-cjk`.
- `install` and `wuling uninstall`, covering themes, fonts (`~/.local/share/fonts/wuling`) and the skill now, and written so
  later plugins, the bindings block and the menu extension slot in:
  - Print the plan first: files, built-ins changed, keys added, required Omarchy version. Proceed on consent; `--yes` for scripts.
  - Record what it owns. Remove only that. Refuse an existing theme, plugin, skill or key binding it does not own.
  - Shared files get an owned block; a block the user edited is reported, not overwritten.
- `wuling` skill beside Omarchy's in each existing agent's skill directory, removal unlinks only ours. `AGENTS.md`,
  `CLAUDE.md`, `agents/skills/`.
- `tools/check`: tokens, generation, command metadata, shell syntax, privacy scan of staged files.
- **Acceptance:** fresh VM install and removal leaves a `~/.config` inventory diff of nothing. All four themes apply, on 4.0.6
  and 4.5. `wuling config set menu.selected fill` changes the real menu, survives re-applying the theme, and leaves the user's
  current background alone (Omarchy moves to the next image when a theme is set again). The first move to a WULING theme from any other theme, another WULING
  theme included, shows that preset's first image; after that, Omarchy 4.5's own memory of the user's choice for each theme stands (4.0.6 has
  none, so there it is always the first image). Omarchy's switcher reaches all three. Backgrounds checked at 1920×1080, 16:10, 3:2 and 21:9 on a real output. The boot unlock screen seen
  for real in a VM (`plymouthd`, `plymouth show-splash`, `plymouth ask-for-password`). Then on kujira: theme applied; `omarchy-plymouth-set-by-theme wuling` run there, seen at the next owner-approved
  reboot.

### C — Bar and Terminal

`kit/`, `plugins/bar`, `plugins/terminal`. Start from `research/spikes/bar-host/` and `research/bar-host-contract.md`.
Host hardening per the contract: overflow, complete hover, shell-hidden transitions, duplicate ids, keyboard review. Terminal's data
commands first, then the QML.

**Acceptance:** the contract's interaction matrix on real input (QMP in VMs; on kujira through its actual hardware: battery,
Bluetooth, tray apps, brightness, which VMs lack). Four edges, two outputs, 1366×768 and 1920×1080, fractional scale, hotplug.
Both presets, both palettes. `omarchy bar` commands. Bar load failure falls back. Switching either plugin off leaves Omarchy's own.
Budget on kujira. **Report to the owner.**

### D — Notifications and OSD

`plugins/notifications`, `plugins/osd`. The notification rules and argv checks come from the installed version's own modules, imported behind the
version check; if that fails the plugin does not take over, Omarchy's stays and `wuling doctor` says why. **Acceptance:** real volume and brightness
keys, `notify-send` with every urgency and actions, every key in DESIGN §9, a toast click running `omarchy-exec-argv` with a hostile argument, Omarchy's
crash notification path (through `omarchy-crash-watch`), DND and its bypass rules, history into the Terminal. A flood of 50; new toasts with the pointer on
the stack; a shell restart with toasts up; a verification code never reaching the file; `showHistory` with the Terminal off, the log off, nothing recorded
and under DND; removal deleting the history. Omarchy's scripts that call them (the caller tables in the research). Handoff in both directions with no
duplicate handlers. Both versions.

### E — Dispatch and power menu

`plugins/dispatch`, `plugins/power`, `plugins/session` with the exit sequence (DESIGN §8.9), the bindings block, the menu extension entry.
**Acceptance:** every mode on real input, launching a terminal app and an app with field codes, clipboard paste, `omarchy agent prompt` with
no agent configured. Power: every route, holds and cancels **without completing reboot, shutdown or logout on kujira**; locked and unlocked;
removal restores Omarchy's System. Exit: the action runs exactly once, at the designed moment, and still runs when the overlay is made to fail;
an action that doesn't end the session gives the desktop back after 10 s. Real logout, reboot and shutdown in a VM, seen through to the next screen:
the desktop must not reappear after the ink, and whatever shows in between is reported. With `wuling.osd` on, Omarchy's exit OSD never shows on the ink, and the
OSD works again after the give-back or when the `wuling.session` plugin is gone mid-sequence; a preview leaves the OSD alone; Omarchy's action and its environment
are exactly as with the plugin off. On kujira `wuling session preview exit` only.

### F — Arrival, sound and soak

Arrival (DESIGN §8.9), `plugins/sound`, login music (off by default), localisation complete. **Acceptance:** Arrival once per session, never on
a shell restart, theme switch, update, unlock or resume, nor on a first install or a first enable on a running desktop; skip by key and click, a held key ignored; a lock request during it; several outputs;
a cold shader cache, frame by frame from outside the VM, with no frame of wallpaper or WULING's bar before the ink (Omarchy 4.0.6's own empty bar may show first, see DESIGN §8.9); gone within 3.5 s; afterwards its windows and timers are gone, and repeated previews don't keep growing. Real logins in a VM; on kujira `wuling session preview arrival` only. Cue overlap bounded, tests on a private null sink with no physical sound. A 24-hour soak on kujira with no steady growth in PSS, CPU or handles, logging the notification writer's PID and exits. An Omarchy update survives, overrides intact. Partial
enable/disable of every part. **Final report to the owner.**

### G — The Terminal's pages

DESIGN §8.2, the owner's decision of 2026-11-04. Build in this order, each landing on its own: the Comms log and page, battery cells, the full Signal; then Performance, Power, Audio, System, Calendar; then Wi-Fi, Bluetooth, Tailnet; then Config. **Acceptance:** every item reaches its page by pointer and by keyboard and comes back; four themes, three languages, 1366×768, a narrow output, 4K and a fractional scale. A closed Terminal runs no collector, leaving a page stops its own, and 200 page cycles show no steady growth. A failing action stays on its page with the old state. Network actions on simulated radios in a VM (`mac80211_hwsim` with `hostapd`, `btvirt` or the like; a fixture `tailscale`): connect, wrong passphrase, forget, disconnect, a released hold, discovery stopped on leaving; the passphrase absent from every process's argv and environment, the journal and every WULING file. Audio on a private null sink, no physical sound. On kujira **read only**: each page opens and shows real data; no connect, disconnect, radio, tailnet, device or volume change, no sound. **Report to the owner.**

### H — Keymap and the theme wave

DESIGN §8.10 and §8.11. The wave starts with an experiment: can it run for every route to a theme switch, Omarchy's picker included, without a wrapper or a standing capture? Bring the answer before building it. **Acceptance:** Keymap lists every bound key, the user's own and a key that fits no group included, on both versions; filter, Esc, outside click; a listed key pressed there doesn't run; nothing stays loaded after closing. The wave plays on every route and output, in all four themes, seen frame by frame from outside the VM; the switch never waits on it, and a failed overlay still changes the theme; off with `session.theme` and with reduced motion; no steady growth over 50 switches. Partial enable with `wuling.keymap` off. On kujira only with the owner's word.

## Verifying

Start from the research's method: a disposable VM from the clean checkpoint, real input through QMP, before-and-after config inventories,
captures inspected by eye. IPC success alone proves nothing: check the surface and the state. kujira is a test box, but
it is shared with the owner's remote sessions: never touch them, never suspend or log out, and never leave it locked. Closing its lid must not
lock it. The owner sometimes uses it in person: read its state first, and the design lead asks before anything runs on its desktop. Notification history there is real: never clear it.

**Open until Omarchy 4.5 is stable (G-V7).** On 4.5.0-rc2 in the VM, moving between the Terminal's pages grows the shell by about 0.1 MiB a visit. No WULING object holds it: the memory sits in Qt's text and rendering resources (font faces, glyph caches, GPU buffers) under the VM's virgl and llvmpipe, and three WULING-side changes didn't stop it (`research/phase-g.2.md`). 4.0.6 holds flat. Accepted for the release candidate. When 4.5 is stable, its update first runs the 200-page-cycle test in the VM and, with the owner's word, on kujira's hardware; growth there reopens G-V7.
