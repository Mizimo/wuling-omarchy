# Phase G4 — Config and release metadata

Implemented against DESIGN `9f0c714` and inbox v437–v439. G3 is already
committed as `a967297`. This delivery adds Config and the two requested radio
presentation corrections. No physical desktop was accessed.

## Behaviour

The Terminal head now has the three-dot Config button after the user. The
head remains when clock, or every overview section, is disabled. Pointer,
keyboard navigation and `wuling terminal open config` reach the same page.
The existing detail transition, watermark, scrolling fade and back keys apply.

Language, sounds, motion, labels, menu selection, individual sections, Arrival
and Exit write through `wuling config set`. Controls retain the stored value
until a successful reply. A rejected action leaves Config open with one error
line. A submitted settings transaction may finish after closing; the page
collector stops immediately. Nothing new watches configuration while closed.

LOGIN MUSIC has a path field, APPLY/Enter and CLEAR. Before changing the file,
the command checks a regular audio file using the libsndfile decoder already
used by stock `pw-play`. It never plays a validation stream. Missing files,
non-audio content, directories, FIFOs and relative paths are rejected; absolute
paths and `~/` are accepted. Removing an old configured file does not break
reading settings or editing unrelated keys. CLEAR writes the empty value.

THEME, BACKGROUND, FONT and DEFAULT APPS use installed Omarchy menu routes.
The route is chosen from menu content, not the version string. DISPLAY, INPUT
and KEYS use Omarchy's config editor for its native Lua files. The editor
helper ends in `setsid`: it needs a fresh session so that the native helper
forks its window rather than making the action wait for the editor to close.
The fix is restricted to these Config editor handoffs. Missing native files
still produce a visible failure in place.

The open-network LINKED card no longer paints a lock, matching the available
list. Scan age uses seconds through 90 seconds, then compact minutes/hours/days
with the same truncation as uptime. The requested Bluetooth representative
shows connected, paired but disconnected, and available devices together.

## Version diagnosis

G1's `prepare_payload` did not write `release.json` for any installation source.
G2 added that operation; the observed G1 failure therefore does not establish
an archive-only bug. This delivery makes the unversioned case explicit and
rejects non-string metadata fields rather than displaying their Python spelling.

Both VMs performed real installs from all three sources:

| Source | Installed metadata |
|---|---|
| Synthetic git checkout of the candidate | Actual checkout commit, commit date, `unreleased`; the unit test also covers an exact tag |
| Source tree with root `release.json` | Supplied version, commit and date preserved |
| Source tree without git or metadata | `version: unreleased`, empty commit/date |

Each installed payload was inspected, System data read and System captured.
The candidate archive was reinstalled afterward. The test checkout hashes are
fixture identities, not release commits. No version is inferred from a folder
name or the Omarchy version.

## Validation

Private evidence is in `wg4`, outside git. All captures contain synthetic VM
data and approved project backgrounds. Capture names include a run/timestamp.
The version-install capture set is indexed by VM and source type.

| Check | Evidence/result |
|---|---|
| Display-free | `check-r2.log`: 113 tests pass, including audio rejection preserving old bytes, native route selection, all metadata sources and the `setsid` handoff. Generated files, syntax and whitespace pass. |
| Versions | Omarchy 4.0.6-1 and 4.5.0rc2-1; Hyprland 0.56.2-4; Quickshell 0.3.2.r7.g2b4501a-1; Qt base 6.12.0-3/declarative 6.12.0-2; Mesa 26.2.5-1; PipeWire 1.6.9-1; libsndfile 1.2.2-4. |
| Settings/input | `interactions-406-r3.log`, `interactions-450-r2.log`: real pointer settings, keyboard Config entry with all sections disabled, clock restored from its switch, MENU preserving the current background. |
| Music/failures | `music-actions-406-r2.log`, `music-actions-450.log`: Enter, missing/non-audio files, old value retained, input Left/Backspace, CLEAR, Arrival/Exit, no music playback. |
| Native handoffs | `native-handoffs-406-r3.log`; `native-handoffs-450.log` for the four menu entries, `native-editors-450-r3.log` for the corrected three editors and missing-file control. Actual surfaces captured; fixture editors closed without saving. |
| Visual matrix | `vm*/matrix.json`: four themes × three languages per version. `vm*/layouts.json`: 800×600, 800×600 with native text size 16, 3840×2160, 1920×1080 at scale 1.25. Config scrolls within its card. Representative captures visually inspected; the narrow large-text view retains existing bar crowding outside Config. |
| First readable row | Six QMP pointer captures: field/full, HUD/full and field/reduced on each VM. The external captured pixels contain the readable first row. Conservative upper bounds from activation are 292.4–295.5 ms (4.0.6) and 291.6–297.4 ms (rc2), subtracting only the fixed 60 ms button hold from capture-read time. |
| Radio corrections | `radio-shots-406.log`, `vm406/bluetooth-three-groups.json`, `vm406/wifi-open-linked.json`: real BlueZ/btvirt devices and an open mac80211_hwsim/hostapd network. Bluetooth shows a connected 76% battery peripheral, a saved disconnected peripheral and an available one. Wi-Fi shows OPEN without a lock and a 13M scan age. |
| Lifecycle | 200 Config open/close cycles per VM; `vm*/cycles.jsonl`. Every sampled close has no loaded detail or spectrum. Final 10-second idle samples show no collector, zero shell CPU ticks, 141/186 FDs. Both final doctors pass; fresh shell logs contain no Config binding/type/reference errors. |

Whole-shell PSS was 502.56 → 527.56 MiB on 4.0.6 and 391.02 → 420.69 MiB on
rc2. These are VM observations, not an allocation attribution or a hardware
budget. The late 4.0.6 values were 525.67, 527.71, 527.74, 527.56 MiB; rc2 was
421.94, 422.15, 424.32, 420.69 MiB. The late samples plateau or fluctuate rather
than continuing to grow. Physical idle measurement remains with verification.

Earlier harness failures are retained: a first post-install IPC request raced
the official shell restart; theme refresh reset the temporary VM resolution;
clipboard capture inherited the clipboard owner's pipe; and an editor-close
assertion ran before the window disappeared. Corrected runs are cited above.
The initial editor action timeout was a product process-boundary bug and was
fixed and retested. Multi-peripheral pairing attempts also exposed fixture
limitations; the representative uses actual BlueZ states and does not claim
that every attempted fixture pairing succeeded. G3's action acceptance remains
in its own report.

No additional design change is requested. Test-only hostapd and btvirt do not
become runtime dependencies. After evidence collection the VMs are shut down,
restored to their existing clean checkpoints and checked; only baseline plus
latest clean snapshots remain. Round containers are removed; the same runtime image is retagged for H, without
a duplicate. The round directory is 55 MiB. The accepted G3 BlueZ build tree was removed
(39 MiB); its build log and fixture binary remain. Evidence and
private harnesses remain locally; no screenshots, logs or credentials enter git.
