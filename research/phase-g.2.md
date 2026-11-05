# Phase G.2 — page numbers and detail-page memory

Inbox v445 and v446, on top of `a316056`. Both disposable VMs from the clean
checkpoints: Omarchy 4.0.6-1 and 4.5.0rc2-1, Hyprland 0.56.2, Quickshell
0.3.2, Qt 6.12.0, Mesa 26.2.5 (llvmpipe). Synthetic UPower batteries and a
fixture `tailscale`. No real hardware was operated.

## H-V1 — a page's number matches the overview

Opened with `wuling terminal open <page>` or through Omarchy's `showHistory`,
a page numbered its head from what the Terminal had collected so far. While a
page is open the collector reads only the clock and that page, so the
overview's optional sections (Link, Levels, Agent, Comms) were unknown:
Telemetry's pages said 04 where the overview says 06, and Comms 08 where it
says 07. Reproduced on both versions.

The number now counts the sections the overview shows before the page's own.
`wuling status` has a `layout` section, read once per collection, reporting
which optional sections would show; a page reads it only when one of them
comes before its section, so Clock and Link pages (02, 03) need nothing extra.
Opened from the overview the number is known at once. Otherwise the head shows
no number until it is known, then the right one: it never shows a guess that
changes. Terminal `state` reports it as `number`.

Polled every 50 ms for 3 s after each route, both versions: Power and
Performance `06`, Comms `07`, Wi-Fi `03`, System `02`, Power from an open
overview `06`. Comms through `showHistory` shows no number for about 0.1 s,
then `07`. No route showed any other value.

Captures and logs are in private round `wh2`; none are committed.
