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
   Its only new keys are Super+Ctrl+G (Terminal), Super+D (Dispatch) and Super+Ctrl+/ (Keymap).
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
| Background | Starts on the survey line | Starts on the wide band |
| Omarchy's panels | Hairline border | Accent hairline |
| Motion | §5 everyday | §5 plus entry choreography |

**Backgrounds.** Three images, each in both palettes, all built from the Endfield Industries identity: its mark, its yellow band and
contour lines. No painted landscapes. Every theme carries all three, so Omarchy's background switcher moves between them.

| Image | What it is | First in |
|---|---|---|
| `bg-line-*` 測線 | A contour map with one survey line, the mark top right. Stays out of the way of windows | `field` |
| `bg-thin-*` 細色帶 | The mark in the middle on a thin yellow band, contours all round | |
| `bg-band-*` 寬色帶 | The mark in the middle on the full band, contours below: the official banner's composition | `hud` |

**Customising.** Values resolve in this order: defaults → the theme's preset → `~/.config/wuling/overrides.toml`.
`wuling theme resolve` prints every value with its origin. An update never writes to `~/.config/wuling/`. `wuling config set
<key> <value>` edits the file, so an agent can change it as easily as a person.

| Key | Values | Default |
|---|---|---|
| `labels` | `true`, `false`: the micro labels on bar cells | `true` |
| `menu.selected` | The selected row in Omarchy's menu. `edge`: a raised row with a leading edge. `fill`: a solid row, yellow on PAPER; on MIST the raised row alone, because Omarchy draws detail text in the light text colour and yellow would hide it. Omarchy reads this from the theme, so setting it regenerates WULING's installed themes | `edge` on MIST, `fill` on PAPER |
| `terminal.sections` | any of `clock link levels signal agent telemetry comms` | all |
| `sounds` | `essential`, `full`, `off` | `essential` |
| `motion` | `full`, `reduced` | `full` |
| `session.arrival` | `true`, `false`: the animation when a session starts (§8.9) | `true` |
| `session.exit` | `true`, `false`: the animation for logout, reboot and shutdown (§8.9) | `true` |
| `session.theme` | `true`, `false`: the wave on a theme switch (§8.11) | `true` |
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

**Omarchy's `colors.toml`** is generated from these (the exact mapping and the ANSI colours are in `tokens/wuling.json`, and the
code in `bin/lib/wuling/theme.py`). PAPER's `accent` is the ochre `#6B5F00`, because Omarchy's templates use `accent` as text. Set
`hyprland_active_border` and `hyprland_inactive_border`. **Ship no `hyprland.lua`**: Omarchy's defaults are already
square and flat (gaps 10/5, border 2), and a git-installed theme would drop the file anyway.

**Omarchy's `shell.toml`** comes from `bin/lib/wuling/theme.py`, including the rule for its menu: a raised row with a yellow
left edge on MIST, a yellow fill on PAPER. Omarchy draws a row's detail text in the menu's text colour at .52, so a
white or yellow fill on MIST would hide it.

## 4. Visual language

- **Type.** Geist Mono for labels and readouts, Geist for body text, Barlow Condensed for the clock and large numerals,
  Noto Sans/Serif CJK for Chinese, Material Symbols Sharp for WULING's own icons. Sizes in `tokens.css`.
- **Shape.** Square. Chamfers 6/10 px on chips, cards and toasts. 1 px hairlines. No radius, no shadow. Panels on Omarchy's `qs.Ui`
  panel, the Terminal included, keep its square frame: chamfering it would mean a second input layer to keep working on every version.
- **Labels.** Micro labels are 8–9 px uppercase mono and decorative: nothing important is only in a micro label.
- **Selection in WULING's own surfaces.** The plate inverts: `paper-0` ground, `ink-2` ink, 2 px yellow on the leading
  edge or foot.
- **Danger.** Logout, Reboot and Shutdown carry a hazard strip and need a long press.
- **Marks.** `assets/ef-mark.svg` is the Endfield Industries mark, redrawn as vector shapes in `currentColor`: use it wherever it is
  shown large. `assets/emblem.svg` is the simplified 30 px plate for the bar's menu cell.

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
| Terminal page | Slides 24 px in the direction of travel and resolves, 220 ms | Scan line |
| Error | Vermilion border and a 300 ms shake | Glitch |

