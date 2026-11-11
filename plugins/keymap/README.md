# Keymap

`wuling.keymap` is an independent overlay. Its retained entry point owns only
open/close state and a stopped reader. The full-screen view, key rows, input
field and Wayland surface are created on open and destroyed after the 90 ms
closing fade. There is no closed-view polling or saved keybinding cache.

`wuling keymap --json` reads the installed `omarchy-menu-keybindings --print`
interface. Native descriptions, user entries and alternative chords remain
intact. Classification uses the original description from the installed
translation catalog where available; unknown purposes stay in OTHER. WULING
does not copy the native Lua parser or dispatch any listed action. An unreadable
or incompatible response displays an error; the native Super+K list remains.

Super+Ctrl+/ is installed in WULING's owned bindings block. The installer
rejects a conflicting user binding. `wuling keymap open|close|toggle` uses the
native overlay host. `wuling.keymap state` reports whether the view and reader
are live. Disabling the plugin in Omarchy leaves all native bindings intact.

Typing filters descriptions and keycaps. Up/Down and PageUp/PageDown scroll;
Escape clears the filter, then closes. The view takes exclusive keyboard
focus and uses the stock Wayland ShortcutInhibitor while open; outside clicks
dismiss it. A compositor cancellation also closes the overlay. Theme, type scale, language, sounds and
reduced motion follow the shared WULING settings. The supported hosts are
Omarchy 4.0.6 and 4.5.0; no runtime packages are added.

The native list is primary. A plain `hyprctl binds` snapshot adds only missing
chords to OTHER, including the physical Copilot code. Active XKB and platform
names prevent duplicate code/symbol rows. An undescribed Lua binding receives
a localized generic label; its action is never inferred or dispatched. Unknown
codes remain `code:N`, and lid switch events are excluded. A changed raw format
fails visibly rather than silently omitting keys.
