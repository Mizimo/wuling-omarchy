# F: Arrival, sound and update boundaries

Delivered implementation under inbox v431; hardware soak remains with the verifier.
E.1 was delivered separately as `ccf474a` and `ff501b4`. The historical
spontaneous writer loss on kujira remains unreproduced/pending under v424;
this work does not claim to identify its cause. F adds numeric writer-start
PID and exit PID/code diagnostics for the verifier's soak.

Ten Arrival previews ended +436 KiB, with unchanged FD count and no remaining
Arrival windows or timers: accepted under v428, with no raw-delta limit.

## Implementation

Arrival stays in the main shell. Its keepLoaded service synchronously reads the
private marker, Arrival switch and supported Hyprland signature timestamp.
Only an unseen compositor less than 30 seconds old automatically plays;
unknown signatures and older desktops are marked without playback. Preview
bypasses the gate. The first window contains only ink; the full view, bounded
metadata reader and fonts load after its swap. The surface has alpha from
creation; a single ink rectangle supplies that first frame. Wall elapsed time drives the
sequence, with an independent watchdog and frame check limiting its lifetime.
There is no forced GC or second shell. The private external-process experiment
was stopped under v426 and is not shipped.

The view types Unicode codepoints, measures mono and serif text in their actual
faces, elides long hostnames, and reveals through the specified 16×9 wave and
scrim. Unavailable factual readings are `—`; addresses and SSIDs are not read
for Arrival. There is no public background-presented signal in the tested
native APIs, so arming uses the specified one-second fallback. Reduced motion
holds the final view for 600 ms and fades for 120 ms. The bar creates six small
source textures only during reveal and releases held state independently.
Hot-unplug transfers the primary input role to a remaining output.

The sound service has four cue voices and one optional user music stream,
using stock `pw-play`. Identical cues are rate limited; overflow drops. Essential
excludes tick/hover, off stops cues, mute stops playback, and native DND gates
notifications and music. Music defaults off, is attempted once per fresh login,
and never plays for preview or ships in a release. Nineteen approved PCM files
regenerate byte-identically from the supplied synthesis script.

Notification compatibility now matches installed module hashes against the
known contracts, independently of the reported Omarchy version. That contract
selects the Rules adapter, display behaviour and native DND path. Unknown
contents retain/restore native notifications. Installing or updating on an
untested version names that fact, tested versions and potential fallback in the
normal consent plan. The tested set remains 4.0.6 and 4.5.0-rc2.

## Acceptance

| Check | Result / evidence under private `wf1/` |
| --- | --- |
| Display-free checks | `f-check-staged-final-r1.log`: 84 tests, generation, metadata, syntax and staged privacy checks passed on the final implementation. Includes unknown-version consent, matching/changed/missing module contracts, and owned layer-rule upgrade/removal. |
| Sound, both versions | `sound-test-vm{406,450}-r2.log`, `sound-extended-vm{406,450}-r1.log`: measured PCM gain 0.6000003186; essential/full/off, mute, DND, four voices, overflow, throttling, preview and disable-with-active-children passed on private null sinks. No physical audio. |
| Fresh-login music, both versions | `fresh-music-vm{406,450}-r2.log`: normal Arrival and independently enabled sound play once; DND and muted logins do not; official shell restart does not replay. All four cases use real logins after the v425 age gate. |
| Input, both versions | `arrival-input-vm{406,450}-final-r1.log`: key/click skip, held key ignored, native Super+Space, lock cancellation and unlock without replay. `arrival-catcher-vm406-r2.log`: skip key consumed; following key reaches the real foot app. |
| Lifecycle | `arrival-lifecycle-vm406-r1.log`: old-session first enable skipped, disable during Arrival releases bar/surfaces, disabled auto-play still allows preview, restart does not replay. |
| Languages/layout | `arrival-layout-vm406-v426-r1.log`: en/zh-Hans/zh-Hant, field/hud, MIST/PAPER, reduced, two outputs and 1.25 scale. `arrival-edges-vm406-r1.log`: long hostname, 2560×1080, removal of primary output and hot-add. Theme changes reset some shots to 1280×800; the fractional output is 1920×1080. |
| Partial installation | `partial-matrix-vm{406,450}-r1.log`: 17 combinations each (all except one, only one, all off), with real QMP input, visible layer checks and native fallback. |
| Official update, stable | `official-update-vm406-driver-r1.log`: full official update exits 0; remains 4.0.6-1; overrides byte-identical and disabled-plugin set unchanged; doctor passes. |
| Official update, RC | rc2 → rc3 official update exits 0; overrides and disabled-plugin set unchanged; unknown-version reinstall preserves both. See component table below. rc3 is not added to support; its VM is restored to the clean rc2 checkpoint. |
| Removal, both versions | `final-cleanup-vm{406,450}-r1.log`: repeated removal restores exact native shell, owned binding block (including Arrival rule) and menu entry, removes resources/private state, and preserves overrides/unrelated edits. Native UI smoke passes, with `final-native-after-removal-vm450-r2.log` allowing the native menu to finish opening. |
| Soak observer | `soak-events-vm406-r3.log`: the 20-second smoke captures a writer exit and replacement between ten-second samples, including both child PIDs and exit code. This is a tool check, not a 24-hour soak. |

## Cold first frame

The earlier threshold-based classifier missed dim wallpaper. Direct inspection
of the final full-overlay recording `f-arrival-cold-vm406-20261102T100306-3294320.mkv`
shows wallpaper around 14.00–14.10 s while the ink fades in. The nominal first
swap was earlier; it did not prove full visible coverage. The initial automatic
“no desktop before ink” result is invalid and is not used for acceptance.
The repeat is retained as `f-arrival-cold-vm406-20261102T100744-3314408.mkv`.

