# OSD

`Osd.qml` replaces the native OSD through `omarchy.clonedFrom`, the panel
`open`/`close` entry and the `osd` IPC target (`show`, `close`, `state`, `ping`).
Native volume/brightness keys and audio/monitor panel calls retain their paths.
`Model.js` interprets the public payload; the surface draws the resulting state.
The HUD audio device label comes from the on-demand `wuling osd device` command.
There is no periodic collector, saved state, focus request or input region.

The surface chooses the focused output at each show, falls back if that output
is removed, and disappears after its supplied duration or explicit close.
It follows the active palette, preset, font scaling, language and reduced motion.
Text-only payloads have no level. No private Omarchy object is traversed.

Disable with `omarchy plugin disable wuling.osd`; the native clone restoration
record returns the previously enabled Omarchy OSD. An update preserves that
choice. If the native OSD was already disabled before installation, disabling
WULING leaves it disabled too. `wuling uninstall` removes unchanged owned
artifacts and entries. Supported versions: 4.0.6 and 4.5.0-rc2.
