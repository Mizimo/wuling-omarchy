"""Small argv-only bridge to native behaviour. No credentials or policy here."""

import json
import re
from . import Error, SCHEMA, command
from . import status

FIXED = {
    "bluetooth": ["omarchy-bluetooth-power", "toggle"],
    "tailscale": ["omarchy-shell", "omarchy.tailscale", "toggleTailscale"],
    "dnd": ["omarchy-shell", "notifications", "toggleDnd"],
    "night": ["omarchy-toggle-nightlight"],
    "mute": ["omarchy-audio-output-volume", "mute-toggle"],
    "play-pause": ["omarchy-shell", "media", "playPause"],
    "previous": ["omarchy-shell", "media", "previous"],
    "next": ["omarchy-shell", "media", "next"],
    "agent": ["omarchy-agent", "--pick"],
    "lock": ["omarchy-system-lock"],
    "sleep": ["systemctl", "suspend"],
    "power-menu": ["omarchy-menu", "toggle", "system"],
}
PANELS = {"wifi": "omarchy.network", "bluetooth": "omarchy.bluetooth", "tailscale": "omarchy.tailscale",
          "night": "omarchy.monitor", "power": "omarchy.power", "audio": "omarchy.audio", "agent": "omarchy.agents"}
NAMES = tuple(FIXED) + ("wifi", "power", "volume", "brightness", "panel")


class PanelUnavailable(Error):
    code = "panel_unavailable"


def route(action, target, payload="{}"):
    try:
        return checked_route(action, target, payload)
    except (Error, ValueError) as exc:
        raise PanelUnavailable("The requested panel is unavailable in the current shell") from exc


def checked_route(action, target, payload):
    method = {"open": "summon", "close": "hide", "toggle": "toggle"}[action]
    # summon reports delivery. hide/toggle are void on both supported native
    # versions: validate their live target first, rather than treating empty
    # stdout as evidence that a missing widget was reached.
    if method != "summon":
        entries = json.loads(command(["omarchy-shell", "shell", "listPlugins"]))
        if not any(row.get("id") == target and row.get("enabled") for row in entries):
            raise PanelUnavailable("The requested panel is unavailable in the current shell")
        if target == "wuling.terminal":
            monitors = json.loads(command(["hyprctl", "-j", "monitors"]))
            focused = next((row["name"] for row in monitors if row.get("focused")), "")
            json.loads(command(["omarchy-shell", target + "." + focused, "geometry"]))
        else:
            json.loads(command(["omarchy-shell", target, "state"]))
    result = command(["omarchy-shell", "shell", method, target, *([] if method == "hide" else [payload])])
    if result not in ({"ok"} if method == "summon" else {"", "ok"}):
        raise PanelUnavailable("The requested panel is unavailable in the current shell")


def plan(name, value=None):
    if name in FIXED:
        if value is not None:
            raise Error(f"{name} does not take a value")
        return list(FIXED[name])
    if name == "panel":
        if value == "dnd":
            return ["omarchy-shell", "notifications", "showHistory"]
        if value not in PANELS:
            raise Error("Unknown native panel")
        return ["omarchy-shell", "shell", "summon", PANELS[value], "{}"]
    if name == "wifi":
        if value is not None:
            raise Error("wifi does not take a value")
        current = status.probe(["nmcli", "radio", "wifi"])
        if current not in ("enabled", "disabled"):
            raise Error("Wi-Fi state is unavailable")
        return ["nmcli", "radio", "wifi", "off" if current == "enabled" else "on"]
    if name == "power":
        if value is not None:
            raise Error("power does not take a value")
        raw = status.probe(["omarchy-powerprofiles-list"])
        available = [item for item in (raw or "").splitlines() if item in ("power-saver", "balanced", "performance")]
        current = status.probe(["powerprofilesctl", "get"])
        if not available or current not in available:
            raise Error("Power profiles are unavailable")
        return ["omarchy-powerprofiles-set", "autodetect", available[(available.index(current) + 1) % len(available)]]
    if name in ("volume", "brightness"):
        if not isinstance(value, str) or not re.fullmatch(r"[+-]?\d{1,3}", value) or not -100 <= int(value) <= 100:
            raise Error("Level must be 0–100, or a signed adjustment of up to 100")
        relative = value[0] in "+-"
        if name == "brightness":
            argument = f"{abs(int(value))}%-" if value.startswith("-") else value + "%"
            return ["omarchy-brightness-display", argument]
        if relative:
            delta = int(value)
        else:
            current = status.volume()
            if current is None:
                raise Error("Audio output is unavailable")
            delta = int(value) - current["percent"]
        return ["omarchy-audio-output-volume", f"{delta:+d}"]
    raise Error("Unknown action")


def run(name, value=None):
    argv = plan(name, value)
    result = command(argv)
    if name == "panel" and value in PANELS and result != "ok":
        raise PanelUnavailable("The requested native panel is unavailable in the current bar")
    if result == "unhandled":
        raise Error("The native service cannot perform this action now")
    # Do not forward arbitrary native output to a QML log.
    return {"schema_version": SCHEMA, "action": name, "ok": True}


def terminal(action):
    if action not in ("open", "close", "toggle"):
        raise Error("Unknown Terminal action")
    route(action, "wuling.terminal")
    return {"schema_version": SCHEMA, "action": action, "ok": True}
