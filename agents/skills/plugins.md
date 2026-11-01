# Plugins

Read the component's DESIGN section, `research/bar-host-contract.md` and the
version table in the API study. Each plugin has a manifest, entry point,
README and locale catalogs. The README states owned state, IPC, settings,
fallback, versions and independent removal.

The shared kit is maintained in `kit/`. Package copies of WULING's kit into
each plugin with a generated content hash; do not use internal symlinks, which
`omarchy plugin validate` rejects. These are generated copies of our code,
never copies of upstream components. Runtime imports of `qs.Ui` use the
installed Omarchy module and the compatibility boundary.

Keep data in commands with versioned JSON. QML renders that state. No idle
animation, closed-view polling or per-view agent collectors. Native widgets
retain their behaviour; the bar supplies their tested host contract. A change
to clock internals must fall back to the visible original widget.

Validate complete artifacts, then test actual input and independent disable /
fallback in both supported VMs. Installation uses the shared owned-resource
manifest and transaction mechanism; do not add ad hoc edits to shared files.
