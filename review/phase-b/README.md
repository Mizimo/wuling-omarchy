# Phase B independent verification

Product **d2a962e**; instructions **v158**; specification through **babba25**. Native installation is blocked by the unrelated-file rollback finding below. Kujira and kaede were not operated during this round.

Private evidence root: `~/.cache/wuling-build/wb1/verifier-v158/`. All captures remain there; none are committed.

## Findings, in severity order

### P1 — Removal can discard an unrelated application's write

`bin/lib/wuling/lifecycle.py` recursively snapshots `~/.config` except the separately managed theme-source tree, then records every before/after difference as a theme effect. There is no check that the native theme operation wrote that path. Removal restores the old bytes when a file still equals the captured after value. Thus the preservation check protects edits made *after* installation, but not independent writes made *during* installation.

Reproduced on both independent VMs (4.0.6 and 4.5.0-rc2):

1. Start with no WULING installation and create a synthetic unrelated app file containing an old draft.
2. Put a transparent `omarchy` wrapper ahead of the official executable in the installer's PATH. It pauses only `theme set wuling`; all calls ultimately delegate to the unmodified official command.
3. Run the unmodified `install --yes`. At the pause, write a new draft from the separate fixture controller, then release the external theme operation.
4. Confirm installation succeeds and its manifest lists the unrelated file under `theme_effects`.
5. Run the unmodified `wuling uninstall --yes` without editing that file again.
6. Observe exit 0 and the **old draft restored over the independent new draft**.

The paused private transaction journal also contains the unrelated file's complete contents. This was demonstrated only with synthetic data, not real application profiles.

Evidence: `guest-concurrent.py`, `vm406/concurrent-full.txt`, `vm450/concurrent-full.txt`; `probe-concurrent-config.py` and `concurrent-config-probe.json` are a supporting helper-level reproduction, not a substitute for the VM run.

Before native installation, constrain capture/restoration to explicitly attributable theme effects and avoid sweeping unrelated profiles into the journal. A successful command and a matching final hash do not establish ownership of an intervening write.

### P3 — Failure/recovery leaves an empty state directory

With an existing skill directory made read-only, installation exits 1 and rolls back its resources, but leaves an empty `~/.local/state/wuling`. A late SIGKILL at a controlled `fc-cache` barrier, followed by recovery through `uninstall --yes`, produces the same residue. The original theme returns, and the transaction journal and sibling backups are removed.

Reproduce the permission case by setting the existing `.agents/skills` directory to mode 0555, running `install --yes`, restoring only the original fixture permissions, and comparing the inventory. Evidence: `vm406/edges/readonly-diff.json`, `vm450/edges/readonly-diff.json`, `vm406/interrupted-full.txt`, `vm450/interrupted-full.txt`, `guest-interrupt.py`.

### P3 — Usage errors do not follow the documented JSON error envelope

`bin/README.md` says errors contain `error.code` and `error.message`. An unknown verb is handled outside the CLI's JSON error handler: `wuling unknown` writes argparse text to stderr and exits 2. Invalid settings and malformed override files do produce schema-versioned JSON errors and exit 1. Either narrow the documented promise or give usage errors the same envelope. Evidence: `cli-contract.json`.

## Completed acceptance

