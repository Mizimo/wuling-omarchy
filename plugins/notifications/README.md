# Notifications

`wuling.notifications` replaces `omarchy.notifications` through Omarchy's clone
contract. It runs in the existing shell process and owns the `notifications`
IPC target and D-Bus notification server while enabled. There is no extra shell.

The tested boundaries are Omarchy 4.0.6 and 4.5.0-rc2. Rules are imported from
the installed native JavaScript modules; `native-modules.json` records their
SHA-256 hashes. The installed modules select the contract, Rules adapter and
DND state path, independently of the reported Omarchy version. Nothing from
upstream is bundled. An unknown module contract or a QML-load failure leaves
or restores the native plugin. `wuling doctor` explains a failed
module check. Do not edit the hashes to bypass an unreviewed update.

The `notifications` target provides `ping`, `dndState`, `isDnd`, `setDnd`,
`toggleDnd`, `showHistory`, `clear`, `dismissAll`, `dismissOne`, `dismiss`,
`invokeLast`, `invokeAction`, `act`, `keyboard`, `count`, `expand` and `probe`.
Methods added in 4.5 are also available on 4.0.6 without adding keybindings.
The service exposes native `doNotDisturb` and `setDoNotDisturb` members.
`wuling.notifications` provides the private Terminal bridge: `ping`, `log`,
`terminal`, and `historyAction`. None of these runs a command string as a shell.

Cards stack newest first, with overflow waiting behind `+N`. Pointer hover
pauses expiry and holds new cards for at most 30 seconds. Keyboard mode lasts
10 seconds without input; arrows/J/K/Tab select, Enter activates, Delete or
Backspace dismisses, 1–9 choose actions and Escape leaves. Critical cards stay.
4.0.6 shows on every output; 4.5 pins the stack to its initial focused output.
Cards keep their 340 px width. The Terminal reports its own native panel
geometry. Only an overlap moves the stack: to the panel's left when it fits,
otherwise to its right, otherwise back to the normal top-right position.

Private state is `$XDG_STATE_HOME/wuling/notifications.json` (normally
`~/.local/state/wuling/notifications.json`), mode 0600 in a 0700 directory.
It holds DND, at most 100 live cards and 100 history rows retained for 24 hours.
Verification text is redacted before writing; images and detected links are
excluded. Live state survives shell restarts. Persistence uses one bounded
stdin writer and coalesced event-driven updates, with no idle polling.
The verification-code privacy guarantee covers WULING's own files. If a sender
puts a code in an image filename that fails to load, Qt can include that path in
a journal warning, just as it can with the native notification renderer.
The latest full snapshot remains pending until an `ok: true` acknowledgement.
An exited or failed writer gets recovery attempts after 1, 5 and 30 seconds;
if all three fail within ten minutes of the original fault, recovery stops.
A writer that survives that window starts a fresh budget on its next failure.
`wuling doctor` reads `wuling.notifications writer` and reports a degraded,
missing or stopped writer. Exhaustion produces one low-priority warning per
compositor session. Teardown kills its child without waiting or flushing.
Health distinguishes `never-started`, `starting`, `running`, `exited` and
`given-up`, with `ever_started`, the current PID, and a nullable exit code.
FailedToStart is detected through `runningChanged`; a five-second startup
deadline also covers a missing transition. Startup failures share the same
three recovery attempts as exits and failed acknowledgements.
Notification objects and their signal callbacks belong to the service, never
to delegates or model rows, and are explicitly disconnected on release.

`showHistory` opens the enabled Terminal log. When that route is disabled it
replays six recent rows, including under DND, without recording them again.
`clear` clears history only. Disabling this plugin hides the Terminal log;
WULING never reads native notification history. Uninstall deletes this private
state, including after an earlier partial removal.

Use `omarchy plugin disable wuling.notifications` to return to native
notifications, and `omarchy plugin enable wuling.notifications` to enable it
again. Original native disablement is preserved. Updates preserve independent
plugin choices. Other WULING components remain independent.

On first use without WULING state, DND is seeded once from the compatible
native stored state, read only. Disabling WULING restores Omarchy's own last
stored value; WULING never writes the native notification files.
