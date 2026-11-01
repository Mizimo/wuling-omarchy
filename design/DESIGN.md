# WULING for Omarchy — design

What WULING looks like and how each part behaves. The decisions behind it are in [DECISIONS.md](DECISIONS.md); how it
gets built is in [../docs/BRIEF.md](../docs/BRIEF.md); what Omarchy allows is in
[../research/omarchy-shell-api.md](../research/omarchy-shell-api.md).

**The pixel source is `design/src/`.** `tokens.css` holds the values, `ui.css` and `proto.css` the components,
`mock.js` the structure. `design/render.sh` renders every screen to `design/mockups/`, and
`design/proto/dispatch.html` (from `proto-build.py`) is Dispatch, operable. Where this file and the mockups disagree,
ask. Everything shown is draft data: no real names, addresses or hosts.

## 1. Principles

1. **Daily use first.** A choice that looks good once and tires every day loses.
2. **Omarchy's logic.** Where things live and which keys do what stay Omarchy's. WULING rebinds none of Omarchy's keys.
   Its only new keys are Super+Ctrl+G (Terminal) and Super+D (Dispatch).
3. **Reuse before rewrite.** If Omarchy has the behaviour, host or call it. WULING writes what it draws, never a second
   copy of what Omarchy does.
4. **Every part can go.** Switching a part off leaves Omarchy's own in its place.
5. **Nothing moves at rest.** No idle animation, and no polling while a surface is closed.

## 2. Presets and palettes

A preset is an Omarchy theme, so Omarchy's own theme switcher (Super+Shift+Ctrl+Space) changes everything at once.

| Theme | Preset | Palette |
|---|---|---|
| `wuling` | `field` 照舊, the default | MIST 青霧 |
| `wuling-paper` | `field` | PAPER 宣紙 |
| `wuling-hud` | `hud` 更強烈 | MIST |
| `wuling-hud-paper` | `hud` | PAPER |

**Menus are the same in both presets**: Omarchy's menu, Dispatch, the power menu.

| | `field` | `hud` |
|---|---|---|
| Bar | 30 px, two-line labels, yellow menu cell | 32 px, 2 px rule, `EF` in the menu cell, `WS` tag, chamfered active workspace, yellow Terminal cell, vermilion power cell, 25 px clock |
| Terminal | Section numbers in yellow text | Yellow header band with hazard strip, yellow number chips, 56 px clock, taller level cells |
| Notifications | Hairline header | Raised header, yellow for important, three-line grip ornament |
| OSD | 316 × 46 px | 380 × 56 px, accent border, large yellow number, device in the label |
| Window focus | Yellow border | Yellow border + corner brackets + window tag (`wuling.focus`) |
| Background | Landscape and survey HUD, baked | The same plus scan lines, rulers and a readout, baked |
| Omarchy's panels | Hairline border | Accent hairline |
| Motion | §5 everyday | §5 plus entry choreography |

**Customising.** Values resolve in this order: defaults → the theme's preset → `~/.config/wuling/overrides.toml`.
`wuling theme resolve` prints every value with its origin. An update never writes to `~/.config/wuling/`. `wuling config set
<key> <value>` edits the file, so an agent can change it as easily as a person.

| Key | Values | Default |
|---|---|---|
| `labels` | `true`, `false`: the micro labels on bar cells | `true` |
| `menu.selected` | `edge`, `fill`: the selected row in Omarchy's menu. Omarchy reads this from the theme, so setting it regenerates WULING's installed themes | `edge` on MIST, `fill` on PAPER |
| `terminal.sections` | any of `clock link levels signal agent telemetry comms` | all |
| `sounds` | `essential`, `full`, `off` | `essential` |
| `motion` | `full`, `reduced` | `full` |
| `language` | `auto`, `en`, `zh-Hant`, `zh-Hans` | `auto` |
| `login_music` | a path | unset |

Add a key only when someone asks for it. Nothing here may need a restart beyond what Omarchy's theme switch already does.

**Other themes.** With any other Omarchy theme active, WULING's surfaces keep the `field` shapes and take colours from
that theme's palette (§3).

## 3. Tokens

One source (`tokens/`) generates the theme files and the plugins' style data. Nothing generated is edited by hand.