| Check | 4.0.6 | 4.5.0-rc2 |
| --- | --- | --- |
| Fresh installation twice, removal twice; config/fonts/state/skills inventory | Empty diff | Empty diff |
| EOF without a TTY, explicit refusal, foreign theme | Refused; empty fixture-relative diff | Same |
| Interactive PTY versus `--yes` | Identical installed inventory | Same files and logical dconf values; binary dconf layout differs |
| Read-only skills; missing skill directories | Safe refusal with empty-state residue; absent directories skipped without creation, as documented | Same |
| Edited owned theme | Update refused with no changes; removal preserves the edited tree | Same |
| Interrupted installation and recovery | Original theme restored; no journal/backups; empty-state residue | Same |
| Four native theme selections and return to original | Actual QMP keyboard input and active-theme checks | Same |
| Root/search menu, clock, lock preview, polkit cancellation, foot, dark/light GTK app | Captured and inspected for all four themes | Same |
| Backgrounds | Three per theme; 48 captures with exact requested output dimensions | Same |
| Preset defaults and native revisit behavior | Field survey line / HUD wide band; entry from another theme returns to the default | Correct defaults; chosen background remembered on revisit |
| `menu.selected fill`, reapply, chosen background | Actual menu changes; persists; setting preserves selected background | Same |
| JSON commands, resolve, doctor; malformed overrides | Stable schema 1 results; failures nonzero | Same |
| Native git theme installation/staging | Metadata and assets survive; `.git` omitted from staged theme | Same |
| Real Plymouth MIST and PAPER prompts | Real daemon and three QMP-entered bullets; mark only, no WULING text | Same, with VT acquisition caveat below |

The 4.5 interactive comparison differed only in dconf database bytes. A controlled follow-up produced those same two hashes and identical complete `dconf dump /` output, establishing representation variance rather than different settings (`vm450/equivalence/`).

The tested modes are 1920×1080, 1920×1200, 1920×1280 and 2560×1080, scale 1. PNG dimensions were checked against the requested real output sizes; these are not image-editor crops simulating display ratios. Every theme cycles three distinct backgrounds through `omarchy theme bg next`; the native Super+Ctrl+Space picker is also captured. No landscape background is shipped. At the wide ratio the survey-line mark approaches the bar but remains below it; labels remain within the frame.

Theme switching uses the native Super+Ctrl+Shift+Space selector, QMP typing/arrows/Enter, and the resulting native theme name. Its substring filter can match both HUD palettes, so the selected result is explicitly disambiguated. The 4.5 harness first narrows to a unique match, then broadens with Backspace and moves with arrow keys; its earlier assumption about the initial selected item was rejected by the observed theme name. Permanent empty dock/notification layers are allowed only after the native notification probe confirms no toast, expansion or keyboard mode. `config set` removes the selected-row edge in MIST's fill mode; it does not imply a yellow MIST row. Selection detail text remains visible.

The GTK fixture is the installed GNOME Disks app, opened in dark and light GTK styles without operating a disk. Authentication windows are cancelled, and lock captures use `lock preview` only. No wrong credentials or real lock operation were used.

Native git installation retains `wuling.toml`, `shell.toml`, previews, unlock asset and backgrounds. On both versions it also retains the fixture's README and ordinary text file; only `.git` is absent from the staged theme. This is a record of the native filter's observed behavior, not a claim that all unknown files are rejected.

Evidence under each of `vm406/` and `vm450/`: `lifecycle/`, `edges/`, `shots/`, `background-dimensions.json`, `config-background.json`, `malformed-overrides.json`, `git-filter.txt`. The 4.5 first-entry record is `first-entry-backgrounds.json`, derived from the initial visual controller log before later revisits.

## Privileged boot operation

The complete installed `omarchy-plymouth-set` and `set-by-theme` scripts were read before execution. The official operation affects **both Plymouth and SDDM**, then rebuilds the initramfs/UKI. A normal successful run changes `/boot/EFI/Linux/omarchy_linux-omarchy.efi` and `/boot/limine.conf` on both tested VMs; 4.5 also updates `/boot/limine.conf.old`.

A controlled external `sudo` wrapper lets the real privileged asset publication finish, then returns exit 73 in place of only the rebuild invocation. Thirteen Plymouth/SDDM asset paths change while `/boot` remains byte-identical. The old boot image survives this failure, **but the old on-disk theme assets do not**; the command is not an all-or-nothing rollback across asset publication and rebuilding. An ordinary retry succeeds. This is an observed boundary of the installed official command, separate from the WULING installer findings.

