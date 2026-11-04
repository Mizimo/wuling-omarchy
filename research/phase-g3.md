# G, third installment: radio pages

Implemented under inbox v437 and DESIGN §8.2 (`a0c08d4`). Wi-Fi, Bluetooth and Tailnet enter
through their overview tiles, keyboard selection and `wuling terminal open PAGE`.
The existing detail frame retains its clock, back behavior, scroll/fade, crumb,
watermark, HUD scan and reduced motion. Right-click retains Omarchy's panels;
Tailnet's right-click enters its own page. Config is the following installment.
No hardware machine was accessed.

## Data and actions

- Wi-Fi reads public NetworkManager properties, cached access points and
  `GetSettings`, never `GetSecrets`. Raw SSID bytes, security, interface and
  optional BSSID restrictions identify saved profiles. The profile's BSSID is
  a byte array in the settings API, unlike the access point's printable address.
  Network rows retain delegate identity across changing signal readings.
  Opening does not scan; S/SCAN explicitly requests it. Initial RADIO data is
  published before the complete list; unread states are unknown, not Off, empty
  or unavailable. A disappearing row becomes inert while its stable ID is removed,
  avoiding transient undefined QML bindings during list replacement.
- Secured unsaved networks open an inline hidden input with reveal. Enter
  clears the field and hands a bounded line to a dedicated process on stdin.
  The new profile's public metadata goes through NetworkManager's D-Bus API;
  activation supplies the secret with nmcli `passwd-file /dev/stdin`. An
  explicit replacement clears the saved secret first. This avoids `--ask`'s
  readline prefill appending a replacement to the old password. No secret is
  passed in argv/environment or written by WULING. NetworkManager owns saved
  connections. Enterprise authentication hands over to the native panel.
- Bluetooth projects BlueZ ObjectManager properties and resolves the same
  default controller as `bluetoothctl`. Connected, paired and available groups
  show identity, type icon and reported battery. Omarchy's native helpers own
  power and device mutations. Postconditions reject a helper that exits zero
  without changing the requested state. rfkill-only presence retains an Off
  tile even when the adapter disappears; native ON clears its soft block.
- Bluetooth discovery has one bounded `bluetoothctl` client owned by its page.
  Leaving or closing releases that client's discovery without stopping another
  client's scan. Leaving also cancels in-flight WULING radio commands and
  clears pending credentials and stale action responses.
- Tailnet projects public CLI status, including self identity, exit node and
  online-first peers. Native up/down commands own state. NeedsLogin passes a
  validated public AuthURL to the native browser launcher; it is absent from
  status output. Missing CLI hides the tile and rejects direct CLI page entry.
- A hold uses the same 800 ms duration for pointer and keyboard; release,
  lost focus, disabled controls and leaving cancel it. Errors stay on the page
  and never echo native command output. Radio readers are opt-in status sections
  refreshed every two seconds only while their page is open. No new runtime
  dependency, daemon, credential cache or private QObject traversal is added.

Active-profile FORGET uses the cancellable 800 ms hold; inactive saved profiles
are forgotten immediately; Wi-Fi's Tailnet badge is shown only when an active direct peer's public
endpoint and actual route prove this interface. Relay/unknown paths do not
infer the transport from a default route.

