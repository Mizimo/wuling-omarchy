# Registered-widget host contract (A-2)

This is a disposable experiment, not a proposed production bar. `Host.qml` is
316 lines, independently written. All widget and panel components are loaded
from the installed registry. No upstream QML or JS implementation is copied.
Sources below are relative to the pinned Omarchy `shell/` directory; 406 means
4.0.6 and 450 means 4.5.0-rc2. Runtime evidence is local under `wa2/`.

The replacement-bar loader supplies `shell`, `manifest`, `pluginRegistry`,
`barWidgetRegistry`, `barConfig`, `omarchyPath` and `barHidden`. The host must
own its PanelWindows, one per output, edge anchors and exclusive zones. A
widget registration contains its component and first-party metadata. Assign
`bar`, `moduleName` and per-entry `settings` after loading. First-party widgets
receive the bar's full host API. Third-party widgets receive an installed
`PluginBarApi`, with `shell.pluginShellForBarEntry(hostId, widgetId)` and scoped
click targets. Computing that facade in a binding caused a binding loop in an
earlier probe; assign it when binding the loaded widget instead.

| Host member | Consumer / missing behavior | 406 → 450 |
|---|---|---|
| `shell` | Clock `BarWidget.qml:51`, audio `Panel.qml:435`, monitor `Panel.qml:258`: inline entry updates, service access and config changes. Missing means controls stop persisting or cannot reach services. | Same role; use each installed facade. |
| `foreground` | `Ui/PanelSlider.qml:14`, panel labels and sliders: content color. | Same. |
| `barForeground` | `Ui/WidgetButton.qml:12`, `Ui/Panel.qml:23`: bar text and panel accents. | Same. |
| `background` | `Ui/PanelSlider.qml:27`: background/contrast color. | Same scalar; 450 config adds background modes. |
| `urgent` | `Ui/WidgetButton.qml:13`, agents and network: attention/accent color. | Same. |
| `fontFamily` | `Ui/WidgetButton.qml:10` and panel text: font family, with upstream font-size tokens. | Same; native Bar uses `Style.font.family`, not `bar.fontFamily`. |
| `position` | `Ui/PopupCard.qml:34`, `KeyboardPanel.qml:68`: popup side and anchor. | Same four edges. |
| `vertical` | `Ui/WidgetButton.qml:58`, `BarWidget.qml:22`: orientation and layout. | Same. |
| `barSize` | `Ui/WidgetButton.qml:59`, `KeyboardPanel.qml:123`: widget and popup geometry. | 450 may call optional `barSizeFor(screen)`, otherwise falls back to `barSize`. |
| `iconSlot` | Probe mirror only: native `Ui/BarIconButton.qml:9`, tray, clock and power read **Style.bar.iconSlot**, not the host member. Omitting the mirror does not remove their native metric. | Same. |
| `iconCanvas` | Probe mirror only: native `Ui/BarIconButton.qml:10` reads **Style.bar.iconCanvas**. | Same. |
| `iconFont` | Probe mirror only: native `Ui/BarIconButton.qml:19` reads **Style.bar.iconFont**. | Same. |
| `statusSlot` | Probe mirror only: native `Ui/BarIndicator.qml:49`, weather and update read **Style.bar.statusSlot**. | Same. |
| `transparent` | Bar presentation and widget contrast. Missing gives incorrect appearance. | 406 boolean; 450 CLI `transparent true` writes `background:"none"` and removes that boolean. Host accepts both. |
| `foregroundAnimationEnabled` | `Ui/WidgetButton.qml:91`: optional foreground animation. | Same; probe disables it. |
| `layoutConfig` | `plugins/bar/widgets/Tray.qml:164`: nested layout/config access. | 450 adds `centerBegin`, `centerEnd`, `tray`; host renders all six sections. |
| `centerSectionRevealHeld` | `plugins/bar/widgets/Indicators.qml:18`: reveal inactive indicators. | Same; probe hover boundary is simplified, not native drag/hover parity. |
| `centerHoverRevealSuppressed` | Indicators plus clock/weather panel: prevent unwanted reveal while panel open. | Same. |
| `setCenterHoverRevealSuppressed(bool)` | Clock `Panel.qml:125`, weather `Panel.qml:67`: coordinate reveal. | Same. |
| `summonBarWidget(id)` | `shell.qml` panel routing: choose live widget on focused output and call `open()`. Missing breaks default panel shortcuts. | Same. |
| `hideBarWidget(id)` | Shell lifecycle: call chosen widget's `close()`. | Same. |
| `isBarWidgetOpen(id)` | Shell toggle: report chosen widget's `opened`. | Same. |
| `panelWidgetIdAt(section,index)` | Shell `togglePanelAt`: 1-based visible panel order, excluding ordinary widgets and zero-size entries. | Same; six sections affect ordering. |
| `moduleWidgets(id)` | `Ui/BarWidget.qml:30`, Bluetooth `Panel.qml:429`: sibling instances across outputs. | Same; restrict third-party lookup to its own id. |
| `activePopout` | `Ui/KeyboardPanel.qml:241`, `PopupCard.qml:76`: current panel identity. | Same; give a foreign marker to a third-party facade for other owners. |
| `requestPopout(owner)` | `KeyboardPanel.qml:242`: close previous owner, preferring `closeForPopoutSwitch()`, then establish new owner. Missing permits overlapping panels. | Same. |
| `releasePopout(owner)` | `KeyboardPanel.qml:247`: release only if this owner is still active. | Same. |
| `switchPanelFrom(owner,direction)` | `Ui/Panel.qml:34`, clock/weather: Tab navigation in visible section order. | Same. Arrow semantics remain each native panel's responsibility. |
| `clickTargets` | `KeyboardPanel.qml:304`: outside-click mask excludes live bar targets. | Same. |
| `registerClickTarget(target)` | `Ui/WidgetButton.qml:48`: register button for popup click-through. | Same. |
| `unregisterClickTarget(target)` | `Ui/WidgetButton.qml:46,56`: remove stale target on host change/destruction. | Same; teardown ordering needs care. |
| `targetBelongsToWindow(target,window)` | `KeyboardPanel.qml:310`: avoid another output's target entering the mask. | Same. |
| `showTooltip(target,text)` | `Ui/WidgetButton.qml:105`, tray: show a delayed, output-anchored tooltip. | Same. |
| `hideTooltip(target)` | `Ui/WidgetButton.qml:37,42,112`: cancel only the current target. | Same. |
| `run(command)` | Workspace, clock timezone, weather, agents, update: execute requested native action. | Same. |
| `traySectionDragActive` | 450 `PluginBarApi.qml` and tray: nested-section drag state. | Added; false in this non-drag probe. |
| `traySectionPopoutOpen` | 450 tray: nested-section panel state. | Added; derive from active owner. |
| `notePopoutCard(card)` / `popoutCardFor(owner)` | 450 KeyboardPanel: reuse previous panel-card geometry within a section. | Added; optional compatibility callbacks, wired only when installed facade declares them. |

