# Focus geometry and the deferred overlay

The proposed HUD focus overlay is not shipped. On the tested Hyprland 0.56.2
build (`efb50993780079460b0cbed1363e2166a2de1d9f`), socket events and the Lua
event registration API provide focus/window lifecycle changes but no complete
window-geometry change stream. A floating window resized using the native
binding changed from x=80, width=820 to x=30, width=920 without a corresponding
geometry event; a focus-driven overlay retained its old position until focus
changed again.

Keyboard events cannot cover mouse resizing, layouts or programmatic changes.
Polling geometry continuously would add permanent work for decoration and is
not part of the design. The candidate was removed after this limitation was
confirmed. Revisit only when the supported compositor exposes complete geometry
events. The native window borders remain responsible for indicating focus.

The source check used the installed version's
[Lua event handler](https://github.com/hyprwm/Hyprland/blob/efb50993780079460b0cbed1363e2166a2de1d9f/src/config/lua/LuaEventHandler.cpp)
and a real resize in the disposable VM. Raw before/after geometry and captures
remain outside git.
