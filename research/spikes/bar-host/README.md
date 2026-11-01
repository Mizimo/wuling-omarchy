# Disposable registered-widget host

A-2 research only. Install this directory as an Omarchy plugin in a disposable
VM, then `omarchy bar use research.bar-host`. It uses installed registry
components and `qs.Ui.PluginBarApi`; no upstream implementation is copied.

`omarchy-shell research.bar-host inspect` reports layout, registered widgets,
slot geometry, open panels and tooltip state. `bar.fontFamily` in shell.json
sets the host font. The experimental `bar.skinProbe: true` draws a 21 px Barlow
Condensed clock label and a volume label; native widgets remain visible and
receive input through an opacity-zero Loader over the same slot. Fonts must
already be installed. The native popup remains a separate window.

See [the host contract](../../bar-host-contract.md) and the A-2 report for
version differences and limitations. Restore the original shell.json, select
`omarchy.bar`, remove the plugin and restart the shell after experiments.
This is deliberately not a complete bar (no drag, overflow or glass mode).
