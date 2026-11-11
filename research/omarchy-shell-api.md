# Omarchy shell extension research

A-1/A-2 interface studies and disposable experiments, not a product
implementation or approved design. Both 4.0.6 and 4.5.0-rc2 now have runtime
controls. A-2 results, limitations and the draft-theme review are in §17; the
406 menu-facade blocker does not reproduce in the 450 control.

## Sources and evidence notation

- **406**: Omarchy **4.0.6**, commit
  [`237f1b4071a0bff2296c6d740ba2b9fd695ebfa0`](https://github.com/omacom/omarchy/tree/237f1b4071a0bff2296c6d740ba2b9fd695ebfa0).
- **450**: Omarchy **4.5.0-rc2**, commit
  [`5978d93ae7da0a325b7493501911e3f1266cadd3`](https://github.com/omacom/omarchy/tree/5978d93ae7da0a325b7493501911e3f1266cadd3).

References below use `406 path:line` or `450 path:line`; lines refer to those
exact commits. A source finding describes implementation at that revision,
not a guarantee of future compatibility. Recommendations are explicitly marked.
Raw VM logs, package inventories, screenshots and configuration manifests stay
outside this repository in the local `wa1` and `wa2` evidence directories. No old WULING
implementation is imported.

## 1. Replacement bar and widgets

A manifest declares `kinds: ["bar"]` and `entryPoints.bar`; the user selects
its id in `~/.config/omarchy/shell.json` under `bar.id`. The host injects
`omarchyPath`, `shell`, `manifest`, `pluginRegistry`, `barWidgetRegistry` and
`barConfig` **only when the entry declares each property**. The entry is one
QML object, not an automatically repeated window. The plugin creates a
`PanelWindow` for each `Quickshell.screens` entry and owns its anchors,
layer, input region and exclusion zone. (`406 shell/shell.qml:170,220`;
`406 shell/plugins/bar/Bar.qml:1210,1248`.)

`barConfig` is a detached copy, including position, transparency, center anchor
and `layout`. `shell.bar` is a scalar facade: `barHidden`, `barSize`,
`fontFamily`, `position`. A replacement should expose those properties on its
root so other plugins receive correct clearance. Horizontal/vertical theme
sizes are `Style.bar.sizeHorizontal` / `sizeVertical`; scaling follows
`[bar] scale-with-font` and `[font] base-size`. Merely selecting the plugin
does not apply these sizes to its windows. (`406 shell/shell.qml:329,446`;
`406 shell/services/PluginBarStateApi.qml:3`;
`406 shell/Commons/Style.qml:297,341,386`.)

The host falls back to `omarchy.bar` for a missing/invalid bar selection or a
`Loader.Error`, remembering `failedBarId` until selection/reload changes it.
A component that loads successfully but draws nothing or throws in its own
logic is not covered by that fallback. (`406 shell/shell.qml:182–264`.)

The widget registry exposes component references, metadata and revision in a
detached catalog; a replacement can instantiate built-in and installed widgets.
This is not sufficient for full compatibility:

- Widget constructors expect the bar contract, including settings, module id,
  tooltip/click registration, popup coordination and shell access.
- The host routes built-in panel hotkeys to the replacement's
  `summonBarWidget`, `hideBarWidget`, `isBarWidgetOpen` methods. Without these,
  the visible button can exist while the default shortcut fails.
- `shell.pluginShellForBarEntry(ownerId, id)` provides target-scoped lifecycle
  and settings, **no service lookup**. A third-party widget needing its own
  service loses that integration under a replacement bar. Do not promise
  arbitrary third-party widget compatibility.
- A full bar itself receives narrow proxies for `omarchy.idle`,
  `omarchy.media`, `omarchy.nightlight`, `omarchy.notifications`, not arbitrary
  live service objects. Built-in audio/indicator behavior needs those proxies.

Sources: `406 shell/services/PluginBarWidgetRegistryApi.qml:3–23`;
`406 shell/Ui/PluginBarApi.qml:13–85`; `406 shell/shell.qml:592–654,691–739,1141–1215`;
`406 shell/services/PluginFirstPartyServiceApi.qml:3–46`;
`406 shell/plugins/panels/audio/Panel.qml:21`.
The service-less limitation remains at `450 shell/shell.qml:713`.

## 2. Panels and coexistence

`shell.summon/toggle/hide(id, payloadJson)` controls configured, enabled UI
plugins. A full bar can control configured non-authentication UI plugins;
ordinary third-party plugins can control their own lifecycle. CLI IPC is also
available to ordinary user processes. A panel/overlay/menu entry implements
`open(payloadJson)` and `close()`. The host queues payloads while loading.
Multiple independent entries can remain open: `openPanelIds` is a set, not a
global single-panel slot. (`406 shell/shell.qml:404,626–650,1126–1230`.)

Built-in bar panels have a separate single-popout coordinator. Opening one
calls `bar.requestPopout(owner)`, which closes the previous owner. Their anchor
is the invoking item's window/screen and geometry, clamped to available space;
top/bottom/left/right positions are handled explicitly. A replacement bar must
provide this contract if it hosts these panels. (`406 shell/plugins/bar/Bar.qml:556`;
`406 shell/Ui/PopupCard.qml:11–147`; `406 shell/Ui/KeyboardPanel.qml:41–205`.)

`KeyboardPanel` uses a fullscreen overlay surface, briefly requests Exclusive
keyboard focus, then switches to OnDemand. Its visible card is anchored to the
bar; the rest is an outside-click catcher, with special treatment of the bar
strip. Popup ownership and keyboard focus are distinct concerns.
(`406 shell/Ui/KeyboardPanel.qml:7–32,79–127`.)

**Design implication:** an independent Terminal can coexist as a separate
plugin, but focus still belongs to one surface, and fullscreen input masks can
cover another panel. Decide whether Terminal joins the bar's single-popout
coordinator or stays independent; coexistence must be verified for outside
click, Esc, monitor changes and keyboard restoration. A third-party plugin
does not get a general shared panel manager through its facade.

## 3. Overlay windows and monitor policy

| Surface | 4.0.6 implementation | Consequence for a new plugin |
|---|---|---|
| OSD | Overlay layer, Ignore exclusion, None keyboard focus, empty input mask; no explicit screen assignment | Set monitor policy explicitly if required; do not assume the host injects it |
| Notifications | One Overlay window per screen, None keyboard focus, input mask around toast column | All outputs receive the stock presentation; do not accidentally consume the whole screen |
| Menu | Overlay layer, Exclusive keyboard focus, fullscreen click catcher, Ignore exclusion; no explicit screen assignment | A Dispatch/power overlay owns Esc, outside-click and monitor policy |
| Bar panels | Overlay layer, anchor's screen, Exclusive-to-OnDemand focus transition | Reuse the documented behavior contract, not a copied implementation |

Sources: `406 shell/plugins/osd/Osd.qml:128–142`;
`406 shell/plugins/notifications/Service.qml:946–984`;
`406 shell/plugins/menu/Menu.qml:1018–1077`;
`406 shell/Ui/KeyboardPanel.qml:79–127`.

4.5 adds `Ui.OverlayWindow`: it snapshots the focused Hyprland monitor when
opened, waits for fullscreen geometry and scale before revealing content,
handles monitor removal and RTL, and defaults to Overlay/Exclusive. It is
absent from 4.0.6. A plugin importing it unconditionally cannot target both.
(`450 shell/Ui/OverlayWindow.qml:7–101`.)

## 4. Menu tree, extensions and Dispatch A

There is **no exposed parsed Omarchy menu tree** in the third-party shell API.
The menu capability is an *application* library (`sortedEntries`, names,
subtext, icons, launch, remove); it is not the Omarchy command tree.
`omarchy-menu` exposes toggle/summon/close/refresh/ping. The actual tree lives
inside `Menu.qml`, with pure helpers in `MenuModel.js`.
(`406 shell/services/PluginAppLibraryApi.qml:1–46`;
`406 bin/omarchy-menu:7–34`; `406 shell/plugins/menu/Menu.qml:219–264`.)

To independently reproduce 4.0.6 behavior, Dispatch A would need all of:

1. Read `$OMARCHY_PATH/default/omarchy/omarchy-menu.jsonc` and the user's
   `~/.config/omarchy/extensions/omarchy-menu.jsonc`. The parser strips full-line
   `//` comments and trailing commas; it is not a general JSONC parser.
   Accept the `items` object wrapper or a direct id-to-item object. Invalid
   input yields no rows. (`406 shell/plugins/menu/Menu.qml:51–52`;
   `406 shell/plugins/menu/MenuModel.js:1–63`.)
2. Normalize `parent` (dotted prefix, otherwise root), root's empty parent,
   `action` before `target` before menu kind, aliases (array or one string),
   icon/iconFont/label/title/description/provider/when/checked. Preserve first
   insertion order; later source entries overwrite matching ids. **Actual
   normalization fills omitted fields before merging**, so a partial extension
   can reset fields to defaults despite the comment describing a per-key
   overlay. This behavior needs explicit parity fixtures.
   (`406 shell/plugins/menu/MenuModel.js:13–95`.)
3. Evaluate `when` and `checked` as shell expressions, batching package and
   command presence and selected state readers. Visibility hides only on an
   explicit false result. Empty static menus/links disappear recursively;
   providers remain visible; recursion stops at depth 32. Reevaluate on open
   and after relevant refreshes; account for a guard process still running.
   (`406 shell/plugins/menu/MenuModel.js:254–277,383–481`;
   `406 shell/plugins/menu/Menu.qml:942–1015`.)
4. Route case-insensitively with `_` normalized to `-`; empty/go/menu routes
   resolve to root, exact ids beat aliases. App aliases do not become command
   routes. Activating an action route executes it rather than opening an empty
   submenu. (`406 shell/plugins/menu/MenuModel.js:176–190`;
   `406 shell/plugins/menu/Menu.qml:847–867`.)
5. Reproduce submenu/back/history, link targets, action execution and dmenu
   request/reply behavior. Commands run through the original action path;
   apps launch through AppLibrary, not a guessed shell command.
   (`406 shell/plugins/menu/Menu.qml:118–145,688–867`.)
6. Search descendants of the current menu. Each term must match a substring
   in label/leaf-id/aliases or a whole description word. Score exact label,
   app whole word, prefix, substring, name and description tiers, then depth
   and insertion order; place current-menu rows before deeper matches and
   preserve the divider. Apps with no filter sort alphabetically.
   (`406 shell/plugins/menu/MenuModel.js:279–352`;
   `406 shell/plugins/menu/Menu.qml:562–638`.)
7. Merge changing desktop entries without duplicate ids and refresh dynamic
   provider rows (including fonts and power profiles); maintain icon refresh,
   deletion and volatile-provider behavior. Static JSON alone is incomplete.
   (`406 shell/plugins/menu/MenuModel.js:107–164`;
   `406 shell/plugins/menu/Menu.qml:266–445`.)

4.5 translates shipped menu rows **before** extensions. Original English
labels remain search-only terms, not routing aliases. This is additional
behavior for parity. (`450 docs/i18n.md:15–16`;
`450 shell/plugins/menu/MenuModel.js:659–676`.)

The disposable tree reader imports the installed internal JS module as an
oracle, with no copied upstream implementation. That proves file access and
static/guard evaluation, **not a supported parsed-tree API**, dynamic-provider
parity, or permission to use that internal dependency in the product.

### Runtime blocker: the third-party menu facade

**406 VM result:** the intended menu AppLibrary capability is unavailable in
this stack (Qt declarative 6.12.0-2). A minimal `kinds: ["menu"]` entry first receives
a shell facade with `appLibrary == null`, then its shell property becomes null.
The same QML declared as an overlay retains its facade. This also reproduces
after a fresh shell process; removing the menu reader, windows, FileViews and
dynamic objects does not remove the failure.

The independent `facade` probe reproduces the relevant type boundary:
`Array.isArray(["menu"])` is true, whereas the same sequence reached through
an Instantiator delegate's `modelData.manifest.kinds` and `property var manifest`
is false; `indexOf("menu")` still returns 0. The source's `manifestHasKind`
requires `Array.isArray`. A panel Loader passes the delegate manifest to facade
creation, so it initially gets a `no-menu` profile and no AppLibrary. The later
prune compares that profile with the original registry manifest and revokes it.
This attribution is supported by the minimal type/lifetime controls and the
source; no upstream file was patched or instrumented.
(`406 shell/shell.qml:352–355,527–533,607–609,797–811,1331–1346`.)

**Design consequence:** do not treat the intended menu facade as a working
product dependency on this stack. The route probe records the defect and uses
the ordinary public `omarchy-shell shell hide research.menu` CLI for Esc when
the facade is missing. That fallback tests routing, not AppLibrary success.
The corresponding Array.isArray/profile checks remain in 450, but A-2 now
confirms its original-registry-manifest lookup avoids this failure; see §17.
(`450 shell/shell.qml:363–366,635–636,822–836,1398`.)
Local evidence: `vm406/guest-evidence/facade-menu-sequence.json`,
`facade-sequence.json`, `facade-overlay.json`; probe: `spikes/facade/`.

### Whole-route replacement (v399 investigation)

Declaring `kinds: ["menu"]` alone does **not** replace `omarchy.menu`; there is no
`menu.id` equivalent to `bar.id`. The replacement mechanism is
`omarchy.clonedFrom: "omarchy.menu"` on an enabled third-party manifest.
`resolveEnabledId` redirects calls using the built-in id to that enabled
replacement; enabling it also disables the source. This metadata can be tested
on an independently written entry, without executing `plugin clone` or copying
the upstream UI. It is still the host's *clone replacement* mechanism, not a
separate general route-registration API. Multiple enabled replacements for one
source are not an ordering contract to rely on.
(`406 shell/services/PluginRegistry.qml:171–181,491–555`.)

At 406 the CLI's root/apps/system/background/theme payloads all pass through
`shell.toggle/summon("omarchy.menu", payload)` and can therefore reach that
replacement without modifying keys. The 406 experiment delivered all six
requested physical-key combinations. `background` resolved to `style.background`,
`theme` to `style.theme`, `power-menu` to `system`, `settings` to `setup`, and
a user extension alias to its own menu. The no-clonedFrom negative control
left Super+Space with stock Omarchy and the probe call count at zero.
Payload route/alias resolution remains
the replacement's responsibility. At 450 Super+Alt+Space instead targets the
dock and is outside this redirection. (`406 bin/omarchy-menu:14–34`;
`450 default/hypr/bindings/utilities.lua:1–9`.)

Loading `MenuModel.js` from the runtime OMARCHY_PATH worked in the 406 QML
probe: 333 default rows and three extension rows were parsed without copying
the module. The static reader merged 337 rows including the injected root,
and its true/false `when` and true `checked` controls returned the expected
visibility and checkmark. This establishes direct runtime import. However it
contains helpers, not the complete live model. `when`/`checked` process
execution, provider scheduling, AppLibrary row construction, menu history and
display grouping are also in Menu.qml. Importing the JS alone cannot guarantee
exact behavior following every update. It needs version/feature checks and
parity checks against the installed version, and a deliberate maintenance
decision. (`406 shell/plugins/menu/MenuModel.js:1–481`;
`406 shell/plugins/menu/Menu.qml:246–445,562–638,942–1015`.)

`locked = true` permits the compositor binding to execute while locked; it
does not turn an ordinary Overlay layer into a session-lock surface. Omarchy
lock uses `WlSessionLock`/`WlSessionLockSurface`, while its ordinary menu uses a
PanelWindow. A locked-key test must distinguish command delivery from a menu
actually being visible over the lock. In the 406 VM the real power key
reached the replacement with the `system` payload while the lock remained
secure. Host framebuffer capture showed only the lock, with the probe listed
as an ordinary layer 3 surface. It became visible after password unlock.
A separate stock-menu control behaved the same way: no system menu over
the secure lock, then the stock System card visible after unlock. Therefore
locked-key delivery is not a usable overlay above authentication.
(`406 default/hypr/bindings/utilities.lua:9`;
`406 shell/plugins/lock/Service.qml:257–275`;
`406 shell/plugins/menu/Menu.qml:1018–1027`.)

## 5. IPC takeover and notification ownership

Third-party QML can register `Quickshell.Io.IpcHandler` with target `osd` or
`notifications`; there is no manifest permission for those strings. Disable
the corresponding first-party plugin through `disabledPlugins`, enable the
replacement service, and ensure the old handler/server has gone before
testing the new one. Do not rely on duplicate-target ordering. Services are
created for enabled manifests and destroyed when disabled/removed, even when
previously retained. (`406 shell/services/PluginRegistry.qml:148–168`;
`406 shell/shell.qml:904–1026`; `406 shell/plugins/osd/Osd.qml:115`;
`406 shell/plugins/notifications/Service.qml:857,931`.)

The notification server is a `Quickshell.Services.Notifications.NotificationServer`
inside the same shell process, with `keepOnReload: false`. Replacing it does
not introduce another process. In the 406 VM, stock, replacement and restored
stock all used the **same Quickshell PID and unique bus connection** for
`org.freedesktop.Notifications`. With stock disabled and no replacement,
the IPC target disappeared but that process still owned the D-Bus name.
Do not use disappearance of the bus name as the handoff condition. Verify
handler removal, replacement receipt/dismissal, then restored stock delivery.
This is an in-process handoff, not evidence that a separate notification daemon
can acquire the name. Immediate removal/re-enabling can produce a transient
duplicate IPC-handler warning; disable and allow destruction before restoring
the other component. IPC liveness alone does not establish notification delivery.
(`406 shell/plugins/notifications/Service.qml:931–943`;
`406 bin/omarchy-notification-wait:11–26`.)

| Target | 4.0.6 methods to preserve | Callers and source |
|---|---|---|
| `osd` | `show(payloadJson)`, `close`, `state`, `ping` | `shell/plugins/osd/Osd.qml:115–125`; `bin/omarchy-osd:40`; `bin/omarchy-chromium-ytdlp-host:80`; `shell/services/AppLibrary.qml:174,245` |
| `notifications` | `dndState`, `toggleDnd`, `setDnd(value)`, `isDnd`, `showHistory`, `clear`, `dismissAll`, `dismissOne`, `invokeLast`, `dismiss(summary)`, `ping` | `shell/plugins/notifications/Service.qml:857–926`; `default/hypr/bindings/utilities.lua:24–28`; `bin/omarchy-notification-dismiss:11`; `bin/omarchy-toggle-notification-silencing:5`; `bin/omarchy-notification-wait:23` |
| `omarchy.indicators` | `refresh` | `shell/plugins/bar/widgets/Indicators.qml:168–173`; `bin/omarchy-toggle-notification-silencing:6`; `bin/omarchy-reminder:38,198`; `bin/omarchy-capture-screenrecording:246` |

All table references are **406**. DND replies are `on`/`off`; setDnd accepts
true/1/on/yes. `clear` clears history rather than visible toasts. The normal
volume path is `XF86AudioRaiseVolume` → `omarchy-audio-output-volume raise`
→ `omarchy-osd` → `osd.show`. Keep the script path working, not just a direct
probe IPC call. (`406 default/hypr/bindings/media.lua:1–4`;
`406 shell/plugins/notifications/Service.qml:860–895`.)

`omarchy-shell -q` deliberately suppresses missing-target/method failures. A
successful exit status from that wrapper is not proof of delivery: inspect a
counter/state and the resulting surface. (`406 bin/omarchy-shell:13–17,65–82`.)

IPC is only one calling path. The built-in audio/monitor panels and media
service call `shell.summon("omarchy.osd", payload)` directly. Preserve that
identity too, using the replacement metadata and a panel entry with open/close,
otherwise volume keys can work while panel/media feedback disappears.
The DND indicator reads `firstPartyServiceFor("omarchy.notifications")`;
that proxy resolves replacements and expects `doNotDisturb` and
`setDoNotDisturb(value)`. Merely registering an IPC target does not satisfy it.
(`406 shell/plugins/panels/audio/Panel.qml:436`;
`406 shell/plugins/panels/monitor/Panel.qml:259`;
`406 shell/plugins/services/media/Service.qml:248`;
`406 shell/plugins/bar/indicators/Dnd.qml:8`;
`406 shell/shell.qml:461–517`.)

For **450**, notifications exposes `ping`, `isDnd`, `toggleDnd`, `setDnd`,
`act`, `dismissOne`, `dismissAll`, `invokeLast`, `invokeAction(n)`, `keyboard`,
`showHistory`, `dismiss(summary)`, `count`, `expand`, `probe`. `act` can invoke,
dismiss or focus; keyboard mode and numbered actions are additional behavior,
not aliases for dismissal. The old `clear`/`dndState` are not declared in that
handler. (`450 shell/plugins/notifications/Service.qml:1384–1475`.)

Local handoff evidence: `vm406/guest-evidence/notification-{stock,probe,restored}-owner.txt`,
`notification-disabled-owner.txt`, `notification-result.json`, and the restored
stock toast capture. The native volume test delivered an audio payload and
the original sink volume was restored after the test.

The 450 caller audit additionally finds menu guards reading `isDnd`, the
notification demo calling `dismissAll`, and the passwordless-sudo indicator
refresh. Unchanged helpers still call show/close, ping, dismiss, toggleDnd and
indicator refresh. (`450 default/omarchy/omarchy-menu.jsonc:131–132`;
`450 shell/plugins/menu/MenuModel.js:439`;
`450 bin/omarchy-dev-notification-demo:83`;
`450 bin/omarchy-sudo-passwordless:470,488`;
`450 bin/omarchy-osd:41`; `450 shell/services/AppLibrary.qml:189,260`;
`450 bin/omarchy-notification-wait:23`; `450 bin/omarchy-notification-dismiss:11`;
`450 bin/omarchy-toggle-notification-silencing:5–6`;
`450 bin/omarchy-reminder:39,195`; `450 bin/omarchy-capture-screenrecording:506`.)

## 6. Services and access boundaries

| Need | Available path at 4.0.6 | Source |
|---|---|---|
| Audio | `Quickshell.Services.Pipewire`, normal Omarchy audio commands | `shell/plugins/panels/audio/Panel.qml:5–6` |
| Brightness | `omarchy-brightness-display`, including monitor and no-OSD options | `shell/plugins/panels/monitor/Panel.qml:248` |
| Network | `Quickshell.Networking`; Omarchy status/band commands | `shell/plugins/panels/network/Panel.qml:6,813` |
| Bluetooth | `Quickshell.Bluetooth`; Omarchy device/power commands coordinate operations | `shell/plugins/panels/bluetooth/Panel.qml:5,268,638` |
| Battery | `Quickshell.Services.UPower` | `shell/plugins/panels/power/Panel.qml:4` |
| Media | `Quickshell.Services.Mpris`; full-bar narrow media proxy | `shell/plugins/panels/audio/Panel.qml:5,21`; `shell/services/PluginFirstPartyServiceApi.qml:34–44` |
| Tray | `Quickshell.Services.SystemTray`; the widget supplies popup/menu interaction | `shell/plugins/bar/widgets/Tray.qml:1–25` |
| Compositor | `Quickshell.Hyprland` and `hyprctl`/official command helpers | `shell/plugins/bar/Bar.qml:2`; `shell/Commons/Style.qml:350–388` |
| Processes/files | `Quickshell.Io.Process`, `FileView`, `Quickshell.execDetached` under the user's identity | `shell/plugins/panels/bluetooth/Panel.qml:4,638`; `shell/shell.qml:124–145` |

These are normal imported modules/commands, not additional Omarchy manifest
capabilities. A plugin still obeys ordinary OS/device/polkit permissions.
The *host facade* restricts cross-plugin service objects: ordinary plugins get
their own service, menus are intended to get AppLibrary (see the runtime
blocker in section 4), full bars get the narrow
non-auth proxies described above. Authentication capabilities come from trusted
first-party metadata and cannot be obtained by writing an arbitrary capability
string. Lock/polkit state is deliberately outside the public object tree.
This is an API boundary, not a sandbox for same-process QML.
(`406 shell/services/PluginRegistry.qml:92–115`;
`406 shell/shell.qml:394,592–654,904–947`.)

**Recommendation:** read state through supported modules/commands and keep
collection separate from display. Do not traverse host QObject parents to
retrieve services withheld by the facade. Agent command metadata and JSON
outputs belong in the later product plan, not these probes.

## 7. Theme surface and complete field inventory

The generated [shell field inventory](shell-theme-fields.csv) lists every
active and commented key in both pinned `default/themed/shell.toml.tpl` files,
including line numbers, defaults and removals. It can be reproduced with
`inventory-theme.py` without executing upstream code. The parser is deliberately
small: section names and string/number/width-list/bare tokens, not arbitrary
TOML structures. Unknown keys can parse without having a consumer.
(`406 shell/Commons/Color.qml:178–202`.)

The full consumer-facing groups are:

| Section | Fields / families |
|---|---|
| `bar` | background, background-alpha, text, active, scale-with-font, size-horizontal, size-vertical; additional consumer tokens icon-slot, icon-canvas, icon-font, status-slot |
| `hyprland` | active-border, active-border-foreground |
| `controls` | normal / hover-cursor / focus / selected color, fill-alpha, border, border-width, border-alpha; pressed-color, pressed-fill-alpha, selection-color, selection-fill-alpha |
| `spacing` | scale, scale-with-font; xxs/xs/sm/md/lg/xl/xxl/xxxl/huge; control-gap, control-padding-x/y, input-padding-y, control-height, popup-row-height, row-gap, row-padding-x, label-gap, panel-gap, panel-padding, popup-padding, dropdown-width, searchable-dropdown-width, number-field-width, searchable-popup-min-height |
| `font` | base-size; caption, body-small, body, subtitle, title, heading, display, display-large, icon-small, icon, icon-large |
| `popups`, `tooltip` | background, background-alpha, text, border, border-alpha, border-width family |
| `notifications` | popup fields plus countdown |
| `menu`, template `launcher` | background, background-alpha, text, border, border-alpha, scrim, scrim-alpha, selected-background, selected-background-alpha, selected-text, selected-border, selected-border-alpha |
| `polkit` | background, background-alpha, text, text-error, border, border-error, border-alpha, scrim, scrim-alpha, accent |
| `lock` | background, background-alpha, text, placeholder, text-error, border, border-active, border-error, border-alpha, selection, selection-alpha |
| `image-picker` | text, selected-border, selected-border-alpha, unselected-border, unselected-border-alpha; 406 also has scrim/scrim-alpha, removed from 450 template |

Sources: `406 default/themed/shell.toml.tpl:5–237`;
`406 shell/Commons/Style.qml:71–93,232–261,317–348`;
`406 shell/Commons/Color.qml:73–132`;
`450 default/themed/shell.toml.tpl:226–235`.
The `launcher` section remains in the template but is not a separate Color
singleton role at 406; do not assume every template key changes a live surface.

Border consumers accept a solid color or gradient, optional `-alpha`, and
CSS-style `border-width` lists with top/right/bottom/left overrides. Legacy
`border-gradient` variants are compatibility inputs. These parameterized
families are additional to the finite template inventory. Rounding/gaps also
come from Hyprland state; the font family follows fontconfig rather than a
general `[font] family` setting; `OMARCHY_MENU_FONT` is a startup environment
override for menu-family consumers. (`406 docs/theming.md:201–240`;
`406 shell/Commons/Style.qml:270–278,350–388`.)

`colors.toml` is an extensible flat key dictionary, not a closed schema. Its
canonical palette is `mode`, `accent`, `selection`, `muted`, `background`,
`dark_background`, `darker_background`, `lighter_background`, `foreground`,
`dark_foreground`, `light_foreground`, `bright_foreground`, `red`, `yellow`,
`orange`, `green`, `cyan`, `blue`, `magenta`, `brown`, and bright variants of
red/yellow/green/cyan/blue/magenta. Compatibility includes bg/fg short forms,
purple/bright_purple, color0–color15, theme_type and selection_background /
selection_foreground. Derived cursor is bright_foreground. Additional template
keys such as `hyprland_active_border` are legal. Mode resolves explicit mode,
legacy theme_type, light.mode, then background luminance/default dark.
(`406 bin/omarchy-theme-color:113–280`;
`406 themes/tokyo-night/colors.toml:1–31`.)

Templates support `{{ key }}`, `_strip`, `_rgb`, mix helpers and gradient
helpers. User `~/.config/omarchy/themed/*.tpl` run before built-ins; existing
staged outputs win. A theme's `shell.<section>.toml` can replace one section.
The active theme lives under `~/.local/state/omarchy/current/theme`.
`~/.config/omarchy/shell.toml` overrides the theme live and survives switches;
the theme's files load at startup and refresh through explicit theme IPC.
(`406 bin/omarchy-theme-set-templates:370–400`;
`406 docs/theming.md:18–43,177–199`;
`406 shell/Commons/Color.qml:204–251`.)

Theme assets include `backgrounds/`, previews, `unlock.png`, `icons.theme`,
`keyboard.rgb` and `light.mode`; user backgrounds overlay the selected theme.
**Git-installed themes are filtered when staged:** all Lua files (including
hyprland.lua/neovim.lua/gum_env.lua), terminal launch configs, vscode.json and
symlinks are dropped; corresponding official generated outputs are used.
Therefore a public git theme cannot promise that its own hyprland.lua or app
executable configuration will run. User-authored overrides/templates are a
separate supported configuration path. (`406 docs/theming.md:9–66`.)

Lock and polkit theme roles affect color, borders, text, scrim and shared
spacing/type; they do not replace authentication layout/lifecycle or expose
credential data. Plymouth's theme command reads `colors.toml` background and
foreground plus `unlock.png`, then invokes the system-level Plymouth command.
It is explicitly marked as requiring sudo; this optional owner action must
remain distinct from a no-sudo WULING plugin/theme installation.
(`406 default/themed/shell.toml.tpl:189–224`;
`406 bin/omarchy-plymouth-set-by-theme:3–53`.)

Theme activation dispatches terminal, Hyprland, btop, editor/browser and agent
retint commands, including foot/tmux/GNOME/Pi/Claude/Hermes/T3Code/VS Code/
Obsidian/keyboard. Hook files under `~/.config/omarchy/hooks/theme-set*` receive
the theme name. Application-specific limits remain those of each helper;
shell.toml alone does not theme applications.
(`406 bin/omarchy-theme-set:318–338`; `406 docs/theming.md:40–46`.)

## 8. Plugin settings and reload

`shell.json` version 1 holds inline settings on `plugins[]` or
`bar.layout.<section>[]` entries, plus bar selection and disabledPlugins.
There is no universal `config:` nested object or multilayer plugin settings
schema. `shell.updateEntryInline(id, settings)` replaces the matched entry's
settings while preserving its id; callers must retain keys they want to keep.
The host writes atomically, watches the file, and updates bindings.
(`406 shell/shell.qml:111–145,1080–1119`; `406 docs/omarchy-shell.md:110–156`.)

The plugin directory watcher observes close-write/create/delete/move, ignores
hidden staging and .git changes, rescans and reloads affected code. A retained
service's lifecycle differs from an ordinary UI entry; avoid depending on hot
reload as if it were a clean process restart. Data/history/cache should live
outside the code checkout, with an explicit format chosen by the plugin.
(`406 shell/services/PluginRegistry.qml:656–739`;
`406 shell/shell.qml:1030–1050,1455–1495`.)

## 9. UI sounds

Plugins can start ordinary user programs through Process/execDetached without
loading Qt Multimedia. Omarchy includes PipeWire in its package set; the 406 VM has
`/usr/bin/pw-play`, owned by `pipewire-audio 1:1.6.9-1` (read-only `pacman -Qo`).
(`406 install/omarchy-other.packages:34–37`;
`406 shell/plugins/panels/bluetooth/Panel.qml:638`.)

**Recommendation:** initially use `Process` with an argv array invoking
`pw-play` for an installed local WAV/OGG, bounded overlap and cancellation.
This keeps Qt Multimedia out of the shell and avoids an additional custom
daemon for a first implementation. Measure launch latency before deciding
whether a small persistent PipeWire helper is warranted. Login music stays
local and opt-in per project decisions; it is not part of these probes.

## 10. Default bindings and reversible overrides

Use the user's `~/.config/hypr/bindings.lua`, loaded after defaults, with
`hl.unbind("...")` followed by `o.bind(...)`; do not edit packaged defaults.
`o.bind` accepts a command or dispatcher and carries description/options.
(`406 manual/31-dotfiles.md:62–74`; `406 default/hypr/helpers.lua:92–106`.)

| Key | 4.0.6 | 4.5.0-rc2 |
|---|---|---|
| Super+Space | Omarchy menu root | Omarchy menu root |
| Super+Alt+Space | Omarchy menu apps | `omarchy.dock apps` |
| Super+Escape | system menu | system menu |
| XF86PowerOff | system menu, locked allowed | system menu, locked allowed |

Sources: `406 default/hypr/bindings/utilities.lua:1–9`;
`450 default/hypr/bindings/utilities.lua:1–9`.

**Installation proposal, not implemented:** inspect effective bindings and the
user file first. Offer a generated, owned include/block that changes only the
selected variant's keys, preserving flags and documenting the displaced
binding. Refuse automatic takeover if a key has a conflicting user override
unless the user explicitly selects it. Save the prior bytes/hash and a record
of the inserted block. Removal deletes only an unchanged owned block; if the
user edited it, report the conflict instead of overwriting their file. Reload
Hyprland and check effective bindings after both operations. Removing the
block restores current packaged defaults naturally; do not replay an old
packaged default over a newer Omarchy version.

## 11. Installation, update and monorepo implications

`omarchy plugin add <git-url>` validates the URL, clones into a temporary
directory, validates **one root manifest.json**, checks id collisions, moves
to `~/.config/omarchy/plugins/<id>`, rescans, then optionally enables. A
noninteractive/--yes add defaults to disabled unless `--enable` is supplied.
No subdirectory selector or multiple-manifest installation is present.
One manifest may declare multiple kinds but has one id and one entry per kind.
Third-party discovery only scans immediate child directories.
(`406 bin/omarchy-plugin-add:96–165`;
`406 bin/omarchy-plugin-validate:23–36,111–116`;
`406 shell/services/PluginRegistry.qml:689–719`.)

Update fetches origin HEAD, shows a diff, confirms and fast-forwards, validating
afterward and rolling back a failed validation. Removal disables/rescans and
deletes a git checkout, unlinks a symlink, or backs up a non-git directory;
clone-specific restoration does not automatically define restoration for a
new independently written replacement plugin.
(`406 bin/omarchy-plugin-update:25–78`;
`406 bin/omarchy-plugin-remove:82–120`.)

**Packaging implication:** the planned monorepo of separable plugins plus a
theme cannot be installed completely by one `omarchy plugin add` call. Options
for a later design decision are generated single-plugin distribution repos,
or a documented user-level installer that places each plugin through the
supported manual-directory mechanism and installs the theme separately.
Internal symlinks are rejected by plugin validation; a shared UI kit must be
packaged coherently rather than linked out of a plugin to an arbitrary tree.
Any custom updater must preserve user settings and explicitly restore disabled
built-ins. No installer or distribution decision is implemented in A-1.

## 12. Language integration

4.5 reads the user's `~/.config/omarchy/language` registry code. `I18n` exposes
language, formatLocale, translations, plural/number formatting and direction.
`Commons.Translations` loads plugin-local `en.json`, base-language JSON and
exact-language JSON with fallback in that order; bound `t()` / `tn()` calls
rerender on changes. Use zh-TW for Traditional Chinese and zh-CN for Simplified
Chinese, not an invented system code. Manifest names/descriptions are not yet
translated. (`450 docs/i18n.md:7–25,41–51`;
`450 shell/Commons/Translations.qml:5–100`.)

4.0.6 lacks that module. **Recommendation:** isolate locale adaptation from
visual components and load a version-appropriate adapter so a missing import
cannot break all of 4.0.6. At 450, follow the Omarchy language file and format
locale, not only inherited LANG. The exact 406 fallback policy needs a design
decision before product code.

## 13. Compatibility changes requiring explicit handling

| Area | Change in 4.5.0-rc2 | Source |
|---|---|---|
| Bar layout | left, centerBegin, center, centerEnd, right, tray; default third-party placement is centerEnd, not center; tray cannot contain itself | `450 shell/Commons/Util.qml:179`; `shell/services/PluginRegistry.qml:194–204,253–290` |
| Notifications | New action/focus/keyboard/expansion behavior and IPC; changed default shortcuts | `450 shell/plugins/notifications/Service.qml:1384–1475`; `default/hypr/bindings/utilities.lua:24–31` |
| Apps | Default Super+Alt+Space goes to dock apps | `450 default/hypr/bindings/utilities.lua:2` |
| Overlays | Shared focused-monitor/scale-aware OverlayWindow, RTL support | `450 shell/Ui/OverlayWindow.qml:7–101` |
| Language | Plugin catalogs, live locale, translated menu before extensions | `450 docs/i18n.md:7–25` |
| Theme | Image picker drops scrim template keys; recheck actual consumer before promising a token | `450 default/themed/shell.toml.tpl:226–235` |
| Plugin watcher | Reaps orphaned watcher processes before starting a replacement | `450 shell/services/PluginRegistry.qml:679–715` |

The basic scoped shell API and service-less hosted-widget boundary remain in
the source. The 406 experiments use its real default keys. The separate 450
runtime matrix is completed in A-2 (§17): five functional probes, facade
control, six-section catalog and dock exception. Do not carry the 406
passive-notification result over to 450's full `act` behavior.

## 14. Runtime cost and experiment results

### Environment and stock checkpoint

Fresh Omarchy 4.0.6 ISO plus local cidata, followed by official `omarchy update -y`
and a reboot. No old WULING payload is installed. Core package versions:

| Package | Installed version |
|---|---|
| omarchy | 4.0.6-1 |
| hyprland | 0.56.2-4 |
| quickshell | 0.3.2.r7.g2b4501a-1 |
| qt6-base | 6.12.0-3 |
| qt6-declarative | 6.12.0-2 |
| mesa | 1:26.2.5-1 |
| pipewire-audio | 1:1.6.9-1 |

The installed shell.qml, PluginRegistry.qml and MenuModel.js hashes match the
406 source snapshot. The VM uses KVM, 8 vCPUs, 8 GiB guest RAM and virtio-vga-gl
with host llvmpipe rendering. Host execution is nice 15 with idle I/O priority.
1366×768 and 1920×1080 were verified through compositor output state and
captures. The offline `original-omarchy-406` checkpoint contains stock Omarchy
following the official update; `a1-clean-406` is the restored latest checkpoint.
Both are offline disk snapshots without a saved RAM image. The retained ISO's previously verified SHA256
is `b542db5fecc37395d9af6654a8146ebed225f275ae4d5a6fcf432e40afe7bb88`.

### Functional checks on 406

| Probe | Observed result | Local evidence under `vm406/` |
|---|---|---|
| Bar | Replacement at both requested sizes; one bar on each of two outputs. Horizontal edges reserve 26 px, vertical edges 28 px on both | `bar-r2-test.log`; `guest-evidence/bar-*-monitors.json`, captures and `bar-two-layers.json` |
| OSD | Real volume key reached `osd.show`; direct built-in-id summon also reached the probe. Native OSD and original volume restored | `osd-test.log`; `guest-evidence/osd-volume.json`, `osd-identity.json`, `osd-native-restored.png` |
| Notifications | notify-send receipt, Super+comma dismissal via dismissOne, same-process D-Bus ownership, restored stock toast | `notifications-test.log`, `supplemental-test.log`; notification evidence listed in section 5 |
| Focus | Temporary compositor binding opened Exclusive-focus overlay; physical Esc closed it and incremented the counter | `focus-test.log`; `guest-evidence/focus-result.json` and capture |
| Menu routes | No-metadata negative control, all six original key combinations, command/user aliases, runtime JS import and guard controls | `menu-r3-test.log`, `menu-r3-resume.log`; `guest-evidence/menu-routes.json`, `menu-tree.json` |
| Locked power key | Command delivered while secure, ordinary overlay hidden until unlock; stock menu control agrees | `menu-locked-host.png`, `stock-menu-locked-host.png`; `guest-evidence/menu-locked-*.json` and after-unlock captures |
| Menu facade | Fails independently of the route reader; overlay control retains facade; delegate sequence type mismatch reproduced | `guest-evidence/facade-*.json`; section 4 and `spikes/facade/` |

The second output is a compositor-created headless output, not a physical
connector/hotplug test. Bar catalog visibility is not full widget compatibility.
The notification probe covers passive delivery/dismissal, not every history or
action method. The menu probe does not implement app/provider/search parity,
and its counted public-CLI close fallback does not pass the facade check.

Each probe's configuration inventory was restored exactly (path, type, mode,
link target and file SHA256). Inventories and empty difference lists are in
`guest-evidence/{bar-r2,osd,notifications,focus,menu-r3,notification-gap}/`.
The first bar attempt stopped because the pilot allowed idle lock; it was
removed with an empty inventory diff and rerun. Early menu attempts exposed
the facade defect and an incorrect test expectation for background/theme
aliases; the recorded final route checks use the upstream resolved ids.

### Cost method

Formal stock → empty service → restored stock runs each start a fresh shell
process, warm for 20 seconds and sample for 120 seconds at 4-second intervals
(31 samples). Geometry is 1366×768. All three use the official stay-awake
control; before/after checks require an unlocked session, active DPMS and the
same geometry. The prior idle state is restored after testing. An earlier
pilot that relied on modifier-only input was affected by idle lock and is
excluded, with its raw logs retained under `invalid-idle-*`.

Read shell PSS from smaps_rollup and CPU ticks from /proc; CPU is a percentage
of one logical core. QEMU/host rendering CPU and memory are separate, including host-side virgl
textures. CPU tick resolution is about 0.0083 percentage points over a 120-second
run, so these very small CPU values are coarse. These VM/virgl figures do not predict a physical GPU.

| Fresh-process run | Mean PSS (MiB) | PSS range (MiB) | Idle CPU (%) |
|---|---:|---:|---:|
| Stock A | 297.05 | 295.49–297.39 | 0.0166 |
| Empty service B | 290.77 | 288.45–291.39 | 0.0167 |
| Restored stock A2 | 293.20 | 290.15–294.05 | 0.0416 |

All before/after condition checks passed. The empty service produced no measured
increase in these runs, but its allocation is **not resolved** by this small
sample: B is below both stock means and the two stock means themselves differ
by 3.85 MiB. This is neither evidence of a memory saving nor a zero-cost claim.
The method measures whole-process PSS, including sharing/startup variation;
it is not an allocator accounting experiment. Raw samples and conditions:
`guest-evidence/cost-fresh-{a,empty,a2}.json` and matching `-conditions.json`;
run summaries: `cost-fresh-{a,empty,a2}.log`.


## 15. Agent integration

User provisioning links each directory in
`$OMARCHY_PATH/default/agents/skills/` into the user's `.agents/skills`,
`.claude/skills`, `.codex/skills`, `.pi/agent/skills`, `.hermes/skills` and
existing Hermes profiles. The three requested migrations relink only named
Omarchy skills or names present in that source directory; they do not clear
the destination directories. (`406 bin/omarchy-provision-user:84–103`;
`406 migrations/1786098807.sh:1`, `1786539345.sh:1`, `1787843905.sh:1`.)

**VM experiment, 406:** a dummy `wuling` skill symlink and content survived
`omarchy update -y` and explicit reruns of all three migrations in all five
directories. The probe then removed only its five links and sentinel folder.
The official update completed with exit 0. This establishes behavior for these
versions; a future upstream skill using the same name would be a collision.
Local evidence: `vm406/guest-evidence/agent-check.log`, `vm406/update-result.json`.

`omarchy commands --json` returns `{ok: true, commands: [...]}`. Each record
contains route, binary, group, name, summary, requires_sudo, hidden, args,
examples, aliases, filename_route and routes. Metadata comes from `# omarchy:`
comments. Discovery scans **only `$OMARCHY_PATH/bin/omarchy-*`**; it does not
add commands from arbitrary PATH entries or plugin bin directories.
(`406 bin/omarchy:167–294,313–339,642–692`.)

**VM experiment, 406:** a disposable executable in `~/.local/bin` ran directly,
but `omarchy wa1 probe` was rejected and the command was absent from the JSON
catalog (369 visible records). Therefore WULING should expose its own `wuling`
command catalog rather than install into the packaged Omarchy bin directory.
Local evidence: `vm406/guest-evidence/agent-check.log`.

Super+Shift+Ctrl+A calls `omarchy-agent --pick`. It reads the default agent;
with none selected it opens `setup.default.agent`, otherwise launches the
agent through the normal terminal helper with a common app id. Prompts use
`omarchy-agent-prompt` → `omarchy-agent --prompt`; inline mode is distinct.
`omarchy-agent-crash` gathers core metadata and directs the chosen agent to
the installed diagnose-crash skill. These are existing Omarchy workflows,
not a reason to introduce an agent credential store in WULING.
(`406 default/hypr/bindings/utilities.lua:96`;
`406 bin/omarchy-agent:37–140`; `406 bin/omarchy-agent-prompt:7–23`;
`406 bin/omarchy-agent-crash:7–52`.)

The agent panel separates collection from display. `omarchy-agent-usage-update`
runs collectors and atomically replaces per-agent JSON files under
`${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/usage/`. Main.qml discovers
and watches those files. The display record includes id/name/ready,
usageStatusText/authHelpText, limits/tierLabel/balance, today's prompts,
sessions/tokens/model breakdown, recentDays, total prompts/sessions,
activeDays, modelUsage and flags for available stats. Rate limits and account
balances remain local; optional cross-device aggregates apply to usage counts.
(`406 bin/omarchy-agent-usage-update:4–51`;
`406 shell/plugins/agents/Main.qml:5–77,212–275`.)

**Recommendation:** consume the existing JSON and documented collector command
for WULING's bar/Terminal; tolerate missing/new fields and collector failures,
avoid logging account content, and share one collection schedule rather than
start a collector per visual component. Do not copy Main.qml's implementation.
The Claude app template already maps theme palette, selection, status, prompt
and diff colors into its JSON theme; use that theme path instead of a separate
agent-specific WULING palette. (`406 default/themed/claude.json.tpl:1–43`.)

## 16. Reusable development checks

| Tool / workflow | Third-party use and boundary | Source |
|---|---|---|
| `omarchy plugin validate DIR` | Directly useful for each staged plugin; validates manifest, reserved ids, entry points and symlinks. It does not execute QML or prove rendering | `406 bin/omarchy-plugin-validate:23–116` |
| `test/all`, `test/cli`, `test/shell.d` | Upstream repository regression suites, not a generic plugin runner. Run against the pinned source in a disposable environment; use them as dependency checks, and give WULING its own tests | `406 test/all:3–23`; `test/shell:4–36` |
| `test/acceptance`, `test/acceptance.d` | Exercises an installed desktop over SSH, discovers session environment, records artifacts; shared helpers can be sourced from the installed/test checkout. Run only in a disposable VM and restore modified state | `406 test/acceptance:1–70`; `agents/skills/acceptance-tests.md:5–40` |
| Visual verification | Official fullscreen capture and short recordings, followed by inspection for clipping/focus/stale state. QMP input proves global shortcuts; wtype alone does not | `406 agents/skills/visual-verification.md:5–43`; `agents/skills/acceptance-tests.md:42–44` |
| `omarchy dev link` | For a complete Omarchy checkout, changes system OMARCHY_PATH/sudo resolution and requires reboot for a coherent session. It is not a plugin installation mechanism and is unnecessary for WULING-only development | `406 bin/omarchy-dev-link:3–42,93–123` |

No upstream files need modification to install these disposable plugins.
The proposed long-term structure is in [maintainability.md](maintainability.md).

## 17. A-2 runtime findings (v400 / v401)

**The registered-widget host and the overlay replacement are viable research
paths on both tested versions.** The host needs a real compatibility layer;
importing MenuModel.js does not make a replacement menu behaviorally equivalent.
The native System extension works on both versions without changing bindings.
These are independent experiments, not a product implementation or approval to
use internal APIs indefinitely. Evidence below is local under `wa2/`; no logs,
raw JSON, screenshots or theme images are in git.

### 4.5.0 release (phase I)

Omarchy 4.5.0 replaces the release candidate as the tested 4.5 version. The
signed x86 ISO installs `omarchy 4.5.0-3`, the stable repository's version at
the time, with Hyprland 0.56.2-4, Quickshell 0.3.2.r7, Qt 6.12.0 and Mesa
26.2.5, the same as rc2. Of the files in `/usr/share/omarchy` that are also in
the `v4.5.0` tag, all match it except `install/helpers/logging.sh`, which only
the installer uses. Between `v4.5.0-rc2` and `v4.5.0`, 130 commits change 27
files under `shell/`. None of them is in `shell/Commons`, `shell.qml`, the
panel host (`Ui/Panel`, `Ui/KeyboardPanel`, `Ui/PluginBarApi`,
`Ui/OverlayWindow`), the bar widget registry or the plugin shell facade, and no
IPC method WULING calls changed signature. The rc2 observations below still
hold for those files.

The content gates check file hashes, not the version string:

| Gate | Installed files hashed | 4.0.6 | 4.5.0 |
|---|---|---|---|
| Notifications (`plugins/notifications/native-modules.json`) | `shell/plugins/notifications/` `NotificationLogic.js` (4.0.6); `Store.js`, `Security.js`, `Delivery.js`, `Markup.js`, `Detect.js` (4.5) | contract `4.0.6` | contract `4.5.0`: the rc2 hashes, unchanged in the release |
| Theme wave (`plugins/session/native-theme.json`) | `bin/omarchy-theme-set`, `shell/Commons/Color.qml`, `shell/Commons/Style.qml`, `shell/plugins/background/Background.qml` | contract `4.0.6` | contract `4.5.0`. Two files differ from rc2, neither in a still background's timing: `omarchy-theme-set` sends the intro's output to `/dev/null`, and `Background` keeps the last still when a video background is chosen, until OWE takes over |

`omarchy version` prints `4.5.0-3`; the installer and `wuling doctor` treat
`4.5.0` with any package release as tested, and a release candidate as
untested.

Changes in 4.5.0 that WULING follows:

- **Transient notifications.** The native store no longer keeps a card with
  the `transient` hint, live or in history (`shell/plugins/notifications/Service.qml`
  `storePut`). `omarchy-notification-send --transient` is new, and
  `omarchy-migrate-notify` sends its reminder with it at every login. WULING's
  service shows such a card and keeps nothing of it on 4.5.0.
- **The bar under a full-screen window.** The native bar fades and takes no
  input on a workspace with a real full-screen window, because Hyprland 0.56
  lifts layers back above full screen; its tooltip stays transparent until the
  surface has the bar's fractional scale (`shell/plugins/bar/Bar.qml`).
- **Region-capture binds.** The screenshot selection now binds its keys only
  for the selection and leaves them disabled afterwards
  (`default/hypr/bindings/utilities.lua`, `selection_keys`). From the first
  selection until a configuration reload, `hyprctl binds` lists all eight,
  enabled or not, as bare `__lua` binds with no description and no field that
  tells them from a user's own. The Keymap takes their chords from that table,
  gated by the table's own hash.

Changes with no effect on WULING: the clock widget's `WallClock` timer (the
members the bar skin reads remain), `omarchy-toggle-nightlight` (same
`--status` output), `omarchy-hibernation-available` (also requires `disk` in
`/sys/power/state`, which the power cards follow), the plugin registry's clone
restore (WULING's clones have one kind each), the media service's idle-player
choice, and install and remove entries in the menu.

### RC update and differences affecting WULING

The independent RC disk completed official `omarchy channel set rc` and
`omarchy update -y`: installed Omarchy 4.5.0rc2-1, Hyprland 0.56.2-4,
Quickshell 0.3.2.r7.g2b4501a-1, Qt base 6.12.0-3 / declarative 6.12.0-2,
Mesa 1:26.2.5-1. Installed shell, registry and MenuModel hashes match the pinned
450 source. The initial update invocation ended with status 143 without a
conclusive cause; the subsequent official update completed with status 0.
No manual package replacement or upstream patch was used.

All five A-1 functional probes passed on RC: bar at both resolutions, four
edges and two outputs; volume-key OSD; notification D-Bus handover and dismiss;
focused overlay; runtime menu tree with true/false guards and checked rows.
Each probe restored its owned configuration. RC has 422 default menu rows,
compared with 333 at 406. See `vm450/*-test.log`, `menu-facade-test-r2.log` and
its collected guest evidence. A-1's cost experiment was not repeated in A-2.

| Contract | 406 | 450 runtime / implication |
|---|---|---|
| `menu` facade | Revoked in minimal control, AppLibrary unavailable | Stable, AppLibrary available. The delegate now reads the original registry manifest rather than its model-converted copy (`450 shell/shell.qml:1398`). The isolated sequence conversion is still reproducible, but does not revoke this facade. |
| Overlay facade | Stable; no AppLibrary | Same; public DesktopEntries is an independent option with different launch semantics. |
| Super+Alt+Space | Menu apps route | Dock, outside the menu replacement mechanism. |
| Background/theme aliases | `style.background`, `style.theme` | `appearance.background`, `appearance.theme`. Resolve through installed model rather than hard-coded paths. |
| Network shortcut | Super+Ctrl+W | Super+Ctrl+N; W opens background selection (`450 default/hypr/bindings/utilities.lua:15,106`). |
| Bar layout | left / center / right | Six sections including centerBegin / centerEnd / tray; default catalog loads into the independent host. |
| Transparent CLI | `bar.transparent` boolean | Writes `bar.background="none"`; false maps to opaque. The probe handles both (`450 bin/omarchy-bar:223–272`). Glass mode remains outside this probe. |
| Shared panel facade | Basic coordination | Additional tray-section state and popout-card geometry callbacks. |
| Menu request/reply | select/input, single selection | Adds multi-select, preselection and on-change commands/change keys; ignoring these breaks callers. |
| Language | English menu model | Shipped rows translated before user extensions, English search terms retained. A replacement must call this logic as well. |

The successful 450 facade control supersedes the earlier source-only uncertainty
in §4/§13. It does not retroactively change the 406 result.

### Thin host, panels and input skin

The independent [host](spikes/bar-host/) is **316 QML lines**, with all 14
requested default widgets loaded from the installed registry. The complete
[member contract](bar-host-contract.md) names consumers, failure behavior and
version differences. The four icon/status metric mirrors are not overrides:
native widgets read Style.bar directly. The [mouse/keyboard matrix](bar-host-matrix.csv) separates
working interactions from unavailable hardware/data. Default panel shortcuts,
numbered right-section panel selection, Esc, outside clicks, mutual exclusion
and Tab were exercised through QMP, with shell IPC used for inspection.
Native arrow behavior is preserved: for example audio arrows operate its
volume/cursor, while the probe Terminal's horizontal arrows switch panels.

The CLI layout controls and watched shell.json updates worked on both versions.
Panel anchors followed top/bottom/left/right. Moving audio to the left moved its
popup anchor; changing clock format updated its label. With a physical virtual
output and a second headless output, a QMP shortcut opened audio only on the
currently focused output. See `vm*/host-layout*.log`, `host-layout.json` and
`shots/*-host-{top,bottom,left,right}-audio.png`.

The Terminal model imports installed `qs.Ui.Panel` / `KeyboardPanel`. Its QMP
shortcut, Esc, outside click, audio handoff, Tab and arrows worked under both
native bar and independent host on both versions. Switching from the host to
the native bar used an official shell restart after the 406 hot-switch pilot
left stale/duplicate handlers. Clean hot replacement is **not** established.
See `vm*/overlay-terminal-both-bars.json` and `spikes/terminal-widget/`.

VM limitations are material: no Bluetooth adapter, battery, brightness device,
SNI application or pending-update indicator. Bluetooth's default shortcut
showed its no-adapter panel. Power had no visible panel; in the 406 probe its
invisible `opened` flag could remain set, so visible-panel mutual exclusion is
reported separately. Agents was hidden at 406 with no account data; its native
empty-state panel was captured separately. A temporary US/German layout fixture
made the keyboard widget testable and was removed. Weather became available
once its native data arrived. No hardware success is inferred from component
loading alone.

For v401, the host draws its own Barlow Condensed **21 px** clock text and a
volume percentage, while an opacity-zero Loader fills exactly the same slot
with the native widget. `visible` stays true. Both versions passed clock left
(calendar), right (format and width update), middle (timezone selection), default
calendar shortcut, audio left and audio wheel. Popup screenshots remain fully
visible and correctly anchored because each popup is an independent window.
See `shots/*-host-skin-{bar,clock,audio}.png` and `vm*/host-matrix-rest*.log`.
Qt documents that Item opacity does not disable input; the runtime proof also
checks these particular upstream components. [Qt Item opacity](https://doc.qt.io/qt-6/qml-qtquick-item.html#opacity-prop).

This is a workable adapter for these two components, with explicit costs:

- Bind the visible label to the native state (`displayText`, current PipeWire
  sink volume); otherwise format changes and service updates can disagree.
- Let the host own width from its label plus padding and constrain the native
  Loader to that width. Reading native implicitWidth as a second layout owner
  can cause loops or mismatched hit areas. Recompute adjacent slots and anchors
  when a clock format or volume digit count changes.
- Keep native enabled/visible state and lifetime. A hidden/disconnected native
  widget cannot supply input; opacity also hides its built-in hover/pressed/open
  indicators, so an eventual host must decide which visible feedback to draw.
- These native state properties and button geometry are internal dependencies.
  A future popup changed from a separate window to an in-tree item could inherit
  transparency. Recheck both interactions and pixels after upstream updates.
- The probe's vertical own clock text is intentionally basic, not a finished
  vertical design. Drag, overflow and complete hover behavior are not implemented.

The native-bar control uses the draft shell.toml and stores
`bar.fontFamily="Geist Mono"`. Native `Bar.qml:72` still reads
`Style.font.family`; that JSON key does not change its font. The independent
host deliberately honors it. Neither setting adds a continuous baseline,
custom section separators or an arbitrary center ornament to the native bar.
Those require a replacement host or additional supported widgets, not color
keys. Planning estimates for host hardening and drag are in the contract file.

### Overlay route takeover and the work behind Dispatch A

The overlay manifest with `clonedFrom: omarchy.menu` passes plugin validation.
On both versions it keeps its shell facade and can close itself without the
406 menu-probe CLI fallback. All menu-bound default keys and power-menu,
settings and a user-extension alias reach it; the 450 dock exception is verified
by an unchanged call count. Both bars were tested. Public DesktopEntries listed
apps, and selecting Chromium launched an actual client in each bar control.

Enabling the replacement disables **all kinds of the source menu plugin**.
Consequently its native bar-widget registration disappears: the independent
host's menu slot has no component/zero width, and the native bar loses its menu
button too. Declaring only overlay does not preserve the source's other kind.
A replacement needs its own small bar-widget if that button is required.

`DesktopEntry.execute()` is not an AppLibrary-equivalence guarantee: the public
API currently ignores terminal requirements and field codes. The simple Chromium
launch proves only the path exercised. [Quickshell DesktopEntry](https://quickshell.org/docs/v0.3.0/types/Quickshell/DesktopEntry/).
On 450 a genuine menu-kind plugin can instead use the now-working AppLibrary
facade, subject to the version-specific contract and its parity tests.

The complete shipped lexical caller inventories are
[406](menu-request-callers-406.csv) and [450](menu-request-callers-450.csv),
including transitive scripts and JSONC actions. Reproduce with
`menu-request-callers.py /path/to/checkout`. A conditional caller is a potential
path, not a claim every invocation opens a picker. User extensions and external
CLI callers can add more and cannot be exhaustively enumerated by shipped code.

The direct select callers cover keybindings (desktop, tmux and herdr), file
selection, timezone, plugin enable/disable/clone/remove, theme removal, webapp
and TUI removal, RetroArch core selection, transcode format/resolution and webcam
selection. The native clock's middle button adds
`plugins/panels/clock/BarWidget.qml:155` (406) / `:171` (450) → timezone → select.
No additional shipped direct `menu-input` caller was found; the public input
CLI itself remains part of the replacement contract. Theme/background/Plymouth
image pickers use the separate image-selector / image-picker request path and
are not automatically replaced by `omarchy.menu`.

Both select and input create a selection file and wait for a done file. A
replacement must finish on accept **and cancel**, preserve row encoding, output
and exit semantics, multiple selection and requested size. In 450 it must also
handle preselected rows and on-change argument arrays/change keys. The probe
intentionally does not implement these protocols; using it as a daily menu
would leave native selection callers waiting. Sources: `406 bin/omarchy-menu-
select:70–100`, `omarchy-menu-input:28–61`; `450 bin/omarchy-menu-select:109–147`.

| §4 rule | Runtime import can supply | Replacement still owns |
|---|---|---|
| 1–2 parsing / normalization / merge | MenuModel helpers, exact installed semantics | File watching, error/reload lifecycle, preserving extension behavior |
| 3 when / checked | Guard script generation and interpretation helpers | Process scheduling, pending reruns, refresh and stale-result handling |
| 4 routes / aliases | Installed route resolver | Dispatch, action execution, links, lock-aware application policy |
| 5 navigation / request-reply | Some pure model helpers | History/back state, selection protocol and cancellation; UI focus/lifecycle |
| 6 search / ordering | Matching and score helpers | Current/deep grouping, query state, viewport and keyboard parity |
| 7 apps / providers | Pure row helpers; 450 menu facade has AppLibrary | Provider subprocesses, volatile cache, refresh/deletion/icons; 406 launch parity |
| 450 translation | Installed translation helper | Locale changes, loading translation data, translated/English search tests |

Estimate: **15–25 engineering days** for one-version behavioral equivalence and
reviewable tests, plus **5–10 days** for the second-version differences and edge
cases, excluding visual design, animation and packaging. This is a planning
estimate based on the separate orchestration layers, not measured development
time. A route reader alone is far smaller. A normal upstream update needs a
focused 1–2 day compatibility review; changed menu orchestration can exceed it.
Check manifests/facades, MenuModel exports, static tree and aliases, guards,
providers, AppLibrary, search/i18n, request payloads and all caller inventories,
then repeat keyboard, pointer, cancellation and locked-key controls. Runtime
import avoids a copied parser fork but does not eliminate this maintenance.

### Native System action extension

Both versions passed Super+Esc, power key, power-menu alias, clicking the System
row, and repeated toggle. The extension keeps the native icon, label and alias
because normalization otherwise clears omitted fields. The original menu calls
`cancel()` and executes the action directly (`406 Menu.qml:854–864`); it does
not open a System submenu first. No intervening menu was observed in 220 (406) / 222 (450) compositor-layer
samples over three seconds; maximum sample gaps were 17.0 / 15.8 ms. This is
not an exhaustive per-frame flash proof.
Searching `reboot` still finds the original System/Reboot action. It was viewed,
never executed. Removing the extension restored the original System menu.

The negative lock control opened the ordinary overlay behind the secure lock
and exposed it after password unlock. The guard in `spikes/system-route/guard.sh`
checks `lock isLocked` and only toggles when the answer is exactly false. In both
VMs it kept the overlay closed while locked and after unlock; normal unlocked
open/close still worked. This solves the observed already-locked power-key case,
not an atomic check-versus-lock race or an authentication boundary. No default
key needed to be unbound. Evidence: `vm*/system-route.json`,
`system-lock-resume.log`, host lock captures and `shots/*-system-*.png`.

### Draft themes, genuine screenshots and constraints

All four designer-supplied drafts were copied as plain theme directories and
applied through official theme set on 406. The requested 1366×768 surfaces are
listed in the local `shots/INDEX.md`; images remain outside git. Tokyo Night
root/audio/lock captures provide the before control. Canon artwork and music
were not used. Lock theme captures use preview; the separate secure-lock
experiment above exists only for route behavior. Polkit captures use `pkexec true`
launched by the compositor and cancelled without authentication. The initial
SSH-detached attempt had a dead parent and no dialog; final polkit images were
retaken through the desktop session.

| Token / surface | Observation |
|---|---|
| `menu.selected-border-width = "0 0 0 2"` | Works: single left border, including AS yellow and PAPER dark edge. |
| Menu selected background / alpha | Consumed by `Color.qml:99`; alpha 1 is visibly opaque in the supplied drafts. No independent alpha sweep was needed for these drafts. |
| `border-width` | Popup/notification one-pixel frames and selected per-side border render. Native geometry and controls still own their individual layout. |
| Selected detail text | **Poor contrast in AS**: the breadcrumb/detail keeps `root.foreground` at opacity .52 even when selected (`406 Menu.qml:1292–1301`), unlike the main label's selected-text. On a light selected fill it becomes faint. This is not an ignored selected-text token. Drafts were not edited. |
| Lock | Preview reflects background, placeholder and active border. Idle/error/selection roles exist but were not all activated for theme screenshots. |
| Polkit | Prompt, background, border and scrim reflect each draft. Error roles were not triggered; cancellation succeeded. |
| Native bar font | JSON fontFamily ignored by native bar; a host or system fontconfig setting is required. |
| Power / Bluetooth / agents | Power screenshot is an unavailable no-battery trial, not a panel. Bluetooth shows no adapter; agents shows the native no-account state. |
| Applications | Native generated configs shown in foot+fastfetch, btop, Neovim, Chromium new tab and tiled windows. The first Neovim launch showed parser downloads; it was recaptured after startup. These are app results, not shell.toml alone. |

A separate git-marked copy included harmless denied-file probes. Official theme
set reported dropping `foot.ini`, `hyprland.lua`, `neovim.lua`; the staged files
of those names were regenerated from official templates. `colors.toml`,
`shell.toml`, `icons.theme` and `unlock.png` retained identical SHA-256 hashes.
Border colors therefore survive git installation via generated official files.
Evidence: guest `theme-git.stderr` and `theme-git-check.json`.

Official `omarchy-plymouth-set-by-theme wuling-as` completed with status 0 in a
PTY and rebuilt the boot image. The first non-PTY invocation could not obtain
sudo authentication and did not count as success. After reboot, QMP capture was
attempted, but this VM has a plain Btrfs root, **no LUKS**: the disk-unlock screen
was **not captured (沒拍到)**. No reinstall was done. Boot reached the greeter;
the official `omarchy-plymouth-reset` subsequently restored default Plymouth
and SDDM assets and completed with status 0.

Final cleanup and configuration comparison are recorded with the round's local
closure inventory. Raw experiment failures remain in evidence: route-name and
shortcut assumptions, the 450 background setting change, native Esc clearing a
query before closing, and QMP screendump's `no surface` under virgl. Corrected
controls and image review determine the results above; none was silently counted
as a pass.

Closure: both original themes/configurations were restored and `.config`
inventory differences were empty, including after the final shell restart.
Probe fonts, plugins, bindings/extensions and draft directories were removed;
volume returned to 40%, stay-awake was off, secure lock was off. Both guests
powered off normally with status 0. Their round containers were removed. Each
VM retains only its original baseline and latest A-2 clean disk checkpoint;
the superseded A-1 clean checkpoint was deleted. The previously authorized
generic VM runtime image is retained for the development VMs. Evidence and
127 indexed 1366×768 screenshots remain local; the round's `closure.json`
records disk sizes and the exact cleanup inventory.
