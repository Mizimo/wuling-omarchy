# WULING bar

`Host.qml` implements the replacement `bar` kind. It loads Omarchy's registered
widgets through the installed `qs.Ui.PluginBarApi`; native panels, services,
click actions and saved inline settings remain native. WULING draws only the
menu, identity, workspaces, window label, clock face and power cell.

The host owns transient layout, tooltip, click-target and single-popout state.
It writes no separate configuration or history. `omarchy bar` and native
`shell.json` own layout, position and transparency. A duplicate single-instance
id retains its first placement. Overflow scrolls within each section, and a
panel shortcut reveals its anchor. The clock's input layer is the original
widget at zero opacity; a changed internal clock contract falls back to the
visible original. Vertical bars always use that original clock.

Settings are resolved by the generated kit: palette, preset, font scaling,
`labels`, `motion` and `language`. The generated `kit/` contains copies of our
shared code, with hashes; Omarchy code is imported at runtime, never copied.

`wuling.bar inspect` is a read-only Omarchy shell IPC diagnostic of layout,
widget ids, geometry, labels, tooltip and open state. Its output can contain
native widget text; keep diagnostic captures private. No user data is logged
by the plugin. Native widgets receive the full host contract; third-party
widgets receive the installed scoped facade.

Compatibility is limited to Omarchy 4.0.6 and 4.5.0. The central boundary
is the installer gate and the host contract in `research/bar-host-contract.md`:
six layout sections, the transparent/background setting and optional popout
callbacks. The installer and removal restart the shell officially, since
4.0.6 does not safely replace live bar IPC owners.

Disable with `omarchy plugin disable wuling.bar`, then `omarchy restart shell`.
The native bar takes over and continues to host the independently enabled
Terminal. Removing all of WULING uses `wuling uninstall`; only unchanged owned
resources and shared additions are removed. A load failure lets Omarchy's
native loader fall back to its own bar.