Both palettes were shown through the actual `plymouthd`, `show-splash` and `ask-for-password` on an owned VM VT. QMP entered three synthetic characters without submitting them. Xvfb/SDL captured the real display because QMP's screendump reports no surface with this GL path; original full frames are retained beside coordinate-recorded crops. The daemon was stopped and the original graphical VT restored. Official default Plymouth and SDDM assets were reapplied before shutdown.

The first 4.5 PAPER preview was black despite an active daemon/VT. DRM still showed the fbcon buffer. No input was sent; native `deactivate`, `reactivate` and `show-splash` reacquired the display on the same daemon, and the unchanged theme then rendered correctly. Three characters were sent only after inspecting the real prompt. This manual VT acquisition caveat is not evidence of real-boot success or failure.

Evidence under `vm406/` and `vm450/`: `installed-plymouth-scripts.txt`, `boot-*.json`, `plymouth-*.log`, `plymouth-success-diff.json`, and the MIST/PAPER prompt captures. The controlled rebuild failure is `vm406/plymouth-failure-diff.json`; the 4.5 preview caveat is `vm450/plymouth-preview-note.md`.

No privileged boot operation or reboot was performed on kujira. Its separate approval gate remains closed.

## Independent method and limits

The two original baseline snapshots were exported while the source VMs were off. Source disk size/mtime/ctime remained unchanged. Read-only exported bases and writable overlays are entirely verifier-owned, with no backing dependency on the implementer's disks. Only one verifier VM runs at a time; QEMU/Xvfb use nice 15 and idle I/O. No implementer test script was executed as acceptance.

The 4.0.6 guest is `4.0.6-1`, kernel `7.2.8-9-omarchy`; the 4.5 guest is `4.5.0rc2-1` with the same kernel. Host GL uses llvmpipe through virgl. These VMs establish functional behavior, not the native CPU/PSS budget. Early boot was delayed by host pressure; it occurred before WULING installation and is not attributed to the product.

A fresh agent reviewed only `skills/wuling/` from the pinned product and found no material safety/discoverability issue or private details. This was a document-only review. The pinned `tools/check` passed. At documentation HEAD `4897522`, privacy review covered all 19 reachable commits, 251 distinct blobs and 274 working-tree files, with no private-path/credential patterns or forbidden artifact paths; all distinct historical raster images were inspected as approved assets, synthetic mockups or theme previews. Raw captures are not submitted.

The fresh repeat-install/remove inventory is separate from the longer graphical session. After the latter, removal preserves the intentional user override. After removing only that test-created override, 4.0.6 also retains 71 Codex bundled-skill entries and changes in dconf/mise configuration that appeared later in the session. The corresponding final 4.5 diff contains only dconf (578 to 586 bytes). These are recorded, not erased to claim a zero diff; their individual writers were not traced. WULING's release, command, four themes, fonts, skill links and owned state are absent. No claim of an unchanged whole desktop is made after the app/native-workflow exercise.

Because P1 blocks native installation, the 900-second kujira comparison, battery/Bluetooth/brightness observation and resource-budget decision are **not performed**. The accepted phase-0 baseline remains the reference, not a substitute for this missing installed measurement.

## Cleanup

Both verifier VMs were powered off normally; both verifier containers were removed. Each retains its read-only exported baseline and only one overlay checkpoint, `verified-clean-b`. Original themes and default boot assets are restored, lock state is false, idle is enabled, and owned application/authentication/Plymouth probe processes are absent. The final inventory caveats above remain recorded.

Allocated storage is **20.50 GiB**: exported bases 18.06 GiB, overlays 2.19 GiB, and remaining sources/captures/evidence 0.26 GiB. No shared runtime image was removed; no verifier-specific image was created. Reproducible working material remains until this report is accepted, then is eligible for removal. Details: `disk-accounting.json` and each VM's `shutdown.json`.

No product files were changed. Only this review is committed; concurrent implementation work is preserved.