The clock's nested panel passes its **host widget** as popout identity; do not
identify the nested panel as a separate slot. Third-party facades deliberately
hide arbitrary first-party internals. The probe uses the installed facade,
not a JavaScript imitation. `Ui/PluginBarApi.qml` is itself part of the version
contract and should be included in compatibility checks.

The layout proof covers official `bar position`, `transparent`, `move`, `set`,
watched shell.json changes, four edges and focused-output shortcuts. The 450
transparency change was found by a failing control, then handled in this probe.
It does not implement 450's glass background mode or adaptive contrast.

A production host still needs overflow policy, complete hover behavior,
keyboard/accessibility review, shell-hidden transitions, duplicate-id placement handling and safe hot
replacement. The probe observed stale/duplicate IPC handlers when switching
bars in the 406 process; a fresh official shell restart removed them. This is
not a claim of clean hot replacement or an upstream attribution.

Drag is a separate implementation: start threshold, pointer capture, insertion
preview, per-section/output geometry, tray nesting, cancel/commit persistence,
and edge-move preview. Estimate **5–10 engineering days** plus regression work
for native-like drag parity; this is a planning estimate, not a measured task.
Without drag, official `omarchy bar move ... --section/--before/--after` and
`omarchy bar position ...` remain usable and were exercised. Hardening the
non-drag host and its compatibility fixtures is roughly another **2–4 days**.
