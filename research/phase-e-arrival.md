# E: Arrival's earliest frame

Inbox v416; product baseline `03df1dd`. A minimal keepLoaded service in the same
omarchy-shell process mapped an ink overlay with a magenta marker. Two complete
logout/login cycles per version changed both login session and compositor PID.
Omarchy files, background startup and bar code were not modified. The fixture is
in `research/spikes/arrival-first-frame/`; it is not a product animation.

In all four recordings, the probe appeared before any visible themed wallpaper
or bar. The preceding screen was the compositor's plain dark background after
the greeter disappeared. Hyprland fades the mapped layer in: its first partially
visible marker counts, rather than waiting for full magenta. The first-frame
comparison uses every captured frame, not the half-second contact sheet.

| Omarchy | Run | Probe first captured frame / recording PTS | First captured visible desktop after probe | Maximum capture gap near probe |
|---|---|---|---|---|
| 4.0.6-1 | 1 | 1651 / 13.758 s | 2007 / 16.724 s | 12 ms |
| 4.0.6-1 | 2 | 1646 / 13.716 s | 2006 / 16.716 s | 10 ms |
| 4.5.0rc2-1 | 1 | 1695 / 14.124 s | 2021 / 16.841 s | 9 ms |
| 4.5.0rc2-1 | 2 | 1693 / 14.108 s | 2019 / 16.824 s | 19 ms |

The desktop column reports its first capture after the identification square has
fully faded away; the compositor can blend the departing overlay with desktop
on preceding frames. These PTS values include password entry, not a login-speed
benchmark. Both VMs used the WULING field/MIST theme, 1280×800 on fresh login,
Quickshell 0.3.2 and Qt 6.12.0-2, KVM/virgl with a software host renderer. Host
X11 capture requested 120 fps, preserved timestamps and produced 2161 frames
per 18-second lossless RGB recording. Timing jitter and occasional duplicate
millisecond timestamps remain in the capture; they are not hidden by resampling
the analysis. Human preview videos are resampled to 60 fps; use the originals
and frame CSVs for evidence.

This establishes that this supported service path *can* precede desktop in both
VMs. It does not prove the eventual animation can never lose the startup race:
this probe does no settings/data work and has much less QML to create, and the
19 ms sampling gap exceeds one 75 Hz guest refresh. The final Arrival still
needs the F checks, including cold cache and real hardware. No decision about
adding or omitting the specified 120 ms cut-to-ink is made here; the result goes
to design before implementing Arrival's start.

Local evidence: `~/.cache/wuling-build/we1/arrival-vm{406,450}-first-*-r{1,2}.mkv`,
matching `.r3.csv`, `arrival-analysis-*-r3.log`, `arrival-first-*-r*.log`, and
`shots/arrival-*-first-frames-r3.png`. `arrival-summary-*-r1.png` shows the frame
before the first marker, its first capture, four captures later, and desktop.
Earlier analysis logs/plates deliberately remain: the first threshold wrongly
required a nearly full-bright marker; r3 measures contrast against its local
ground and is the reported analysis. The two r2 guest logs also retain a stale
fixture environment's Hyprland socket warning; logout and the new login did
complete, as their changed session IDs/PIDs show. The fixture environment was
then changed to discover live `hyprctl instances`, rather than an old runtime
directory.