| Token | MIST | PAPER | From another theme's `colors.toml` |
|---|---|---|---|
| `ink-0` … `ink-5` | `#050707 #0A0D0C #0E1211 #141A18 #1B2321 #24302D` | `#D9DDD5 #E4E7E0 #ECEEE7 #F6F7F2 #E1E5DE #D3D9D1` | `darker_background`, `dark_background`, `background`, `lighter_background`, a mix, `selection` |
| `line`, `line-soft` | `#2B3734 #1C2523` | `#C3CBC3 #D8DDD6` | foreground mixed into background, 18 % and 10 % |
| `mist-6` … `mist-4` | `#4D5D59 #6F827D #93A49F` | `#A3ADA8 #7A8783 #5C6A66` | `muted`, `dark_foreground`, a mix |
| `paper-2` … `paper-0` | `#C9D3CE #E6EBE5 #F4F5EF` | `#2A3330 #121614 #121614` | `foreground`, `light_foreground`, `bright_foreground` |
| `fill` (yellow) | `#FEF700` | `#FEF700` | `accent` |
| `accent-ink` | `#FEF700` | `#121614` | `accent` |
| `on-accent` | `#0E1211` | `#121614` | whichever of background and foreground contrasts more with `accent` |
| `jade`, `vermilion`, `azurite`, `gold` | `#62D9A6 #E3432F #4C93C6 #C9A55C` | `#0F8A68 #C8361F #2F6F9E` (gold: ornament only) | `green`, `red`, `blue`, `orange` |

`fill` is for fills. `accent-ink` is the accent as text or a thin line. On PAPER yellow is only ever a fill.

**Omarchy's `colors.toml`** is generated from these (see `design/theme-draft.py` for the exact mapping, plus the ANSI
colours). PAPER's `accent` is the ochre `#6B5F00`, because Omarchy's templates use `accent` as text. Set
`hyprland_active_border` and `hyprland_inactive_border`. **Ship no `hyprland.lua`**: Omarchy's defaults are already
square and flat (gaps 10/5, border 2), and a git-installed theme would drop the file anyway.

**Omarchy's `shell.toml`** is in `design/theme-draft.py`, including the rule for its menu: a raised row with a yellow
left edge on MIST, a yellow fill on PAPER. Omarchy draws a row's detail text in the menu's text colour at .52, so a
white or yellow fill on MIST would hide it.

## 4. Visual language

- **Type.** Geist Mono for labels and readouts, Geist for body text, Barlow Condensed for the clock and large numerals,
  Noto Sans/Serif CJK for Chinese, Material Symbols Sharp for WULING's own icons. Sizes in `tokens.css`.
- **Shape.** Square. Chamfers 6/10/16 px on chips, cards and panels. 1 px hairlines. No radius, no shadow.
- **Labels.** Micro labels are 8–9 px uppercase mono and decorative: nothing important is only in a micro label.
- **Selection in WULING's own surfaces.** The plate inverts: `paper-0` ground, `ink-2` ink, 2 px yellow on the leading
  edge or foot.
- **Danger.** Logout, Reboot and Shutdown carry a hazard strip and need a long press.

## 5. Motion

Durations micro 90, short 160, base 240, long 420 ms. Easing snap `(.2,.8,.2,1)`, out `(.16,1,.3,1)`, linear for
veils. Staggers: rows 20, cards and tiles 45, sections 60 ms; at most 12 steps.

| Event | Everyday (both presets) | `hud` adds |
|---|---|---|
| Panel or menu opens | Backdrop cuts on; shell focuses in (150 ms), then content resolves in reading order; first row readable ≤ 320 ms | Sections stagger with a scan line |
| Closes | Wash-out, 120–140 ms linear | — |
| Hover | The plate changes at once, 100 ms linear | — |
| Selection | Fill settles from the leading edge, 240 ms snap | — |
| Value that accumulates (level, progress) | Segments fill cell by cell | Hot leading cell |
| Value that changes (telemetry, clock) | Swaps within a frame | — |
| Toast arrives | Slides 8 px and resolves, 200 ms | Strip slice |
| OSD | Reveals in 160 ms, leaves in 120 ms | Scan line |
| Focus moves (`hud`) | — | Brackets travel, 120–180 ms snap |
| Error | Vermilion border and a 300 ms shake | Glitch |

Input is never held hostage: a surface takes input from its first frame, and typing during the build applies at once.
Respect a `motion = "reduced"` setting: every entry becomes a 90 ms fade.

## 6. Sound

The cue set from the earlier WULING: short, dry, industrial and water, synthesised, ours. `open`, `close`, `toggle`,
`select`, `deny`, `notify`, `alert`, `tick` and `hover`.

