# Verification

`tools/check` is the display-free entry point. Keep meaningful failure tests:
ownership conflicts, interrupted installation, rollback, changed shared blocks,
repeated install/remove, invalid overrides and deterministic generation.

For VM acceptance start at a clean checkpoint and inventory user configuration
before installation. Use real QMP keys, buttons and wheel events, inspect the
visible surface and capture the compositor output. Test both supported
Omarchy versions. Check the requested resolutions, output shapes, scale and
hotplug; do not infer hardware support from a VM's loaded component.

After removal compare the inventory, restore only test-created data, shut the
VM down normally and remove its container. Keep a baseline and the latest
clean checkpoint. Evidence stays outside git; a small report describes exact
versions, limits and paths. Do not erase user edits to obtain an empty diff.

Privacy checking supplements review; it cannot establish that an arbitrary
image contains no private content. Inspect every new public image and use
only synthetic account, machine and notification data.
