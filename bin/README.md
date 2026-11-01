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
  reapplies the active one while preserving the selected background. An empty `login_music` disables the optional file.
- `wuling status --json`: component availability; phase B explicitly reports
  `status_collection: false` instead of inventing live data.
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

Boot unlock is deliberately separate: after installing a theme, the user may
run Omarchy's official `omarchy plymouth set-by-theme wuling` with its requested
privileges. The WULING installer does not run that operation.
