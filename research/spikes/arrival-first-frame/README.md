# Arrival first-frame probe

Disposable service plugin for the E-phase startup experiment requested by DESIGN
§8.9. It maps a minimal opaque ink surface immediately when Omarchy creates the
service, on every output, with a magenta identification square. A one-shot timer
removes it. It has no process, data fetch, shader, theme resolver, keyboard grab
or once-per-login marker. It is deliberately cheaper than the eventual Arrival.
Do not install this as a product plugin or use its timer as presentation timing.

In each disposable VM, install the folder under the native user-plugin directory,
validate its full path and enable `research.arrival` using the official command.
Log out using `omarchy system logout`; record the VM's host SDL window *before*
typing the fixture password; log in normally. Confirm a new login session and
Hyprland PID. Inspect all captured frames from greeter through desktop, including
partially faded-in squares. No Omarchy file or startup sequence is changed.
Disable the probe and remove its own directory after the experiment.

The capture is compositor output as shown by QEMU, not a guest-side recorder
started after login. Capture timestamps are not Wayland presentation-feedback
timestamps. Report actual capture gaps, and do not interpret an absence in a
small VM sample as proof that a desktop frame can never precede the final
animation on another machine. Full Arrival needs its own F acceptance.

Results and local artifact names: `research/phase-e-arrival.md`.
