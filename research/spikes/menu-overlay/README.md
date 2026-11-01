# Disposable overlay replacement for menu routing

The independently written overlay declares `omarchy.clonedFrom: omarchy.menu`
to exercise Omarchy's replacement mechanism without cloning its code. It
imports the installed MenuModel.js at runtime and uses public DesktopEntries.
The UI is only a route/capability probe, not Dispatch or a compatible menu.
It does not implement dmenu request/reply, providers or full search parity.

In a disposable VM, validate and enable the plugin, exercise the default menu
keys and inspect `omarchy-shell research.menu-overlay inspect`. Typing an app
name and pressing Enter launches its first matching DesktopEntry. Do not use
this probe as a normal desktop menu: native callers expecting a selection file
and done file would wait indefinitely. Enabling it disables the entire source
plugin, including its bar-widget entry. Restore the original plugin configuration
and remove the probe after use.
