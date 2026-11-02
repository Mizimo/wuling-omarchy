# E.1 — notification writer recovery and visual corrections

Implemented against inbox v423 and DESIGN `ad9be9e`. The recovery defects are
fixed and tested on both supported VMs. **The historical spontaneous writer
exit on kujira remains unexplained:** the specified sequence did not reproduce
it. This report does not treat forced termination as an explanation of that
incident. The design lead has been asked for the verifier's contemporaneous
evidence; neither workstation was accessed.

## Persistence

A single newest full snapshot remains pending until its exact in-flight
snapshot receives a schema-1 `ok: true` reply. Changes during a write coalesce;
a negative or malformed reply retains the latest snapshot and enters recovery.
Exit codes are logged without notification contents. A failed launch also has
a finite startup deadline. There is no idle poll.

The original fault gets three recovery attempts after 1, 5 and 30 seconds.
If all three fail within ten minutes, the writer stops. A subsequent fault
after that window begins a new budget. `wuling.notifications writer` reports
running/ready/pending, attempts, exit code and reason; doctor queries it and
fails for an enabled missing or unhealthy provider. An intentionally disabled
provider is not an error. Exhaustion inserts one translated low-priority
warning, not history. A private runtime marker, keyed by the compositor
identity, prevents repeats across shell/plugin restarts. It contains no message
or hostname. Teardown kills the child immediately, without a final write or
wait; unsaved updates at teardown are not promised durable.

## VM results

Both VMs use the existing clean E checkpoints, Omarchy 4.0.6 and 4.5.0-rc2,
Quickshell 0.3.2, Qt 6.12 and Mesa 26.2.5. Evidence is outside git in
`~/.cache/wuling-build/wf1/`.

| Check | 4.0.6 | 4.5.0-rc2 |
|---|---:|---:|
| Original font/restore/restart sequence | 9/9 retained writer | 9/9 retained writer |
| Kill child, send, dismiss, recover; restart without resurrection | pass | pass |
| Negative ACK, newer update, recover latest full state | pass | pass |
| Stopped writer + 50 notifications + official restart | 2.30 s | 3.41 s |
| Invalid JSON observed during that restart | 0 | 0 |
| Three measured recovery delays | 1.09 / 5.06 / 30.06 s | 1.13 / 5.08 / 30.07 s |
| Exhaustion: doctor fails with cause; one warning | pass | pass |
| Final doctor after recovery and fixture removal | pass | pass |

The original sequence used unmodified product `1905201`: official restart,
native text size 16, native reset plus exact restoration of five font files
and the dconf scaling key, then another official restart at least 15 seconds
later. Eight checkpoints per repetition include a later critical notification
and its dismissal; all 144 sampled checkpoints retained exactly one writer.
No diagnostic product edits or child signals occurred in those runs.

Why an empty historical qslog is insufficient: the
[pinned Quickshell Process implementation](https://github.com/quickshell-mirror/quickshell/blob/2b4501a282689792b62e94f3fb30d8f512324fe6/src/io/process.cpp)
closes a child's stderr channel when no parser is attached, and the old WULING
exit handler emitted no diagnostic. This explains missing observability, not
the cause of the exit. The candidate now records exit code and exposes health.

`e1-writer-baseline-*` and `e1-writer-repeat-*` contain the original runs.
`e1-writer-candidate-vm406-r2.log` and `e1-writer-candidate-vm450.log` contain
the fault tests; `e1-runtime-*` records packages and exit-code diagnostics.
The first 4.0.6 fixture queried IPC before plugin registration and stopped;
the corrected fixture waits for provider readiness. No product workaround was
needed. The ten-minute budget reset and coalescing/ACK permutations are tested
deterministically, not claimed as a ten-minute real-time VM run.

## Visual corrections

Agent is now a full-width bordered row with icon and new three-language copy
on the left and the default-agent micro label inside the right edge. The
missing-panel error uses the content inset and the specified bar wording.
Hazard has an ink-2 ground, four-pixel perpendicular stripes at -45 degrees
(horizontal period 8√2 px); dangerous selected cards include the hold label.
The shared change also corrects Terminal's red foot stripes. RUN and ASK use
escaped plain text instead of highlighting the entire query. Notification
README limits its verification-code promise to WULING's own files and explains
the native-equivalent failed-image journal boundary.

Both VMs were captured with real QMP input in Traditional Chinese/MIST field,
Simplified Chinese/MIST hud, and English/PAPER field. Agent usage and the
missing Tailnet tile used synthetic data; the missing native target and its
routing were real. Fixtures were restored before doctor. Captures under
`shots/e1-agent-error-*`, `e1-hazard-*`, `e1-ask-*`, `e1-run-*` have immutable
run/time names. The combined visual script used an unsupported Dispatch CLI
argument after finishing its six panel/power captures; the separate Dispatch
run uses actual prefix keys and passes. The failed script's `finally` restored
the synthetic data. No missing captures are claimed.

`tools/check`: 77 tests, generated artifacts, syntax and privacy checks pass.
F continues next; real-machine startup and the 24-hour soak remain untested.
