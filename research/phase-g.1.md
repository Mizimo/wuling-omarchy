# Phase G.1 — Terminal page and Keymap corrections

Implemented inbox v444 on top of `64239f4`: the verifier's G findings G-V1 to
G-V6 and the design lead's H-L1. Each was first reproduced on the unmodified
installation in both disposable VMs, then fixed and checked again on both:
Omarchy 4.0.6-1 and 4.5.0rc2-1, Hyprland 0.56.2, Quickshell 0.3.2, from the
clean checkpoints. Input was real QMP keyboard, pointer and wheel events.
Batteries came from a synthetic UPower service (charging 78 %, absent, low 8 %)
and Tailnet from a fixture `tailscale` command. No real hardware was operated.

## Findings

| Item | Cause | Change |
|---|---|---|
| G-V2 cold Night holds the action queue | `wuling action` captures stdout/stderr through pipes. A cold `omarchy-toggle-nightlight` starts `hyprsunset`, which inherits those pipes, so the wrapper waited for its 120 s timeout while later Terminal actions queued | Actions that may leave a native process behind run with their output detached and only the exit status checked. Of the commands behind Terminal actions, only Night (`hyprsunset`) and Lock (a backgrounded password-manager lock helper, bounded at about 4 s) do this. Radios, power cards, launches and the clipboard already detach. A runtime test with a fake command that leaves a child holding stdout fails on the old code after 20 s and passes in 0.2 s |
| G-V1 English shows `count-unit` | `Runtime.tr` and `label` fell back on falsy values, so English's legitimately empty unit returned the key | Fallback checks that the key is present in the catalog. The two count labels trim the trailing space in English. `count-unit` was the only empty value in any catalog |
| G-V3 blank space below the last Comms row | The page `Loader` in the scroll column keeps the previous page's height after it unloads, so Config, Tailnet or System left their height behind | The Loader takes part in the column only while it holds a page |
| G-V4 System head | A 86 KB copy of the full mark scaled into 52 px | The 52 px plate, the same file as the bar's menu cell |
| G-V5 cut labels | `DetailValue` captions were a single fixed-height line with elision | A caption that doesn't fit puts the Chinese half under the English one, as the bar's cells do, and otherwise wraps at spaces; `LOAD 1 · 5 · 15` keeps `1 · 5 · 15` together. The row, the Performance head and the Power pack card grow with it. Values stay on one line |
| G-V6 input mute icon | The input level always drew `mic` | `mic_off` when muted, like `volume_off` on outputs |
| H-L1 Keymap head on the bar | The overlay ignores exclusive zones and placed its head at fixed offsets from the output's top | The dim layer and outside click still cover the output. The head, filter, columns and foot start inside Hyprland's reserved area for that monitor (left, top, right, bottom, the same field Omarchy's dock reads), refreshed when the view opens. The `06` is gone |

## Checking every page for cut text

Terminal IPC gains a read-only `truncated` method: visible WULING text in the
open panel that is elided or overflows its box. It was swept over the overview
and all ten pages, three languages, text size 12 and 16, the `field` and `hud`
presets, at 1366×768: 132 views per version.

- Before: only the three reported labels were cut, on both versions and both
  presets: `LOAD 1 · 5 · 15` (24 views), `Frequency · 頻率／频率` (16) and
  `Health · 健康度` (8 at size 12).
- After: nothing cut in any of the 264 views, Tailnet included. The final
  layout change to where labels break was checked again on Performance and
  Power in both languages and sizes, with nothing cut, and inspected by eye.

## Results after the fix, both versions

- Cold Night from `wuling action night`: 0.68 s and 0.63 s, light on; an
  immediate second toggle 0.43 s and 0.42 s, light off; `hyprsunset` stays up.
  Before: still running at 12 s on both.
- Comms at 640×480 after Config, Tailnet or System, and at 800×600 with text
  size 16 after Config or System: scrolled to the end, the oldest row sits
  above the foot with the column's own bottom padding.
- English counts read `15`, `18`; zh-Hant `則` unchanged.
- Keymap with the bar on top, at the bottom and hidden (`omarchy-toggle-bar`,
  reserved area `[0, 0, 0, 0]`): nothing of the overlay touches the bar, and
  with the bar hidden the head starts at the top edge.
- `wuling doctor` passes after each installation; `tools/check` passes with 123
  tests.

Captures and logs are in private round `wh2`; none are committed.
