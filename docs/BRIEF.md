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
The owner sees the result after C and F. **Rebooting kujira always asks the owner first.**

### B — Theme and foundations

- `tokens/` from `design/src/tokens.css` and `design/theme-draft.py`; delete `theme-draft.py` once `tools/` replaces it.
  Generation is deterministic; a check regenerates the text files into a temporary directory and compares bytes, and compares
  images through a manifest of hashes. Contrast is checked at generation: text at least 4.5:1, a row's detail text as Omarchy
  actually draws it.
- `theme/` with the four themes of DESIGN §2: `colors.toml`, `shell.toml`, `icons.theme`, `light.mode` for PAPER,
  `backgrounds/` with all three images of DESIGN §2 (`design/assets/bg-*.jpg`, named so Omarchy's sort puts that preset's first
  image first), `unlock.png` (`design/assets/unlock-*.png`), `preview.png` and `preview-unlock.png` from real captures, and the
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
  current background alone (Omarchy moves to the next image when a theme is set again). First apply shows the preset's first image, and
  Omarchy's switcher reaches all three. Backgrounds checked at 1920×1080, 16:10, 3:2 and 21:9 on a real output. The boot unlock screen seen
  for real in a VM (`plymouthd`, `plymouth show-splash`, `plymouth ask-for-password`). Then on kujira: theme applied; `omarchy-plymouth-set-by-theme wuling` run there, seen at the next owner-approved
  reboot.

### C — Bar and Terminal

`kit/`, `plugins/bar`, `plugins/terminal`, `plugins/focus`. Start from `research/spikes/bar-host/` and `research/bar-host-contract.md`.
Host hardening per the contract: overflow, complete hover, shell-hidden transitions, duplicate ids, keyboard review. Terminal's data
commands first, then the QML.

**Acceptance:** the contract's interaction matrix on real input (QMP in VMs; on kujira through its actual hardware: battery,
Bluetooth, tray apps, brightness, which VMs lack). Four edges, two outputs, 1366×768 and 1920×1080, fractional scale, hotplug.
Both presets, both palettes. `omarchy bar` commands. Bar load failure falls back. Switching either plugin off leaves Omarchy's own.
Budget on kujira. **Report to the owner.**

### D — Notifications and OSD

`plugins/notifications`, `plugins/osd`. **Acceptance:** real volume and brightness keys, `notify-send` with every urgency and
actions, every key in DESIGN §9, a toast click running `omarchy-exec-argv` with a hostile argument, Omarchy's crash notification path
(through `omarchy-crash-watch`), DND and its bypass rules, history into the Terminal. Omarchy's scripts that call them
(the caller tables in the research). Handoff in both directions with no duplicate handlers. Both versions.

### E — Dispatch and power menu

`plugins/dispatch`, `plugins/power`, the bindings block, the menu extension entry. **Acceptance:** every mode on real input, launching a
terminal app and an app with field codes, clipboard paste, `omarchy agent prompt` with no agent configured. Power: every route, holds
and cancels **without completing reboot, shutdown or logout on kujira**; locked and unlocked; removal restores Omarchy's System.

### F — Sound and soak

`plugins/sound`, login music (off by default), localisation complete. **Acceptance:** cue overlap bounded, tests on a private null sink
with no physical sound. A 24-hour soak on kujira with PSS, CPU and handles flat. An Omarchy update survives, overrides intact. Partial
enable/disable of every part. **Final report to the owner.**

## Verifying

Start from the research's method: a disposable VM from the clean checkpoint, real input through QMP, before-and-after config inventories,
captures inspected by eye. IPC success alone proves nothing: check the surface and the state. kujira is a test box, but
it is shared with the owner's remote sessions: never touch them, never suspend or log out, and never leave it locked.