- Played with `pw-play` from a small service, bounded overlap, never Qt Multimedia in the shell.
- Master at 60 % of system volume. `sounds = "essential"` (default: no `hover`, no `tick`), `"full"` or `"off"`.
- Do Not Disturb silences notifications. Omarchy's own menu has no events to hook and stays silent.
- **Login music** is off by default. The user supplies the file (`login_music` in overrides); it never enters the repo.
  One-shot at session start, skipped when muted or in DND.

## 7. Copy and language

Labels are `English · 中文`. The Chinese half follows the language (zh-Hant, zh-Hans); in English only the English
half shows, except the fixed marks 武陵 and 調度 and the Termination title 終止協議. Follow Omarchy: `~/.config/omarchy/language`
on 4.5, `LANG` on 4.0.6. Catalogs are per plugin (`en.json`, `zh-TW.json`, `zh-CN.json`), in the shape of Omarchy 4.5's.
Old §6 copy applies where a label is carried over.

## 8. Surfaces

### 8.1 Bar — `wuling.bar`

A `kinds: ["bar"]` plugin that draws the surface and layout, and hosts Omarchy's widgets from the registry. Read
`research/bar-host-contract.md`: it lists every member the host must provide. Follow `bar.layout`, so `omarchy bar …`
and `shell.json` keep working. All four edges. One window per output.

| Section | Cell | Drawn by | Behaviour |
|---|---|---|---|
| Left | Menu (`omarchy.menu`) | WULING: yellow cell with the mark | Left: Omarchy's menu. Right: terminal |
| | Identity (added) | WULING: `Wuling · 武陵` over the hostname, uppercase | — |
| | Workspaces (`omarchy.workspaces`) | WULING: cells `01`–`05` and up, as Omarchy lists them | Left: focus |
| | Window (added) | WULING: app label over title | — |
| Centre | Indicators, weather, keyboard, update | Omarchy's widgets | Theirs. Several hide themselves when idle |
| | Clock (anchor) | WULING's face over Omarchy's widget | Left: calendar. Right: format. Middle: timezone |
| Right | Tray, agents, Bluetooth, network, audio, monitor, power | Omarchy's widgets | Theirs |
| | Terminal (`wuling.terminal`) | WULING | Left: Terminal |
| | Power (added) | WULING | Left: power menu |

- **The clock is the one cell that layers.** Draw the label (Barlow Condensed 21 px; 25 in `hud`) and a date stack; put
  Omarchy's `omarchy.clock` over it, same box, `opacity: 0`. Bind the label to the widget's `displayText`; let the host
  own the width. Draw the open and hover states yourself, since the widget's are hidden. If the widget's internals
  change, fall back to showing the widget as it is. Vertical bars use the plain widget. Omarchy's default format is `dddd HH:mm`, so when the
  layout entry sets none the host passes `HH:mm`. Right-click still cycles Omarchy's formats and writes them to `shell.json`;
  show the date stack only while the format has no date of its own.
- **Host font** is Geist Mono. Icon glyphs fall back through fontconfig to Omarchy's Nerd Font, as tested.
- **Narrow screens:** below 1280 px drop the identity cell; below 1024 px also drop the date stack and window.
- **Not rebuilt:** drag to reorder, drag to move the bar. `omarchy bar move` and `omarchy bar position` do it.
  Double-clicking empty bar space toggles transparency, as Omarchy's does.
- **Hot-switching bars leaves stale IPC handlers** in 4.0.6, so install and removal restart the shell officially.

### 8.2 Terminal — `wuling.terminal`

The Field Terminal: one panel for what is going on and the switches used most. A `bar-widget` plugin using
`qs.Ui`'s panel, so it shares Omarchy's rules: one popout at a time, Esc, outside click, Tab to the next panel. It works
under Omarchy's own bar too. Key: **Super+Ctrl+G**. 372 px wide, full height minus the bar and 10 px gaps.

| # | Section | Shows | Source | Input |
|---|---|---|---|---|
| 02 | Terminal | Clock with seconds, date, zone, uptime | System | — |
| 03 | Link | Tiles: Wi-Fi, Bluetooth, Tailscale, DND, Night, Power profile. A tile with no hardware or service hides | Quickshell modules, Omarchy commands | Left: toggle. Right: Omarchy's matching panel |
| 04 | Levels | Volume, brightness, segmented | PipeWire, `omarchy-brightness-display` | Drag, wheel. Same OSD as the keys |
| — | Signal | Now playing. Hidden when nothing plays | MPRIS | Play/pause, previous, next |
| 05 | Agent | Per agent: plan, session and week meters, time to reset. Row: open the default agent. Hidden when no agent has usage | `~/.local/state/omarchy/agents/usage/*.json` | Row: `omarchy-agent --pick`. Agent: Omarchy's agents panel |
| 06 | Telemetry | CPU, memory, temperature with sparklines. Sampled only while open | `/proc`, hwmon | — |
| 07 | Comms log | Recent notifications | `wuling.notifications`' state file | Click: the notification's action |
| | Foot | Lock, Sleep; Exit, Reboot, Off | Omarchy's commands | Dangerous ones open the power menu |