Under v431, the existing owned Hyprland block now adds an exact namespace rule
for `wuling-session-arrival` with `no_anim = true`, following Omarchy's own bar
pattern. It is installed/updated/removed through the same transaction as the
bindings. Exit uses a different namespace and is unchanged. There is no extra
cut to ink. The four final cold-shader-cache real logins (both versions ×
field/PAPER) pass direct frame inspection: no wallpaper or bar before ink.
The first captured ink is RGB (5,7,7), filling 99.983% of the 4.0.6 samples
(the cursor occupies the remainder) and 100% on 4.5.

| Version / palette | Final raw recording | First ink PTS / frame |
| --- | --- | --- |
| 4.0.6 MIST | `f-arrival-cold-vm406-20261102T101717-3359675.mkv` | 14.191 s / 1703 |
| 4.0.6 PAPER | `f-arrival-cold-vm406-20261102T101750-3363288.mkv` | 16.190 s / 1563 |
| 4.5.0-rc2 MIST | `f-arrival-cold-vm450-20261102T101718-3359705.mkv` | 14.591 s / 1751 |
| 4.5.0-rc2 PAPER | `f-arrival-cold-vm450-20261102T101750-3363095.mkv` | 17.040 s / 1880 |

These PTS values are relative to separate recordings, not login latency.
Host capture scheduling was irregular in the PAPER runs; use the recorded
PTS rather than dividing frame numbers by 120. Full contact sheets and CSVs
share each movie's basename. Earlier `cold-v431-*` runs establish the layer
rule fix but are superseded by these final `cold-alpha-*` runs.

Inspection also found that creating an opaque window then changing its clear
colour to transparent could expose black during the wave/wipe. Creating the
alpha surface immediately and painting the first ink with a single Rectangle
fixes that without loading any font or metadata before the first frame. The
final videos show the real desktop through the wave and wipe. Two lifecycle
measurements per version (`arrival-lifetime-vm{406,450}-final.log`) bound the
inactive response to 3378–3420 ms after first swap, with visual, controller and
watchdog all absent. The independent 3500 ms watchdog remains.

## Update beyond the tested set

`official-update-vm450-20261102T100743-3314352.log` records the complete official
rc2 → rc3 update. `official-update-vm450-driver-r1.log` includes full doctor JSON:
all checks pass, Omarchy is explicitly `tested: false`, and notification contents
match contract `4.5.0-rc2`. `rc3-components-r1.log` records reinstall and actual
input. These are smoke results on rc3, not a new support promise.

| Component | Observed after rc3 update |
| --- | --- |
| Bar | WULING remains visible; native widgets load. |
| Terminal | WULING opens through Super+Ctrl+G, renders and closes. |
| Notifications | WULING continues with the matching rc2 module contract; visible toast and healthy writer. No period without a provider was observed. |
| OSD | WULING shows the native `osd show` request. |
| Dispatch | WULING opens through Super+D and closes. |
| Power | WULING opens through native Super+Esc and closes without executing an action. |
| Session | WULING Arrival preview opens and skips. |
| Sound | Deliberate disablement survives update and reinstall; enabling it again plays a cue through the private null sink, then it is disabled again. |
| Theme | WULING remains active and resolves; bar, panel and background stay visible. |

No broken component was observed in this bounded exercise. Public-interface
components continue; no module gate was bypassed and no native file was patched.

## Evidence, failed fixtures and limits

Evidence stays in `~/.cache/wuling-build/wf1/`, outside git. Cold MKVs are lossless
RGB at a requested 120 fps, retaining original PTS. Duplicate capture frames and
irregular scheduling remain visible; do not infer compositor refresh rate from
the recording rate. MP4s and contact sheets are previews, not timing sources.

Failed fixtures are retained: the first PulseAudio recorder missed signal due
to its default buffering; the corrected recorder uses bounded low latency.
The first fresh-music observer lacked the session environment and recorded no
samples. The first layout script used obsolete Hyprland dispatch syntax; the
corrected run uses the installed Lua API. The first input catcher requested an
uninstalled terminal; the repeat uses installed foot. The soak smoke first
used an incorrect shell-name pattern, then exposed journald's byte-array
encoding for Qt's coloured messages; the observer now decodes it before
retaining only numeric diagnostics. The first 4.5 post-removal menu check ran
before its layer appeared; the readiness-based repeat passes. Transient teardown
logs include unavailable-theme and native WidgetButton tooltip warnings; no
missing native bar/menu/notification provider remained after restart.
None of those failed attempts is counted
as acceptance. The initial first-frame classifier failure is described above.

Both supported VMs use Quickshell 0.3.2.r7.g2b4501a-1, Qt declarative 6.12.0-2
and Mesa 1:26.2.5-1, KVM/virgl with a software host renderer. This does not establish
physical hardware behaviour or host texture memory from guest PSS. The
implementer did not operate kujira or kaede. Real boot/Arrival on hardware
remains unseen by owner decision.

[Soak instructions](phase-f/SOAK.md) and the read-only observer are supplied for
the verifier's 24-hour kujira run, including natural writer loss diagnostics.
Memory must stay reasonable without steady growth; idle CPU should be near
zero. There is no hard +40 MiB limit. A natural writer failure must be preserved
and investigated, not explained away by our forced-failure recovery test.

## Cleanup

The rc3 update VM was returned to its clean rc2 checkpoint before final testing.
After final removal, private null sinks are unloaded and original audio defaults
restored; the user music fixture is absent. Both VMs are shut down normally.
Only the original baseline and latest clean uninstalled checkpoint are retained
per VM. The round's containers and unused runtime image are removed by name.
Private evidence remains in `wf1/`; no capture, raw log, music or credential is
committed. User override files are deliberately retained by removal.