Input is never held hostage: a surface takes input from its first frame, and typing during the build applies at once.
Respect a `motion = "reduced"` setting: every entry becomes a 90 ms fade.

## 6. Sound

The cue set from the earlier WULING: short, dry, industrial and water, synthesised, ours. `open`, `close`, `toggle`,
`select`, `deny`, `notify`, `alert`, `tick`, `hover`, and for §8.9 `boot`, `drop` and `seal`.

- Played with `pw-play` from a small service, bounded overlap, never Qt Multimedia in the shell.
- Master at 60 % of system volume. `sounds = "essential"` (default: no `hover`, no `tick`), `"full"` or `"off"`.
- Do Not Disturb silences notifications. Omarchy's own menu has no events to hook and stays silent.
- **Login music** is off by default. The user supplies the file (`login_music` in overrides); it never enters the repo.
  One-shot at session start, as Arrival's arming ends, skipped when muted or in DND.

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
  change, fall back to showing the widget as it is. Vertical bars use the plain widget. Omarchy's stock layout sets `dddd HH:mm` explicitly, so when the
  layout entry sets none or exactly that, the host passes `HH:mm` and the date stack carries the day (`MON 週一` by language, as in the Terminal's head). Right-click still
  cycles Omarchy's formats and writes them to `shell.json`, one step of the ring then looks like the next, which we accept; show the date stack only while the format has no date of its own.
- **Host font** is Geist Mono. Icon glyphs fall back through fontconfig to Omarchy's Nerd Font, as tested.
- **Narrow screens:** below 1280 px drop the identity cell; below 1024 px also drop the date stack and window.
- **Not rebuilt:** drag to reorder, drag to move the bar. `omarchy bar move` and `omarchy bar position` do it.
  Double-clicking empty bar space toggles transparency, as Omarchy's does.
- **Hot-switching bars leaves stale IPC handlers** in 4.0.6, so install and removal restart the shell officially.

### 8.2 Terminal — `wuling.terminal`

The Field Terminal: one panel for what is going on, the switches used most, and a detail page for every item on it. A `bar-widget` plugin using
`qs.Ui`'s panel, so it shares Omarchy's rules: one popout at a time, outside click, Tab to the next panel. It works
under Omarchy's own bar too. Key: **Super+Ctrl+G**. 372 px wide, full height minus the bar and 10 px gaps.

| # | Section | Shows | Source | Input |
|---|---|---|---|---|
| 02 | Terminal | Clock with seconds, date, zone, uptime. Head right: the user, then `⋮` | System | Clock: Calendar. User: System. `⋮`: Config |
| 03 | Link | Tiles: Wi-Fi, Bluetooth, Tailscale, DND, Night, Power profile. A tile with no hardware or service hides. A radio that is only soft-blocked still has hardware, so its tile stays and shows Off: a ThinkPad's Bluetooth adapter leaves USB while blocked. Wi-Fi shows the network's name when connected and Tailscale `Connected`; otherwise On or Off in the language's pair. Read without starting a scan. Night needs only Omarchy's toggle and `hyprsunset` installed, not running: the toggle starts it, so a stopped service shows Off | Quickshell modules, Omarchy commands, rfkill | **Wi-Fi, Bluetooth, Tailscale, Power: left opens the page, and the switch lives there**, so a stray click can't cut a remote machine off. DND, Night: left toggles. Right: Omarchy's matching panel, as before; Tailscale's exists only as its bar widget, so right opens its page too |
| 04 | Levels | Volume, brightness, segmented | PipeWire, `omarchy-brightness-display` | Drag, wheel. Same OSD as the keys. Volume's icon: Audio. Brightness's icon: Omarchy's monitor panel |
| 05 | Signal | Art 64, title and artist, progress hairline, times, transport (play in yellow), 20-cell jade spectrum. No player: head `NO SIGNAL · 無訊號`, dashed art, `--:--`, outlined transport without yellow, flat cells; it crossfades to the live layout, 220 ms | MPRIS; `cava` if installed | Previous, play/pause, next |
| 06 | Agent | Per agent: plan, session and week meters, time to reset. A meter's label is the limit's name without its parenthesis, micro uppercase; the label column grows to the widest, up to 66 px, and the meter gives the room. Row: open the default agent, left aligned, its name as a micro tag at the right when known. Hidden when no agent has usage | `~/.local/state/omarchy/agents/usage/*.json` | Row: `omarchy-agent --pick`. Agent: Omarchy's agents panel |
| 07 | Telemetry | CPU, memory, temperature with sparklines. One cell per battery pack: % and the state word. A pack whose full energy is 0 shows `— 未裝 N/A`, muted; at 8 % or less, vermilion and static, because one empty pack beside a healthy one is information, not an alarm. Sampled only while open | `/proc`, hwmon, UPower | CPU, memory, temperature: Performance. A pack: Power |
| 08 | Comms log | The newest rows that fit above the foot, at least 3. A row: source and time, then the summary, then the body in up to 2 lines. Head: the count, `CLEAR ALL 清除`. Hidden while `wuling.notifications` is off | `wuling.notifications`' state file | Click: the row opens in place, full body, and its action button if it has one, validated again before running. `+N`: Comms |
| | Foot | Lock, Sleep; Exit, Reboot, Off | Omarchy's commands | Dangerous ones open the power menu |

Section numbers follow what is shown. Too tall: the body scrolls, its last 14 px fade into the panel's ground, and the foot stays, so a cut row never reads as a glitch against the foot. Sections can be switched off in
overrides. Data comes from commands printing JSON (`wuling status --json`); the QML only displays it. Share one
collection schedule with Omarchy's agents panel; never start collectors per view, never log account contents.

The spectrum needs `cava`, which stock Omarchy doesn't ship. WULING never installs it. If it's there, it runs at nice 19 only while the panel is open and something plays. Without it the cells follow the stream's peak through PipeWire, or stay flat if that isn't available.

**Detail pages.** Every item opens its own page inside the panel (DECISIONS, 2026-11-04). The clock section stays; the page slides over everything below it, the foot included, 220 ms and 24 px in the direction of travel, `hud` with its scan line, reduced motion a 90 ms fade; first row readable within 320 ms. Head: `‹ BACK · 返回` and at the right the crumb, `03 LINK › WI-FI · 無線網路`, the number in the accent. Foot: key hints. Behind the content a watermark glyph at 4.5 %. Too tall: it scrolls, with the same 14 px fade.

- **Getting around.** ↑↓ select, Enter activates, ← or Backspace goes back outside a text field. Esc steps back, then closes, as in Dispatch. `wuling terminal open <page>` goes straight there: `performance power audio system calendar wifi bluetooth tailnet comms config`. Closing the panel forgets the page. Cues: `select` going in, `close` coming back, `toggle` when a hold completes, `deny` on a failure.
- **Data.** Each page is a section of `wuling status`, started when the page opens and stopped when it closes. A closed Terminal still runs nothing. Reading never changes state; each action is a fixed argv in `wuling action`, never through a shell.
- **The same backends as Omarchy's panels:** NetworkManager through `nmcli` and `Quickshell.Networking`, `Quickshell.Bluetooth`, `Quickshell.Services.Pipewire`, UPower, `powerprofilesctl`, and the `tailscale` command when it's installed. No new dependency. Anything that imports an Omarchy module goes through the check in §10.
- **Failures stay on the page.** The row says what failed in one line, `deny` plays, the old state stays. What a service answered isn't logged.
- **A hold guards what can cut you off:** 0.8 s of Enter or pointer, release cancels, the Power menu's bar. Wi-Fi off, disconnect, Tailnet stop. Remote access rides on them.

| Page | Shows | Does |
|---|---|---|
| Performance 效 | CPU % large, load 1 · 5 · 15, temperature, frequency, uptime. 60 s sparkline. One 24-cell bar per thread, yellow above 80 %, two columns past 8 threads. Memory: a 24-cell bar of used, cache and free, a legend, swap. Processes: name, CPU %, RSS | `S` sorts by CPU or memory. Enter: `btop` in the default terminal |
| Power 電 | Combined % large, state in jade while charging, time to full or empty, watts, supply. 24 h level sparkline from UPower's history. One card per pack: state word, gauge, %, health | Profile: `SAVER 省電 · BALANCED 平衡 · PERFORMANCE 效能`, ←→ moves it |
| Audio 音 | Output devices: the active one a card with a jade rail, a level and mute; the others rows. The input device with its level and a live meter. `STREAMS`: one level per app | Choose the device, drag or wheel a level, mute. The meter runs only while this page is open; if it lights Omarchy's microphone indicator, it comes out and the delivery says so |
| System 系 | The emblem and the hostname large. `HOST`: host, OS, kernel, CPU, GPU, disk. `SESSION`: Omarchy, Hyprland and Quickshell versions, uptime, display, input method. `RELEASE`: WULING version, commit, date | `COPY 複製`, `FASTFETCH` in the default terminal |
| Calendar 曆 | A month, Monday first, ISO week numbers; today a yellow tag, Sundays vermilion-light, other months muted. `TODAY`: date, ISO week, day of year, zone | ‹ ›, `TODAY · 今天`. Omarchy's clock panel stays on the bar |
| Wi-Fi 網 | `RADIO`, interface, an OFF\|ON switch. `● LINKED · 已連線` in jade: signal bars, name, lock, band; IPv4, gateway, rate and security, signal; `hub` + `TAILNET · 遠端經此` when the tailnet goes through this link. `AVAILABLE · n`, the list's age, `↻ SCAN`: signal bars, name, lock or `OPEN · 開放`, band, `SAVED · 已存` | Enter connects. A secured unsaved network opens `PASSPHRASE` in place, hidden with a `visibility` toggle. The passphrase goes to `nmcli` on stdin, as in Omarchy's panel: never in argv, the environment, a log or a state file. Enterprise networks hand over to Omarchy's panel. `DISCONNECT` (hold), `FORGET`. `S` scans; opening the page doesn't, it shows what NetworkManager already has |
| Bluetooth 藍 | `RADIO` and its switch. `● CONNECTED · 已連接`, `PAIRED · 已配對`, `AVAILABLE · 可用`: type icon, name, battery % when reported. Empty: `NO DEVICES · 尚無裝置` | Connect, disconnect, pair, forget. `S` discovers, and leaving the page stops it. Turning the radio on clears a soft block too |
| Tailnet 鏈 | State, this machine's name and address, exit node. `n/m ONLINE`; peers, online first: name, `DIRECT` or `RELAY`. `NEEDS LOGIN · 需要登入` or `STOPPED · 已停止` when that's the case | Start, stop (hold), with the same commands as Omarchy's widget. Missing `tailscale`: the tile hides, no page |
| Comms 訊 | Every row with its full content and action, newest first | The action button, `CLEAR ALL 清除`. Omarchy's `showHistory` lands here |
| Config 設 | WULING's own: `THEME` and `BACKGROUND` through Omarchy's switchers; `LANGUAGE`, `SOUNDS`, `MOTION`, `LABELS`, `MENU`; `SECTIONS`, one switch each; `ARRIVAL`, `EXIT`, `LOGIN MUSIC` | Each writes with `wuling config set`. `DISPLAY`, `INPUT`, `FONT`, `KEYS`, `DEFAULT APPS` hand over to Omarchy's menu or tool: nothing Omarchy has is rebuilt |

### 8.3 Notifications — `wuling.notifications`

Replaces `omarchy.notifications` in the same process, through `disabledPlugins` and `omarchy.clonedFrom`. Omarchy's
scripts and keys reach it unchanged.

- **IPC target `notifications`, 4.0.6:** `dndState`, `toggleDnd`, `setDnd`, `isDnd`, `showHistory`, `clear`, `dismissAll`,
  `dismissOne`, `invokeLast`, `dismiss(summary)`, `ping`. **Added on 4.5:** `act`, `invokeAction(n)`, `keyboard`, `count`,
  `expand`, `probe`; do not assume the old names exist there. Also the service members `doNotDisturb` and
  `setDoNotDisturb` that the DND indicator reads, and `omarchy.indicators refresh`.
- **Levels:** normal has a jade edge. One with actions or a click command has a yellow edge. Critical has a vermilion edge.
- **Keep Omarchy's rules**, from the installed version's own modules (`shell/plugins/notifications/`). Lifetimes: critical stays, low at
  least 5 s, normal at least 8 s, at most 30 s. DND lets through app `omarchy-action` and critical from `notify-send`, and on 4.5 a detected
  verification code. Ephemeral ones (`transient` hint, `notify-send`, `omarchy-action`) silenced by DND are not recorded.
- **Toast:** 340 px, header (`Comms · 通訊`, app, time, close), art, summary, body, actions, a life line. Stacks from the
  top right, newest on top, on the outputs Omarchy uses: every output on 4.0.6; on 4.5 the focused one, where the stack stays until it
  empties. Toasts keep that place unless the open Terminal's panel covers it. Then they sit to the panel's left; if 340 px doesn't fit there, to its right;
  if neither fits, they stay and overlap. They never shrink.
- **A flat stack, no decks.** What doesn't fit waits behind a one-line `+N` tail and moves up as space frees; at most 100 live, as Omarchy. With the
  pointer on the stack, lifetimes pause and new toasts wait, at most 30 s, so nothing moves under the pointer. Toasts on screen survive a shell
  restart, with Omarchy's grace.
- **Keyboard**, the same on both versions. `act`: with no choice it dismisses, with one it runs it, with more it enters keyboard mode. Keyboard mode
  is Omarchy's: ↓ J Tab, ↑ K Shift+Tab, Enter runs the click, Delete or Backspace dismisses, 1–9 press a button (buttons show their digit), Esc leaves,
  and the same idle timeout. `expand` toggles: truncated bodies open and lifetimes pause; it returns `expanded` or `collapsed`. `probe` and `count` keep
  Omarchy's fields.
- **Actions:** buttons as the app sends them. **Clicking a toast** runs its `omarchy-exec-argv` hint as argv, never through a shell,
  with the same validation as Omarchy's. Omarchy's crash notification (`omarchy-crash-watch`) has no action buttons and depends on this.
- **DND survives the handover.** With no state file of its own yet, the plugin takes DND from Omarchy's stored state, read once. Omarchy's file is never written, so
  after the plugin is disabled Omarchy returns to the value it last stored.
- **History** goes to `~/.local/state/wuling/notifications.json`, 0600 in a 0700 directory: 100 rows and 24 hours on both versions. A row keeps what
  Omarchy 4.5's `Store.persistable` keeps: no images or links, and text with a verification code only as the placeholder. `clear` clears history
  only. Removal deletes the file: it holds other people's messages. This promise covers WULING's own files: a sender that names an image file after a code and fails
  to load it gets Qt's warning in the journal, as under Omarchy, and we leave that.
- **Saving can't fail quietly.** One writer process saves the state. A change counts as saved only when the writer answers ok; until then the newest full state is kept and
  sent again. If the writer exits or fails to start while the shell runs, it gets three restarts, after 1, 5 and 30 s; the first failure doesn't count against them. If the third restart also dies, all within 10
  minutes of that first failure, it stops trying, `wuling doctor` fails with the reason, and one low toast says history isn't being saved, once per session. A writer that outlives those 10 minutes starts a new count. Shell teardown still never waits for it.
- **`showHistory`** opens the Terminal's Comms page. If the Terminal or its log section is off, it replays the newest 6 as toasts and
  changes no setting. Like Omarchy's replay this ignores DND: the user asked, and it is how to see what DND held back. A replay records nothing new.
  With nothing to show, a low toast says `No recent notifications`, not a dead key.
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
- **After the hold** comes the exit sequence (§8.9), then Omarchy's action. With that switched off, the action runs when the hold completes.
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

### 8.7 Focus overlay — not built

The mockups once showed `hud` with corner brackets and a tag following the focused window. Hyprland 0.56 reports no event when a window is
resized from the keyboard, so the brackets would stay in the wrong place until focus next moved, and a timer just for a decoration breaks
principle 5. The focused window has Omarchy's yellow border in both presets. Build it if Hyprland gains a geometry event.

### 8.8 Theme only

Omarchy's menu, panels, clipboard, emoji, pickers, lock screen, polkit dialog and apps change through the theme alone;
their code and layout stay Omarchy's. The system font stays the user's (`omarchy font set`). **Boot unlock:** Omarchy's `omarchy-plymouth-set-by-theme` reads the theme's `unlock.png` and
colours. It needs sudo, so it is a separate, optional step. The image is the **Endfield Industries mark alone**
(`assets/unlock-{mist,paper}.png`): no WULING name, no band. Omarchy centres the image and hangs the password box 40 px below it, so the
pair always sits low. The mark is 300 px tall, and 40 px of empty space below it in the image lifts it to just above the centre.

**fastfetch.** The vertical 武陵 mark (`design/assets/fastfetch-logo.png`) is in the user's own config, not the theme: the
installer asks.

### 8.9 Session motion — `wuling.session`

The two animations the earlier WULING was liked for. `design/mockups/arrival-*.png` and `closing-*.png` show the look. Both are full-screen
overlays built only while they play. They leave nothing running behind them, and neither ever delays or
blocks what the user asked for. Switching the plugin off leaves Omarchy's own start and exit. No 3D: the earlier 3D login world belonged to a
greeter and a lock screen, which stay Omarchy's here.

**Arrival, once per login session.** The marker is in `$XDG_RUNTIME_DIR/wuling/`, keyed by the session id, so a shell restart, theme switch,
update, unlock or resume never replays it. Times run from the overlay's first presented frame. Always MIST until the wave. It plays only at the start of a session: no marker yet, and the compositor started under 30 s ago. WULING installed or `wuling.session` first enabled on a desktop that has been running writes the marker and plays nothing; the worst a slow login can do is miss the animation, which is why a plain age check is good enough here.

| When | What |
|---|---|
| 0 | Ink-0. Registration marks scale in from 1.6 (160 ms, 30 ms apart); the run timer starts; `EF-WL / <HOSTNAME>` and `■ SYSTEM BOOT` decode; the ■ blinks |
| Arming ends, 0.4–1.0 s | When the bar has its first frame on every output, the background is drawn and settings are read, or at 1.0 s. The wave's shader is warmed in this time: a cold cache stalled 6–10 refreshes on kujira in the earlier build. Everything below counts from here (A). `boot` cue, login music |
| A | Title types: `<HOSTNAME> — 武陵 FIELD TERMINAL`, 28 ms a step, CJK one step, yellow caret. Too wide: steps down to 36 px, then elides the middle of the hostname. Progress, 20 segments, fills over 1.9 s beside a percentage ticker |
| A + 0.6 | Subtitle resolves and decodes; A + 0.68 the rule draws from the left |
| A + 0.72 | Log lines resolve 110 ms apart, each with a `tick` a little higher than the last: compositor, shell, link, power (omitted with no battery), operator. Real values read before the overlay starts; a value not ready in 300 ms shows `—` with `[ -- ]`, never an invented one. The link line names the interface and `online`, not an address: people film their desktops |
| A + 1.3 | Operator's `[ .. ]` turns `[ OK ]` |
| A + 1.4 | The ink leaves in 16 × 9 cells, a wave from the top (threshold .55 · row + .35 · hash, cells at the threshold ghost with a yellow tint and outline), 420 ms, `open` at half level: the real desktop appears under the log, with an ink scrim keeping the left column readable (.82 at the edge, .62 at 46 %, .08 at 78 %). PAPER turns the overlay to PAPER in the same 420 ms |
| A + 1.45 | `WELCOME BACK, ENDMINISTRATOR · 歡迎回來，管理員` decodes |
| A + 2.0 | The overlay wipes top to bottom behind a yellow scan line, 300 ms snap. `wuling.bar` slices in at + 20 ms (6 slices, 200 ms, `drop`) |
| By 3.5 s | Everything is gone and destroyed, whatever else happened. A watchdog enforces this |

- **Skip:** any key or click jumps to the wipe. It holds exclusive keyboard focus, so the skipping key reaches no app; a key already held when
  it appeared does not count. Hyprland's and Omarchy's global keys keep working.
- **Lock:** a lock request removes it at once.
- **Outputs:** the focused one runs the whole sequence; others show frame, title and progress in step; all wipe together.
- **No desktop before its first frame.** The first frame is ink alone, from a service loaded with the shell (`keepLoaded`), which also reads the session
  marker before it draws, so a shell restart never flashes ink. Everything else loads behind that frame. Omarchy's first frame on both versions followed
  this path in four real logins out of four (`research/phase-e-arrival.md`), so there is no cut to ink. The compositor's fade-in is off for this one layer (`no_anim`, in WULING's Hyprland block, as Omarchy does for its own bar): on a cold 4.0.6 login the wallpaper arrived while the ink was still fading up and showed through for about 100 ms. Before the ink, Omarchy 4.0.6 itself shows an empty dark strip, its own bar, for under a second: its plugin scan is a subprocess, so the selected bar isn't available yet. We have no clean way to stop that and 4.5 doesn't do it, so we leave it.
