# Disposable interface probes

These independently written probes answer A-1 interface questions. They are
not WULING components, an installer, a theme, or complete replacements for
Omarchy services. Run them only in a disposable Omarchy VM. Results and pinned
source references belong in [the API study](../omarchy-shell-api.md).

| Directory | Question | Deliberate limit |
|---|---|---|
| `bar` | Replacement through `bar.id`, screen enumeration, theme size and widget catalog | No widget hosting or popup coordinator |
| `osd` | Same-name IPC and built-in-id lifecycle routing | Displays the payload; no production OSD layout |
| `notifications` | D-Bus delivery, same-name IPC, default passive-toast dismissal | Bounded notes; no history, actions, persistence or keyboard mode |
| `focus` | Exclusive keyboard focus and Esc after a compositor shortcut | A single fullscreen input surface |
| `menu` | Whole-route redirection and loading the installed internal MenuModel.js | No copied upstream code; no complete provider/app/search UI |
| `empty` | Incremental cost of one service loader with an empty Item | No settings, timers or window |
| `facade` | Menu versus overlay facade lifetime and Instantiator sequence types | No windows, files or upstream imports; tests an observed API defect |

## Isolation and installation

1. Save an offline stock VM checkpoint. Record package versions, the stock
   display configuration, shell PSS/CPU and notification bus owner.
2. Copy this directory to a cache location inside the VM. Run
   `python3 config-inventory.py > BEFORE.json`, keeping the output outside git.
   Save the original bytes, mode and presence/absence of
   `~/.config/omarchy/shell.json`, `~/.config/hypr/bindings.lua`, and any menu
   extension file that the test will modify. Refuse existing `research.*` ids.
3. Copy only the selected probe directory to
   `~/.config/omarchy/plugins/research.<name>`. Run
   `omarchy plugin validate PATH`, `omarchy-shell shell rescanPlugins`, then
   `omarchy plugin enable research.<name>`. Inspect the result and shell log;
   a valid manifest alone does not prove its QML loads.
4. For OSD/notifications, explicitly disable the built-in first before enabling
   the replacement, so no test relies on duplicate targets. Their `clonedFrom`
   metadata also preserves calls made through the built-in plugin id. This
   metadata is a research use of the upstream replacement mechanism; these
   sources were not made with `plugin clone`.

## Checks

- Bar: inspect `omarchy-shell research.bar inspect`; test 1366×768 and
  1920×1080, then two compositor outputs. Check one `research-bar` layer and
  the correct reserved edge per output. The catalog result does not establish
  compatibility with every widget.
- OSD: inject the real `XF86AudioRaiseVolume` key through QEMU, then inspect
  `omarchy-shell osd inspect` for a changed counter and audio payload. Also
  summon `omarchy.osd` through shell IPC to check the non-IPC identity path.
- Notifications: record `org.freedesktop.Notifications` ownership, send a
  uniquely named `notify-send` message, inspect the receipt counter, then
  inject Super+comma and inspect dismissal. At 4.5 this checks only `act`'s
  passive-toast branch. Do not infer action/history compatibility.
- Focus: add a temporary, unoccupied key in the VM's user bindings file that
  runs `omarchy-shell shell toggle research.focus`; reload Hyprland. Inject
  that key and Esc through QEMU. Inspect `opened`, `focus` and `escapes`.
- Menu: first remove `omarchy.clonedFrom` in the VM-only manifest for a
  negative control. Restore it, rescan, re-enable, and exercise the original
  root/apps/system/background/theme keys plus CLI aliases. Compare the
  payload counter, QML runtime-model flag and actual layers. Test the power
  key separately while locked; receiving a command does not prove visibility
  above a session lock.
- Facade: load it as `menu`, then change only the VM manifest to `overlay`
  with the same entry file and restart the shell. Compare `assignments`,
  `hasShell` and `sequenceCheck`. The menu route probe explicitly counts a
  public-CLI Esc fallback when this facade is unavailable.
- Tree: install a temporary menu extension with true/false `when` guards.
  Run `node menu/read-tree.cjs` in the VM using the installed runtime. It
  imports MenuModel.js, merges the static sources and runs the model's guard
  script. Guard commands come from the installed menu and extension; do not
  run this against untrusted extensions on a personal desktop. Dynamic
  providers and app-row orchestration remain outside this reader.

QEMU input uses the official [`send-key` QMP command](https://qemu.readthedocs.io/en/stable-10.1/interop/qemu-qmp-ref.html#command-QMP.send-key).
Examples of its qcodes are `meta_l`, `spc`, `comma`, `volumeup`, `power` and
`esc`. Direct IPC calls are additional diagnostics, not substitutes for the
compositor shortcut tests.

## Removal and cost measurement

Disable/remove the one probe, restore only the saved files that this test
changed (including original absence), remove newly created empty directories,
then reload configuration and rescan. Compare a new configuration inventory
with `BEFORE.json`: paths, types, modes, link targets and file hashes must
match, or the difference must be investigated. Check stock bar, menu and
notification delivery again; do not count a missing probe as full restoration.

Measure stock → empty service → restored stock with identical geometry and
render backend, warmup and sampling duration. Restart the shell for each
formal sample to separate a loaded empty service from retained hot-reload
allocations. Save the original idle state and use the official
`omarchy-toggle-idle stay-awake` control for every sample, restoring the state
afterward. Check unlocked state, DPMS and geometry before and after each run.
Modifier-only input proved insufficient to prevent idle lock in the pilot;
that pilot is excluded. Read shell
`smaps_rollup` and process CPU ticks; report CPU relative to one logical core.
QEMU/host rendering memory is separate. Do not call a delta within the two
stock runs' variation zero cost. Keep raw logs and screenshots outside git.
