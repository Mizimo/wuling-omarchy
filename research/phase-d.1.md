# Phase D.1 — notification finishing and OSD numbers

Implemented inbox v416 on top of `b3761e8`. The toast measures its bottom from
its actual content/action geometry, leaving 10 logical pixels below the action
row, and uses a 14 px close glyph. Overflow is a 22 px strip, the stack's full
width, with the toast's background/line and `+N · MORE 更多` (`+N MORE` in
English). Layout reserves the strip and its gap. Terminal history says `+N 則`
or `+N more`. OSD removes only a final `%` from supplied progress text;
`40 dB` remains unchanged.

Both existing VMs booted from the clean D state and installed the candidate:
Omarchy 4.0.6-1 and 4.5.0rc2-1, Quickshell 0.3.2, Qt 6.12.0-2. Each was viewed
at 1366×768 with 51 notifications including a two-action card, overflow,
Terminal history and OSD. The first used HUD MIST over its yellow background
band; the second HUD PAPER. Chinese and English were checked. This is the
requested focused visual check, not a repetition of D's full matrix.

The new run also exposed an OSD binding loop on show: reading PanelWindow's
`screen` inside the expression that decides whether that same window maps.
The per-output delegate now compares its fixed `modelData` instead. After an
official shell restart, both versions opened and closed OSD with `40%`,
`40 dB` and `100%`; all six captures show the intended text, and neither run
reported relevant QML warnings. This does not change the selected-output rule.

`tools/check`: 52 tests, generation, metadata, syntax and staged privacy pass.
No DESIGN/BRIEF change is needed for these clarifications.

Raw evidence is local under `~/.cache/wuling-build/we1/`: `d1-look-{406,450}.log`,
`d1-osd-r2-{406,450}.log`, `check-d1-final.log` and immutable `shots/d1-*` PNGs.
The first-run binding warnings remain in those logs. The same round's VMs
continue into E's Arrival first-frame experiment; no checkpoint was added and
no old evidence was deleted for this small correction.