- **Layout:** scales with the output's logical height, 768 being 1.0. The column stays 1126 design pixels wide and centred, so 21:9 gets wider
  margins, not a wider log.
- **Language:** as §7. In English the Chinese halves don't show; 武陵 stays.
- **Reduced motion:** no typing, no wave, no wipe: the final frame holds 600 ms, then a 120 ms fade.

**Exit, for Logout, Reboot and Shutdown in the power menu**, once the hold completes. Lock, Suspend, Hibernate and Screensaver run at once, as
in §8.5. Times run from the end of the hold.

| When | What |
|---|---|
| 0 | The card presses and pulses; a 34 px vermilion 終 stamp, from the menu's title 終止協議, lands at the card's lower right, scale 1.4 to 1 in 60 ms, `seal` |
| 120 ms | The menu de-resolves, 160 ms: scaleY 1 to .5 to .02 about the centre line, contrast up, fading |
| 280 ms | The theme's `background` colour covers every output in cells from the top: the same 16 × 9 wave as Arrival's, 280 ms. No screenshot is needed: the cells draw over the live desktop |
| 560 ms | **Omarchy's action runs, once.** The mark fades in, 200 ms, and the overlay stays until the session ends |

- **It ends where the next screen begins.** The mark is the theme's `unlock.png` at its native pixels, in the centre: where Omarchy's boot screen
  draws it, in the same colour, on reboot and shutdown too, once `omarchy plymouth set-by-theme` has been run. After a logout, Omarchy's login screen has
  the same image about 44 px higher, above its password field. A blank moment from a mode change or the firmware may come between, and isn't ours. In
  other Omarchy themes the mark is the plugin's own copy in the palette's text colour.