Section numbers follow what is shown. Too tall: the body scrolls and the foot stays. Sections can be switched off in
overrides. Data comes from commands printing JSON (`wuling status --json`); the QML only displays it. Share one
collection schedule with Omarchy's agents panel; never start collectors per view, never log account contents.

### 8.3 Notifications — `wuling.notifications`

Replaces `omarchy.notifications` in the same process, through `disabledPlugins` and `omarchy.clonedFrom`. Omarchy's
scripts and keys reach it unchanged.

- **IPC target `notifications`, 4.0.6:** `dndState`, `toggleDnd`, `setDnd`, `isDnd`, `showHistory`, `clear`, `dismissAll`,
  `dismissOne`, `invokeLast`, `dismiss(summary)`, `ping`. **Added on 4.5:** `act`, `invokeAction(n)`, `keyboard`, `count`,
  `expand`, `probe`; do not assume the old names exist there. Also the service members `doNotDisturb` and
  `setDoNotDisturb` that the DND indicator reads, and `omarchy.indicators refresh`.
- **Levels:** normal has a jade edge. One with actions or a click command has a yellow edge. Critical has a vermilion edge.
- **Keep Omarchy's rules** (`shell/plugins/notifications/Service.qml`, `NotificationLogic.js`). Lifetimes: critical stays, low at
  least 5 s, normal at least 8 s, at most 30 s. DND lets through app `omarchy-action` and critical from `notify-send`. Ephemeral
  ones (`transient` hint, `notify-send`, `omarchy-action`) silenced by DND are not recorded.
- **Toast:** 340 px, header (`Comms · 通訊`, app, time, close), art, summary, body, actions, a life line. Stacks from the
  top right, on every output, as Omarchy does. While the Terminal is open on that output, toasts sit to its left.
- **Actions:** buttons as the app sends them. **Clicking a toast** runs its `omarchy-exec-argv` hint as argv, never through a shell,
  with the same validation as Omarchy's. Omarchy's crash notification (`omarchy-crash-watch`) has no action buttons and depends on this.
- **History** goes to `~/.local/state/wuling/notifications.json`. `showHistory` opens the Terminal at the log.
- Verify handoff by receipt and dismissal, not by the D-Bus name: it stays owned by the same process.

### 8.4 OSD — `wuling.osd`

Replaces `omarchy.osd`: IPC target `osd` with `show(payloadJson)`, `close`, `state`, `ping`, plus a panel entry with
`open`/`close` and `clonedFrom`, because Omarchy's panels call `shell.summon("omarchy.osd", …)`. The payload is
`omarchy-osd`'s: `icon`, `message`, `value`, `progressText`, `max`, `duration`. No keyboard focus, empty input mask, on
the focused output, centred above the bottom edge. Segmented level, number on the right; messages without a value show
text only.

### 8.5 Power menu — `wuling.power`

Omarchy's System entries as cards, with a long press for the dangerous ones. Reached by Super+Esc, the power key, the
bar's power cell, and System in Omarchy's menu, all through **one entry in Omarchy's menu extension file**
(`~/.config/omarchy/extensions/omarchy-menu.jsonc`): `system` gets an `action` that runs `wuling power toggle`, keeping
Omarchy's icon, label and `power-menu` alias, since omitted fields are cleared. No key is rebound; removing the entry
restores Omarchy's. See `research/spikes/system-route/`.

- **Entries:** read `system.*` from Omarchy's menu file and the user's extension when opening, with their `when` and `action`,
  so they follow updates (Suspend and Hibernate have `when` conditions). If that fails, fall back to Omarchy's seven in order.
- **Input:** ←→ select, letter keys jump (S L U H E R P), Enter runs. Logout, Reboot and Shutdown need a **0.8 s hold** of
  Enter or the pointer; release cancels. Esc closes. Other entries run at once.
- **Locked:** `wuling power toggle` asks `omarchy-shell lock isLocked` first and opens nothing while locked, so no menu
  waits behind the lock. This is not a security boundary.
