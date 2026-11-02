# Shared visuals

Edit this directory, then run `tools/generate`. Each plugin contains a regular
file copy, with content hashes. Omarchy rejects internal symlinks; no upstream
code is included. `Runtime` resolves settings on file changes and falls back
to generated tokens during startup. It has no periodic work. Components use
Omarchy's font scale and plain text; icon glyphs come from our licensed subset.

`Button`, `Level` and `Section` draw interactive plates and headings. `Spark`
and `Hazard` repaint only when their data, colours or dimensions change.
Native panel ownership and dismissal remain in the installed `qs.Ui` module.
