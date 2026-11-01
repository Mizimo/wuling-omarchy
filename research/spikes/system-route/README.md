# Disposable native System-route extension

`extension.jsonc` is a complete experimental System entry, retaining the native
icon, label and power-menu alias. With the independent focus probe enabled,
place it in the official menu extension file in a disposable VM. Preserve and
restore any pre-existing extension file. This keeps the native menu and its
bindings; the action toggles the focus probe instead of opening System children.

For the lock control, replace the action with an absolute invocation of
`guard.sh`. The script only opens while the native lock reports exactly false;
a failed query leaves it closed. A lock-state query followed by launch is not
an atomic security primitive. This guard prevents a menu being left open by a
power key pressed while already locked; it is not a new authentication boundary.
The menu remains an ordinary overlay beneath the secure lock.

A-2 checks keys, alias, clicking System, repeated toggle, original reboot search,
locked/unlocked controls and removal. Do not trigger actual reboot/shutdown.
