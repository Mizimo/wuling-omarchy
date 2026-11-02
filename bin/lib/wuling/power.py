"""Read native System entries at opening; retain their guards and actions."""

from pathlib import Path
import json
import os
import subprocess
from . import Error, SCHEMA, command, jsonc, paths
from . import actions, dispatch

KEYS = {"screensaver": "S", "lock": "L", "suspend": "U", "hibernate": "H", "logout": "E", "reboot": "R", "shutdown": "P"}
ICONS = {"screensaver": "monitor", "lock": "lock", "suspend": "bedtime", "hibernate": "downloading", "logout": "logout", "reboot": "restart_alt", "shutdown": "power_settings_new"}
DANGEROUS = ("logout", "reboot", "shutdown")
FALLBACK = {
    "system.screensaver": {"label": "Screensaver", "action": "omarchy-launch-screensaver force"},
    "system.lock": {"label": "Lock", "action": "omarchy-system-lock"},
    "system.suspend": {"label": "Suspend", "action": "systemctl suspend", "when": "! omarchy-toggle-enabled suspend-off && ! omarchy-sleep-disabled"},
    "system.hibernate": {"label": "Hibernate", "action": "systemctl hibernate", "when": "omarchy-hibernation-available && ! omarchy-sleep-disabled"},
    "system.logout": {"label": "Logout", "action": "omarchy-system logout"},
    "system.reboot": {"label": "Reboot", "action": "omarchy-system reboot"},
    "system.shutdown": {"label": "Shutdown", "action": "omarchy-system shutdown"},
}


def extension_path():
    return paths()["home"] / ".config/omarchy/extensions/omarchy-menu.jsonc"


def read_menu():
    root = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
    native = jsonc.loads((root / "default/omarchy/omarchy-menu.jsonc").read_text())
    extension = extension_path()
    custom = jsonc.loads(extension.read_text()) if extension.exists() else {}
    if not isinstance(native, dict) or not isinstance(custom, dict):
        raise Error("Expected native menu objects")
    # Omarchy replaces the whole entry, so omitted fields do not leak through.
    return {**native, **custom}, native


def guard(expression):
    if not expression:
        return True
    if not isinstance(expression, str):
        return False
    try:
        return subprocess.run(["bash", "-c", expression], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=2).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def snapshot():
    fallback = False
    try:
        menu, native = read_menu()
    except (Error, OSError, ValueError):
        menu, native, fallback = FALLBACK, FALLBACK, True
    rows = []
    for identifier, entry in menu.items():
        if not identifier.startswith("system.") or identifier.count(".") != 1 or not isinstance(entry, dict):
            continue
        action = entry.get("action")
        if not isinstance(action, str) or not action or not guard(entry.get("when")):
            continue
        name = identifier.split(".")[1]
        rows.append({"id": identifier, "name": name, "label": str(entry.get("label", name)), "action": action,
                     "icon": ICONS.get(name, "power"), "glyph": str(entry.get("icon", "")), "key": KEYS.get(name, ""),
                     "dangerous": name in DANGEROUS, "disabled": bool(entry.get("disabled")) and guard(entry["disabled"]),
                     "translated": name in KEYS and entry.get("label") == native.get(identifier, {}).get("label")})
    return {"schema_version": SCHEMA, "rows": rows, "fallback": fallback}


def toggle(action):
    # This is a UX guard, not an authentication boundary. Failed lock queries
    # keep the menu closed rather than queueing it behind the secure lock.
    if action != "close" and command(["omarchy-shell", "lock", "isLocked"]) != "false":
        return {"schema_version": SCHEMA, "ok": True, "opened": False, "locked": True}
    if not dispatch.enabled("wuling.power"):
        if action == "close":
            command(["omarchy-menu", "close"])
        else:
            # The official generic method IPC can open the existing submenu
            # without executing its extension route again. Both supported
            # versions expose this method; do not replace the menu provider.
            result = command(["omarchy-shell", "shell", "call", "omarchy.menu", "openExistingMenu", "system"])
            if result == "unknown":
                command(["omarchy-menu", "summon", "root"])
                result = command(["omarchy-shell", "shell", "call", "omarchy.menu", "openExistingMenu", "system"])
            if result != "ok":
                raise Error("The native System menu is unavailable")
        return {"schema_version": SCHEMA, "ok": True, "native": True}
    actions.route(action, "wuling.power")
    return {"schema_version": SCHEMA, "ok": True, "native": False}


def prepare_extension(previous):
    path = extension_path()
    if path.is_symlink():
        raise Error("Menu extension is a symlink; leave it under its existing manager")
    text = path.read_text() if path.exists() else "{}\n"
    if previous:
        # Preserve a user's subsequent changes. If they replace our route,
        # updates do not silently take it back.
        try:
            jsonc.remove_member(text, previous["edit"])
        except Error:
            return text, previous
    _, native = read_menu()
    system = native.get("system")
    if not isinstance(system, dict):
        raise Error("The native System menu entry is unavailable")
    own = {"icon": system.get("icon", ""), "label": system.get("label", "System"),
           "aliases": system.get("aliases", ["power-menu"]), "action": "wuling power toggle"}
    parsed = jsonc.loads(text)
    if not previous and isinstance(parsed.get("system"), dict) and parsed["system"].get("action"):
        raise Error("The user already assigned a System action; preserve it before installing WULING power")
    result, edit = jsonc.set_member(text, "system", own, previous["edit"] if previous else None)
    return result, {"edit": edit, "created": previous["created"] if previous else not path.exists()}