- Searching "reboot" in Omarchy's menu still finds Omarchy's own entry and runs it without a hold. That is Omarchy's
  behaviour and stays.

### 8.6 Dispatch — `wuling.dispatch`

WULING's own launcher: an overlay plugin on **Super+D**, added in an owned block of `~/.config/hypr/bindings.lua`.
Super+Space and Super+Alt+Space stay Omarchy's. 680 × 456 px, centred on the focused output, with the vertical 調度 rail
and the 令 seal. Open `design/proto/dispatch.html` for everything below.

| Mode | Prefix | Lists | Enter |
|---|---|---|---|
| Apps 應用 | — | Desktop entries, by frecency; fuzzy match | Launch. Must honour terminal apps and field codes; `DesktopEntry.execute()` alone does not |
| Clip 剪貼 | — | `~/.local/state/omarchy/clipboard-history.json`, read only. Hidden if `omarchy.clipboard` is off | `omarchy-clipboard-paste-text --shift-insert --history-index N`; images `omarchy-clipboard-paste-file MIME PATH` |
| Run 執行 | `>` | The typed command, recent commands | Run in the default terminal |
| Calc 計算 | `=` | A live result from a small arithmetic parser (no `eval`) | Copy |
| Ask 詢問 | `?` | The question, recent questions | `omarchy agent prompt "<text>"` |

Tab and Shift+Tab cycle modes; a prefix switches at once. ↑↓ select, Esc clears then closes, outside click closes.
Exclusive keyboard focus; hold focus across the build. State in `~/.local/state/wuling/dispatch.json`.

### 8.7 Focus overlay — `wuling.focus`

`hud` only: corner brackets in the gaps around the focused window and a tag (`FOCUS · FOOT · WS 01`). A click-through
layer on each output, driven by Hyprland events, with no timer. Hidden for fullscreen and for no focus. With `field`
active it creates no window at all. Switching it off leaves the yellow border alone.

### 8.8 Theme only

Omarchy's menu, panels, clipboard, emoji, pickers, lock screen, polkit dialog and apps change through the theme alone;
their code and layout stay Omarchy's. The system font stays the user's (`omarchy font set`). **Boot unlock:** Omarchy's `omarchy-plymouth-set-by-theme` reads the theme's `unlock.png` and
colours. It needs sudo, so it is a separate, optional step.

**fastfetch.** The vertical 武陵 mark (`design/assets/fastfetch-logo.png`) is in the user's own config, not the theme: the
installer asks.

## 9. Keys

| Key | Does | Whose |
|---|---|---|
| Super+Space, Super+Alt+Space, etc. | Omarchy's menu and apps | Omarchy |
| Super+Esc, power key | Power menu, through the menu extension | Omarchy's binding |
| Super+, and family, volume and brightness keys | Notifications, OSD, through their IPC targets | Omarchy's binding |
| Super+Ctrl+A, B, D, P, Alt+D, and W (N on 4.5) | Omarchy's panels, hosted in WULING's bar | Omarchy's binding |
| **Super+Ctrl+G** | Terminal | **WULING, new** |
| **Super+D** | Dispatch | **WULING, new** |

Both new keys are free in 4.0.6 and 4.5.0-rc2. The installer refuses to overwrite a user's own binding of them.

## 10. Public standards

- **Resolutions:** 1366×768 to 4K, fractional scale; sizes scale with Omarchy's `[font] base-size`.
- **Screen shapes:** Omarchy's background only fills by cropping. Backgrounds are 3840×2160 and keep their text inside the area that
  16:9, 16:10, 3:2 and 21:9 all show (`design/src/wall.html`). `design/render.sh bg` rebuilds them.
- **Monitors:** a bar per output. Terminal, power menu, Dispatch and OSD on the focused output. Handle hotplug.
- **Languages:** zh-Hant, zh-Hans, en. English documentation.
- **Versions:** Omarchy 4.0.6 (stable) now. Keep the 4.5 differences behind one small boundary (the table in
  `research/omarchy-shell-api.md` §17): six bar sections, notification methods, `style.*` → `appearance.*`, `background`
  instead of `transparent`, `Ui.OverlayWindow`, i18n.

## 11. Budget

Baseline on kujira (i5-6300U, 7.5 GiB, 1366×768): `omarchy-shell` 304 MiB PSS, 0.04 % of a core at idle. With every
WULING part on: **at most +40 MiB idle, under 0.2 % CPU, no growth across open/close cycles.** Measure every phase the
same way as `review/phase0/`.