- **The action does not depend on the animation.** Its timer is separate. If the overlay fails to load, or `session.exit` is off, the action runs
  when the hold completes. Omarchy gives about 2 s to close windows before the session really ends, which happens under the ink.
- **Nothing gets stuck.** The overlay sits above whatever is on screen and ignores input from the stamp on. If the session is still alive 10 s after the
  action, something refused: the overlay fades out, the OSD works again and a notification says so.
- **Nothing lands on the ink.** A surface that maps later draws over it, because Hyprland keeps no other order within a layer. So `wuling.osd` shows nothing
  while the sequence runs, which keeps the OSD Omarchy raises for these actions off the ink; nothing is wrapped around Omarchy's action to do it, and
  the hold lapses by itself if `wuling.session` is gone. With Omarchy's own OSD in use (`wuling.osd` off) that card does sit on the ink, and so does a toast
  arriving in those seconds, Omarchy's "failed" notification included. We leave both.
- Searching "reboot" in Omarchy's menu, or running Omarchy's command directly, takes Omarchy's own path with no animation.
- **Reduced motion:** the stamp, then a 120 ms fade to the ground, then the action.

`wuling session preview arrival|exit` plays either one and runs nothing, so they can be judged and tuned on a machine that must not log out.

### 8.10 Keymap — `wuling.keymap`

