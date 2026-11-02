# Phase C.1 — Terminal alignment and evidence correction

Inbox v412 follow-up to phase C. No notification or OSD behavior is changed.

The Terminal now follows the approved section geometry: full-width separators,
10 px bottom padding, compact headers and content, three clock detail lines,
username in the header, heavier seconds, fixed English tile micro labels,
localised values, mixed-size telemetry readouts, 96×16 sparklines and English
footer labels with localised accessible names. The final visible section has
no bottom rule. The bar has the identity/workspace separator. Catalogs distinguish
shutdown from an off state and use the requested reboot and comms wording.

The [phase C report](phase-c.md) corrects the missing-font claim. The old capture
was overwritten and the remaining PNG is complete. The earlier candidate
already included the font backup correction; the visual observation remains
unattributed. Capture helpers now use a run ID plus frame timestamp and
exclusive file creation. The verification guide requires immutable filenames.

The four public theme previews were captured again with the real WULING bar,
a neutral terminal window, complete command names and one real prompt cursor.
They were visually inspected before refreshing the image manifest.

Validation: `tools/check` passes (40 tests plus generation, metadata, syntax and
privacy checks). Omarchy 4.0.6 and 4.5.0-rc2 were started from their clean C
checkpoints. Field and HUD were opened and compared visually on each, at
1366×768, scale 1, zh-Hant. The final candidate has no WULING QML load or binding
errors. These are the requested focused checks, not a repeat of C's matrix.
Raw captures and logs remain outside git in `wd1/`; the C raw evidence remains
in `wc1/`. The approved `wc1/hotfix` worktree was removed. Hardware and the
independent cold-login font investigation remain with the verifier.