API references: [NetworkManager D-Bus settings](https://www.networkmanager.dev/docs/api/latest/nm-settings-dbus.html),
[nmcli activation](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html),
and [upstream readline secret handling](https://raw.githubusercontent.com/NetworkManager/NetworkManager/main/src/nmcli/common.c).
No upstream implementation was copied into WULING.

## Verification

Private evidence is in `wg3/`. Both VMs began at their clean F checkpoints:
Omarchy `4.0.6-1` and `4.5.0rc2-1`, Quickshell `0.3.2.r7.g2b4501a-1`, Qt base
`6.12.0-3`, declarative `6.12.0-2`, Mesa `1:26.2.5-1`, NetworkManager `1.58.1-2`,
BlueZ `5.87-2`. Only the VMs received fixture packages through the official
package command: hostapd `2.12-2` and dnsmasq `2.93-1`. Before/after inventories
are retained privately. A separate pure Arch build used full `pacman -Syu`
with inventories to build upstream btvirt; its container was removed.

Wi-Fi uses real mac80211_hwsim station/AP radios, WPA2 and open hostapd
networks and private DHCP. Bluetooth uses two LE btvirt controllers with real
public GATT battery services and a fixture-only agent accepting only synthetic
peers. Tailnet uses a private CLI fixture with running/stopped/login states,
direct/relay/offline peers and explicit failures; no real tailnet was changed.
Input is through QMP, not a product test API.

| Check | Result and evidence |
| --- | --- |
| Display-free | `check-r8-staged.log`: 109 tests, syntax, generated kit equality, metadata and staged privacy pass. Radio tests cover cache-only reads, raw identity/BSSID, stdin secrets, enterprise handoff, disappearing soft-blocked hardware, default-controller selection, native failure postconditions, process-group cancellation and login projection. |
| Entry/back | `entries-{406,450}.log`: pointer and keyboard routes, Backspace/Esc, native Wi-Fi/Bluetooth right-click and Tailnet's right-click page. |
| Password | `password-flow-406-r5b.log`, `password-flow-450-r5.log`: wrong passphrase stays on Wi-Fi, correct retry connects to the specifically asserted WPA2 SSID. Concurrent audit observes nmcli and finds no credential in any process argv/environment, journal or WULING file. Earlier 4.0.6 r4 falsely accepted an auto-connected open fixture and is excluded; final checks assert the exact destination. |
| Wi-Fi | `wifi-interactions-*-r5.log`: released disconnect/OFF hold preserves the link; completed hold disconnects/powers off, keyboard reconnects the saved target, ON restores radio. `wifi-open-forget-*.log`: open network connection and forgetting the inactive saved secured profile preserve the current connection. Active FORGET also passes release/full-hold checks in `active-forget-candidate-*-r3.log`. |
| Bluetooth | `bluetooth-interactions-406-le-r3.log`, `bluetooth-interactions-450-le-r2.log`: pair/connect, 76/84% battery, disconnect/reconnect, scan stopped on leaving, soft-blocked tile/ON, forget. Fixture chronology and native-policy caveat below. |
| Tailnet | `tailnet-interactions-*.log`: pointer and Enter holds, released hold, start, failed stop retaining running state/page, NeedsLogin/browser, missing CLI. |
| Theme/language | `vm*/matrix.json`: four themes × three languages × three pages, 36 captures per VM with real keyboard back/close. Representative captures visually inspected. |
| Layout | `layouts-*.log`: three pages at 800×600, native text size 16, 3840×2160 and scale 1.25. Tall content scrolls with its fade; long crumbs elide. |

### Bluetooth fixture and native-policy limits

The first dual-mode fixture connected two host audio stacks to each other and
produced profile instability. It is excluded from acceptance. The LE battery
fixture exercises actual discovery, pairing, connection and properties without
physical audio. btvirt emits an immediate first advertisement before BlueZ's
StartDiscovery completion; advertising again after discovery starts produces
the expected Device1. This sequencing is confined to the fixture.

BlueZ deliberately permits trusted LE devices to auto-connect after Disconnect;
installed `bluetoothctl` reproduced the immediate reconnect. Stable disconnect
cases disable that policy on the synthetic peers (untrust and disconnect their
reverse client during fixture preparation). Product code neither untrusts
users' devices nor changes BlueZ policy. A native action that leaves Connected
true is reported as a failure with the real state retained. Physical USB
removal/rfkill, vendor pairing dialogs and enterprise network authentication
remain independent hardware acceptance, not claims established by the VM.

### First readable row

`input-first-row-*-r4.log` and `vm*/input-first-row.json`: actual tile pointer
input, all three pages in field/full, HUD/full and field/reduced, nine captures
per VM. All 18 captures were visually read. The first RADIO row has real
interface/controller and power state; Tailnet has its real fixture state.
Wi-Fi's complete cached list may follow the RADIO row.

The harness holds the pointer for 60 ms, then releases to trigger the page.
An external display capture starts 250 ms after the release acknowledgement.
The pixels have returned by a conservative 290.9–296.8 ms (4.0.6) and
288.8–297.8 ms (rc2), measured from the earliest possible release (press-request
start plus the fixed 60 ms hold). PNG encoding happens afterward and is excluded.
An earlier capture at about 180 ms after release contained unread states; those
frames are retained and are not used as passes. No animation was shortened.

These are observed pointer bounds, not a worst-case scheduling guarantee.
Direct CLI outliers are retained separately. The initial
CLI-request sweep used a capture requested at 250 ms. One rc2 reduced Bluetooth
capture was not readable; a repeat recorded a 498 ms IPC round trip. Those
samples are not passes and are not discarded. Forty later native `shell ping`
calls take 7.3–9.7 ms; this does not explain the outlier. Independent collector launches complete in 185.6–190.8 ms for
Wi-Fi (initial RADIO in 128.1–131.4 ms), 116.4–122.0 ms for Bluetooth and
128.2–129.9 ms for Tailnet, across four launches per page per VM. The first-row
sweep precedes only the final unknown-state and disappearing-row presentation
fixes; the final candidate repeats page navigation and Wi-Fi row replacement.

### Repeated pages and idle

`cycles-{406,450}.log`: 200 mixed-page cycles each, including periodic overview
visits. Every closed sample has no page, collection request, loaded detail or
spectrum. 4.0.6 PSS is 400.94→405.28 MiB; its final four samples span
404.06–406.43 MiB. rc2 is 310.86→320.51 MiB; its final four span
319.65–322.47 MiB. The late samples fluctuate rather than showing steady growth; these runs do
not identify every retained allocation or establish unlimited-soak behavior. No forced GC or numerical memory
budget was added. FD counts settle at 141–142 and 187.

The 200-cycle runs precede the final loading/row presentation fixes, which
change no collection or allocation lifetime. Final smoke checks repeat actual
open-network connection/disconnection, list replacement and page back/close.
`final-smoke-*-r8b.log` and `idle-final-*-r8b.log` pass on both versions.
No new page/runtime binding errors occur in the final shell logs.
Both final doctors pass. Closed-shell checks find no collector/action process,
no loaded detail and zero CPU ticks across ten seconds per VM.

### Routing and evidence limits

The rules approved in v437 were both exercised:
active FORGET uses a cancellable hold; the Tailnet badge requires a public
active direct endpoint whose actual route uses the Wi-Fi interface. Both VMs
pass direct-Wi-Fi, relay/unknown and direct-other-interface cases; the private
fixture-only route is removed afterward. A local gateway address routes through
loopback in the all-in-one simulator and correctly fails to establish Wi-Fi
transport. It was replaced by an explicit synthetic host route for the positive
case, not accepted as a false pass.

Explicit scanning completes after approximately 31 seconds in this hwsim
fixture; the initial 15-second test limit was insufficient. The cached list
and its age remain truthful while NetworkManager completes the scan. The
request is only made by S/SCAN, never by opening a page.

Private evidence index: `vm*/matrix.json`, `layouts.json`, `final-visual.json`,
`active-forget-candidate.json`, `final-smoke.json`, `input-first-row.json`,
`status-latency.json`, `cycles.jsonl`, `idle-final.json`, and `doctor-final.json`.
Raw data and captures are not repository assets. The private round occupies
about 216 MiB. Both VMs were shut down normally, restored to their clean F
checkpoints with the matching firmware state, and passed `qemu-img check`.
Only the baseline and latest clean checkpoint remain. The G3 containers and
image tag were removed; the same runtime image is reused under G4's tag.
The separate btvirt build container was already removed.
