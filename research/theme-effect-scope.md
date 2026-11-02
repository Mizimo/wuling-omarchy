# Native theme effects and rollback scope

The phase B verifier found that a before/after walk of all user configuration
mistook concurrent application writes for theme output. That walk and the raw
dconf database backup are removed. A matching after hash cannot establish who
wrote an unrelated file.

The audit follows `bin/omarchy-theme-set` and its called retint commands at the
upstream tags `v4.0.6` and `v4.5.0-rc2`. The source is the
[official Omarchy repository](https://github.com/omacom/omarchy). WULING imports
no upstream implementation. This is a fixed compatibility list, not discovery
by scanning a home directory.

| Native writer | Exact scope relevant to restoration | Policy |
| --- | --- | --- |
| `omarchy-theme-set-vscode` in both versions | `~/.config/Code/User/settings.json`, `Code - Insiders/User/settings.json`, `VSCodium/User/settings.json`, `Cursor/User/settings.json` | Capture only each `workbench.colorTheme` value, its file mode and an empty JSON scaffold when present. Restore just that member; preserve other settings, comments and concurrent app writes. Remove a newly created file only if the resulting object contains no other content. |
| Same editor writer | Each editor's extension directory outside `.config`; generated extension manifest, palette, registration and obsolete marker | Native management. No WULING snapshot. Version 4.5 uses a content-derived extension version and a regular palette file rather than a symlink. |
| `omarchy-theme-set-gnome` in both | `/org/gnome/desktop/interface/{color-scheme,gtk-theme,icon-theme}` | Only these three dconf keys. Never read, save or restore the complete dconf database/dump in the product. |
| `omarchy-theme-set-templates` and the main setter | `~/.local/state/omarchy/current/{next-theme,theme,theme.name}` plus native generation/background state and caches | Reapply the previous theme using Omarchy. No profile backup. |
| `omarchy-restart-terminal`, `set-foot`, `set-tmux`, btop/opencode/helix restart commands | Alacritty mtime, signals, terminal OSCs and tmux runtime settings | No config content written by these paths; no snapshot. |
| `set-claude`, `set-pi`, `set-t3code`, `set-hermes` | Native palettes under their agent homes; Hermes may select its skin through its own CLI | Native management outside the rollback list; do not copy agent settings, credentials or profiles. |
| `set-obsidian` | Selected vaults' `.obsidian/themes/Omarchy/{manifest.json,theme.css}` | Native management; do not enumerate or snapshot vault contents. |
| `set-browser` / `set-browser-policy` | Fixed system browser `color.json` policies and runtime policy refresh | Native operation only; WULING's installer adds no privileged writer. |
| `set-keyboard` | ASUS/F16 hardware commands | No config snapshot. |
| 4.5 `set-fcitx5` | Native theme under the data home, plus packaged glyph links | Theme switch does not pass `--activate`, so it does not edit `classicui.conf`. No WULING backup. |
| 4.5 `set-hunk`, `set-herdr-machines` | Signals; native remote theme propagation | No local configuration capture. |
| `omarchy-hook theme-set` | User-defined effects, unrestricted paths | Never attribute these to WULING. Preserve them; removal states this exclusion. |

The product visits only the four named editor files and their exact ancestor
directories. It does not follow symlinked profile paths, infer ownership of an
unknown file, or persist unrelated editor members. Old broad manifests are
projected onto this list when read; old unknown rollback entries are ignored.
Only empty directories attributable to a recorded theme-member change can be
removed. Installation and removal still manage WULING's own resources through
separate ownership records.

A 4.5 native theme switch can return before background retints complete.
Installation explicitly requests `OMARCHY_THEME_WAIT=1`; a settings refresh
uses the installed `omarchy-theme-refresh` wrapper. Removal captures the
user's selected editor theme before reapplying the original native theme, so
a subsequent native retint cannot erase that intervening preference.

Removal names the excluded native outputs rather than claiming to restore the
whole desktop. In particular, byte-for-byte dconf equality is no longer a goal:
the three owned keys are restored, unrelated keys remain untouched, and native
database serialization may differ. VM verification compares dconf values;
its private test inventory is separate from the product's bounded capture.

`tests/vm-theme-effects.py --disposable-vm` reproduces the independent write at
an external barrier around the real native setter. It also checks repeated
install/remove, read-only skill failure and SIGKILL/recovery at a late font
cache barrier. Run it only in a disposable logged-in VM. Results and raw
inventories remain in that VM's private cache.

## Validation

The isolated phase B hotfix passed `tools/check` and 25 foundation tests. The
threaded concurrent-write unit test also changes an unrelated member of the
same editor file; its new value survives removal and is absent from captured
theme data. Unknown verbs, incomplete commands and invalid options return
JSON error envelopes with a nonzero exit status.

Fresh disposable VMs restored from the clean B checkpoints passed the real
setter barrier, repeated install/remove, read-only skill directory failure,
and SIGKILL/recovery cases on both Omarchy `4.0.6-1` and `4.5.0rc2-1`. The
concurrent application's new content survived; neither its path nor contents
appeared in the theme journal or manifest. Each failure/recovery removed its
newly created empty state directory, while the unit negative control retained
a pre-existing empty directory. Inventory comparison excludes dconf's binary
serialization and compares its logical values separately. Raw logs, journals
and inventories are held outside git.
