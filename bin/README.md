# Command contract

Run `wuling commands --json` for metadata. All data responses include
`schema_version: 1`; errors contain `error.code` and `error.message` and exit
nonzero. Arguments are passed as argv, never evaluated as shell text.

- `wuling theme resolve [--theme NAME]`: effective settings, colours, type,
  geometry, motion and sound, each with an origin. Omarchy's current palette
  supplies colours for other themes; field supplies their geometry.
- `wuling config get [KEY]`: effective settings and explicit user overrides.
- `wuling config set KEY VALUE`: validate and atomically edit one setting.
  Booleans are `true`/`false`; sections accept a quoted space-separated list or
  a JSON array. Menu selection regenerates installed WULING themes and
  reapplies the active one while preserving the selected background. An empty
  `login_music` disables the optional file. A nonempty assignment needs an
  existing audio file readable by pw-play's libsndfile decoder, with an absolute
  path or `~/`. Validation never plays it; rejection preserves the old setting.
- `wuling status --json [--sections SECTION ...]`: an on-demand snapshot of
  `clock`, `link`, `levels`, `signal`, `agent`, `telemetry` and `comms` by default.
  Opt-in detail sections are `performance`, `power`, `audio`, `system`,
  `calendar`, `wifi`, `bluetooth`, `tailnet` and `config`; they are never added to the default collection set. Unknown
  hardware yields null or no tile. CPU percentage needs two samples; the first
  is null. `--watch` produces live JSON lines until terminated (fast initial results,
  then a one-second cadence). The
  caller must stop it when its surface closes. Slow native probes are bounded,
  concurrent and never overlap themselves. No daemon or cache file is created.
  Agent usage reads Omarchy's existing display records; WULING never starts a
  collector or reads credentials. Media selection and controls remain native.
- `wuling action NAME [VALUE]`: fixed native actions used by the Terminal.
  Volume and brightness accept 0–100 or signed adjustments; they use the same
  OSD route as keys. `panel NAME` opens the matching native panel. The three
  dangerous foot actions open the System route (WULING power cards when enabled); this command never performs logout, reboot or poweroff directly.
  `profile` accepts an available `power-saver`, `balanced` or `performance`.
  Audio actions take JSON with numeric `id` and `serial`; `audio-volume` also
  takes `value` (0–100). Current public PipeWire identity is revalidated before
  acting. `system-copy` sends a fresh information snapshot to the clipboard via
  stdin; `system-fastfetch` and `performance-monitor` use native TUI launchers.
  Radio actions revalidate the public interface, access-point or device identity
  in their JSON argument. `wifi-connect` with `credentials: true` reads one
  passphrase line from stdin; never put the passphrase in the argument.
  `bluetooth-scan` owns a bounded discovery client until cancelled.
  `tailnet start|stop` uses the native command and login-browser handoff.
  Destructive radio actions require the panel's hold; direct CLI callers are
  responsible for confirming their intent.
  `config-native` accepts `theme`, `background`, `display`, `input`, `font`,
  `keys` or `default-apps`; these hand over to Omarchy's existing entry points.
- `wuling status --spectrum`: optional 20-cell cava frames, at most 20 per
  second. No cava returns `available: false`; the caller owns its lifetime.
- `wuling terminal open|close|toggle`: the Field Terminal on the focused output.
  `wuling terminal open PAGE` opens `comms`, `performance`, `power`, `audio`,
  `system`, `calendar`, `wifi`, `bluetooth`, `tailnet` or `config`.
- `wuling notifications compatibility|state|boot|terminals|open-history|fallback`:
  internal notification bridge and diagnostics. `compatibility` checks the
  installed native modules. `persist` accepts bounded JSON lines on stdin and
  writes private state; its acknowledgements never contain message text.
  `state` contains private messages: do not include its output in public reports.
- `wuling osd device output|input`: on-demand audio device label for the OSD.
- `wuling dispatch open|close|toggle`: own launcher on the focused output.
  `snapshot` and `activate MODE VALUE` are its internal data/action bridge.
- `wuling power open|close|toggle`: native System entries as held power cards.
  `snapshot` reads native entries and guards on demand.
- `wuling session preview arrival|exit`: safe animation preview, no system action.
  `session exit JSON` is the confirmed-hold worker, not a general shell API.
- `wuling doctor [--json]`: versions, required commands, owned resources,
  fontconfig matches and shipped plugin validation. Exit zero means all checks
  passed. A font match proves availability, not correct graphical rendering.
- `wuling uninstall [--yes]`: print the removal plan, restore the previous
  theme when applicable, and remove unchanged resources. The checkout's
  `bin/wuling uninstall --yes` is safe to repeat after the PATH entry is gone.

`./install` prints the concrete plan and asks for consent. `--yes` accepts it
for scripts; `--fastfetch` also opts into the mark in the user's fastfetch
configuration. Interactive installation asks about fastfetch separately. No
system font preference, authentication code or built-in binding is changed.
It installs the bar, Terminal, notifications, OSD, Dispatch, power, session, sound and Keymap
plugins, enables compatible new components, appends
Terminal at the end of the native right section, and adds Super+Ctrl+G, Super+D and Super+Ctrl+/ in an
owned Lua block. That block also disables compositor animation only for the
Arrival and theme-wave layers, effective on next login. An effective binding conflict is
refused before changes.
Updates preserve native widget placement and independent plugin disablement.
Notifications and OSD use Omarchy's clone restoration contract. Notification
module checks fail closed to the native provider and appear in `doctor`.
An untested Omarchy version is named in the installation plan alongside the
tested versions, with the normal consent prompt. Installed module contents,
not the version string, select the notification contract and DND state path.
The owned System menu extension directs power routes to WULING cards. Removal
restores it and deletes WULING's private notification and Dispatch histories.
Install/removal reload the owned binding and restart the shell officially.

Release code lives under the user's XDG data directory, state and the private
ownership manifest under the XDG state directory. Settings use the XDG config
directory. Omarchy's own theme paths remain HOME-relative, as upstream expects.
Only existing agent skill directories receive a link. Edited owned resources
are reported and preserved; updates refuse conflicts. User overrides survive
both updates and removal.

The transaction journal permits recovery after interrupted filesystem changes.
If the process died inside Omarchy's external theme command before it could
record its effects, the installer preserves the journal and asks for inspection
and restoration of the recorded previous theme. Re-running installation then
finishes recovery. Do not delete the journal or force an ownership conflict.
Font backups live outside fontconfig's search tree: hidden directories within
the font tree are still discoverable. A dedicated font mount on a different
filesystem from WULING's state is refused safely before changing fonts, since
rollback uses an atomic rename.

Boot unlock is deliberately separate: after installing a theme, the user may
run Omarchy's official `omarchy plymouth set-by-theme wuling` with its requested
privileges. The WULING installer does not run that operation.

Panel commands reject native `unknown` responses with nonzero status and
`error.code = "panel_unavailable"`. The native hide/toggle methods return no
value, so their targets are checked through the public registry and live IPC
before invocation. This includes Terminal, Dispatch and Power; exit status
alone is never treated as delivery.

`wuling keymap --json` reads the current native key list, including user-defined
entries. `wuling keymap open|close|toggle` controls the independent Keymap
overlay on Super+Ctrl+/. It never activates a listed binding; Omarchy's native
Super+K list remains available.

`wuling session theme-compatibility` reports the installed content contract for
the optional wave. `session.theme` is an independent boolean setting, default
true. Unknown native content keeps Omarchy's own transition. Keymap snapshots
include a raw active-binding supplement; they never execute listed actions.