Every key on one screen, as in the earlier WULING. An overlay plugin on **Super+Ctrl+/**, in the owned block of `bindings.lua`; Omarchy's Super+K list stays. Built only while it's open. Full screen on the focused output, over the live desktop: the theme's darkest ink at 86 %, the head `KEYMAP · 鍵位`, the vertical 鍵位 in Serif Black 64 with its yellow cut. The same in both presets. Reduced motion: a 90 ms fade.

- **Layout:** groups in columns, by what the keys are for: `SHELL 介面`, `WINDOWS 視窗`, `NAVIGATE 導航`, `APPS 應用`, `SYSTEM 系統`, and `OTHER 其他` for a key that fits none, so none is dropped. A row: the description, then keycaps in mono with a 1 px border, Super a yellow cap `◆`. Too many for the screen: it scrolls. It fits 1366×768 and 4K alike.
- **Data:** the keys bound right now, the user's own included, from the same source as Omarchy's `omarchy-menu-keybindings`. Hyprland's Lua provider reports Lua binds only as `__lua`, so `hyprctl binds` alone isn't enough. `wuling keymap --json` prints them and the QML displays them. A version that changes the source falls under §10: the overlay says it can't read the keys, and Omarchy's list is still there.
- **Input:** typing filters, ↑↓ scrolls, Esc clears then closes, an outside click closes. Exclusive keyboard focus; pressing a listed key doesn't run it.

### 8.11 Theme wave — part of `wuling.session`

A theme switch, by any route, plays the wave of Arrival and Exit: the old look leaves in 16 × 9 cells from the top edge, threshold .55 · row + .35 · hash, cells at the threshold ghosting with a yellow tint and outline, 420 ms, `open` at half level, on every output. `session.theme` switches it off; reduced motion has none, and Omarchy's own transition runs.

- **It never delays or blocks the switch.** If the overlay fails, the theme still changes, as Omarchy changes it.
- **To be proven first.** The wave needs the old look on screen after the new palette applies, and Omarchy has no hook before the switch: `omarchy-theme-set` applies the palette early and runs `omarchy-hook theme-set` near the end. No wrapper around Omarchy's command and no capture running all the time. Omarchy's own theme picker must play it too, not only the Config page.
- It doesn't play during Arrival, Exit or a lock, nor for a background change alone.

## 9. Keys

| Key | Does | Whose |
|---|---|---|
| Super+Space, Super+Alt+Space, etc. | Omarchy's menu and apps | Omarchy |
| Super+Esc, power key | Power menu, through the menu extension | Omarchy's binding |
| Super+, and family, volume and brightness keys | Notifications, OSD, through their IPC targets | Omarchy's binding |
| Super+Ctrl+A, B, D, P, Alt+D, and W (N on 4.5) | Omarchy's panels, hosted in WULING's bar | Omarchy's binding |
| **Super+Ctrl+G** | Terminal | **WULING, new** |
| **Super+D** | Dispatch | **WULING, new** |
| **Super+Ctrl+/** | Keymap | **WULING, new** |

All three new keys are free in 4.0.6 and 4.5.0-rc2. The installer refuses to overwrite a user's own binding of them.

## 10. Public standards

- **Resolutions:** 1366×768 to 4K, fractional scale; sizes scale with Omarchy's `[font] base-size`.
- **Screen shapes:** Omarchy's background only fills by cropping. Backgrounds are 3840×2160 and keep their text inside the area that
  16:9, 16:10, 3:2 and 21:9 all show (`design/src/wallpaper.py`). `design/render.sh bg` rebuilds them.
- **Monitors:** a bar per output. Terminal, power menu, Dispatch and OSD on the focused output. Arrival and the exit on all. Handle hotplug.
- **Languages:** zh-Hant, zh-Hans, en. English documentation.
- **Versions:** Omarchy 4.0.6 (stable) now. Keep the 4.5 differences behind one small boundary (the table in
  `research/omarchy-shell-api.md` §17): six bar sections, notification methods, `style.*` → `appearance.*`, `background`
  instead of `transparent`, `Ui.OverlayWindow`, i18n.
- **An Omarchy we haven't tested.** Omarchy updates on its own schedule, so a newer version must never leave someone with a broken desktop.
  Parts on public interfaces keep running. Anything that imports an installed module checks that module's contents, not the version string, so an update that doesn't touch it changes
  nothing; if it did change, that part stays on Omarchy's own and `wuling doctor` lists it. Installing on an untested version says so in the plan, names the tested versions and
  asks, rather than refusing.

## 11. Budget

Baseline on kujira (i5-6300U, 7.5 GiB, 1366×768): `omarchy-shell` 304 MiB PSS, 0.04 % of a core at idle. With every
WULING part on, **memory only has to stay in a reasonable range** (DECISIONS, 2026-11-02): no steady growth over time or across open and close cycles, and CPU
near zero at idle. A few MiB either way is not a finding and not worth a design change; around +40 MiB idle is where it deserves a look. Measure at milestones, the same way as `review/phase0/`.
