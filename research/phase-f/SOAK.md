# Read-only soak for the verifier

Run on the current installed release from a terminal in the intended graphical
session. Do not log out, restart, reboot, lock, suspend, close owner windows or
change stay-awake settings for this observation. Real login and boot screens
remain VM-only; kujira uses `wuling session preview arrival` when an operator
explicitly chooses to preview it. No unattended action exercise is built in.

Check `wuling doctor` first. Record package versions, theme, scale, resolution,
background, active plugin set and observer start time privately. Identify the
current shell and Hyprland PIDs with `qs list` and `hyprctl instances -j`; verify
the intended session. Substitute those numeric PIDs below. Evidence belongs
outside the checkout and should be readable only by its owner.

```sh
umask 077
python3 -u research/phase-f/soak.py \
  --shell-pid SHELL_PID --compositor-pid COMPOSITOR_PID \
  --seconds 86400 --interval 10 > /private/evidence/wuling-soak.jsonl
```

The observer records PSS, USS, Swap PSS, CPU ticks, FD count, map count, threads,
and deduplicated DRM client metrics for both processes. It uses the phase-0
measurement definitions. 100% CPU is one core. DRM allocation and PSS are not
additive; a guest virgl reading is not the host renderer's texture memory.
The observer creates no service, changes no settings, and reads no app titles,
notification messages, credentials or music paths. It aborts on process loss or
PID reuse rather than joining measurements across shell restarts.

Each sample also contains writer health, including PID, ever-started, status,
last exit code, retry state and reason. Journal start/exit events retain only
the numeric writer PID, exit code and timestamps, so even a writer dying between
samples remains observable. FailedToStart has no child PID and no exited signal;
health must therefore be retained too. The initial sample records a writer
already running before observation. Keep a natural failure as evidence; do not
restart it to make the health indicator green. Our kill/failure tests establish
recovery behaviour, not the historical kujira failure's cause.

Acceptance:

- Require a final `complete`, at least 86400 seconds elapsed, no unexpected shell
  or compositor replacement, no crash and no unaccounted sampling gaps.
- Compare matched 15-minute idle windows with the native baseline: all-WULING
  shell memory must stay reasonable (baseline 304.46 MiB on kujira), and CPU
  should remain near zero at idle. Around native +40 MiB calls for a look,
  not a hard failure; a few MiB alone is not a finding (inbox v427/v428). Keep external workload,
  resolution, theme, scale and warmup differences explicit. Active animation,
  interaction and native activity intervals are not labelled idle.
- Record operator-driven open/close cycle boundaries separately, with a point
  3 seconds after open, 5 seconds after close and 30 seconds after each group.
  Settled PSS, FDs and mappings must return to their warmed range without
  accumulating by cycle. Compare the first and last matched idle windows and
  inspect the full time series; a low final sample alone is insufficient.
- Report every writer PID transition, exit, never-started/given-up state,
  pending snapshot which fails to clear, and restart-budget exhaustion. Zero
  crash lines alone is not a healthy-writer result.

If interrupted, preserve the incomplete capture and start a separate one only
after explaining the interruption. Do not stitch files into a nominal 24 hours.
The implementer smoke-tests this observer in a VM; the 24-hour kujira run and
its acceptance belong to the verifier.
