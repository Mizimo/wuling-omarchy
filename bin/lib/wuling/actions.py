"""Small argv-only bridge to native behaviour. No credentials or policy here."""

import json
import re
import subprocess
from . import Error, SCHEMA, command
from . import status

FIXED = {
    "performance-monitor": ["omarchy-launch-tui", "btop"],
    "system-fastfetch": ["omarchy-launch-about"],
    "comms-clear": ["omarchy-shell", "notifications", "clear"],
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
RADIOS = ("wifi-radio", "wifi-scan", "wifi-connect", "wifi-disconnect", "wifi-forget", "bluetooth-radio", "bluetooth-scan", "bluetooth-pair", "bluetooth-connect", "bluetooth-disconnect", "bluetooth-forget", "tailnet")
NAMES = tuple(FIXED) + ("wifi", "power", "volume", "brightness", "panel", "comms-action", "profile", "audio-default", "audio-volume", "audio-mute", "system-copy", "config-native") + RADIOS
PAGES = ("comms", "performance", "power", "audio", "system", "calendar", "wifi", "bluetooth", "tailnet", "config")


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
    if name == "config-native":
        from .configuration import native
        return native(value)
    if name == "system-copy":
        if value is not None:
            raise Error("system-copy does not take a value")
        return ["wl-copy"]
    if name == "profile":
        profiles = (status.probe(["omarchy-powerprofiles-list"]) or "").splitlines()
        if value not in ("power-saver", "balanced", "performance") or value not in profiles:
            raise Error("The requested power profile is unavailable")
        return ["omarchy-powerprofiles-set", "autodetect", value]
    if name in ("audio-default", "audio-volume", "audio-mute"):
        from . import details
        try:
            data = json.loads(value)
            if not isinstance(data, dict) or set(data) != ({"id", "serial", "value"} if name == "audio-volume" else {"id", "serial"}):
                raise ValueError()
            if type(data["id"]) is not int or type(data["serial"]) is not int:
                raise ValueError()
            if name == "audio-volume" and (type(data["value"]) not in (int, float) or not 0 <= data["value"] <= 100):
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            raise Error("Invalid audio action") from None
        snapshot = details.audio()
        targets = [(kind, row) for kind, rows in snapshot.items() for row in rows if row["id"] == data["id"] and row["serial"] == data["serial"]]
        if len(targets) != 1:
            raise Error("The audio device or stream is no longer available")
        kind, target = targets[0]
        if name == "audio-default":
            if kind == "streams" or not target["available"] or not re.fullmatch(r"[\w][\w.:-]{0,255}", target["name"]):
                raise Error("The audio device is unavailable")
            return ["omarchy-audio-"+("output" if kind == "outputs" else "input")+"-set-default", str(target["id"]), target["name"]]
        if kind == "outputs" and target["active"]:
            target = next((row for row in snapshot["outputs"] if row["volume_target"]), target)
        return ["wpctl", "set-volume", str(target["id"]), str(data["value"]/100)] if name == "audio-volume" else ["wpctl", "set-mute", str(target["id"]), "0" if target["muted"] else "1"]
    if name == "comms-action":
        try:
            data = json.loads(value)
            key, index = data["key"], data["index"]
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", key) or type(index) is not int or not -1 <= index < 3:
                raise ValueError()
        except (TypeError, ValueError, KeyError):
            raise Error("Invalid notification action") from None
        return ["omarchy-shell", "wuling.notifications", "historyDeed", key, str(index)]
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
    if name in RADIOS:
        from . import radios
        try:
            if name == "bluetooth-scan":
                radios.discover()
            elif name == "tailnet":
                radios.tailnet_action(value)
            elif name.startswith("wifi-"):
                radios.wifi_action(name, value)
            else:
                radios.bluetooth_action(name, value)
        except KeyboardInterrupt:
            raise Error("The radio action was cancelled") from None
        return {"schema_version": SCHEMA, "action": name, "ok": True}
    argv = plan(name, value)
    if name == "system-copy":
        from .details import System
        try:
            # The clipboard owner survives this action; never capture its pipes.
            copied = subprocess.run(argv, input=json.dumps(System().read(), ensure_ascii=False, indent=2)+"\n",
                                    text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            if copied.returncode:
                raise Error("The system information could not be copied")
        except (OSError, subprocess.TimeoutExpired):
            raise Error("The clipboard is unavailable") from None
        result = ""
    elif name in ("performance-monitor", "system-fastfetch", "config-native"):
        from .dispatch import native_launch
        # Config editor helpers end in setsid. A session leader lets that
        # native helper fork its editor instead of waiting for the window.
        launched = native_launch(argv, new_session=True) if name == "config-native" and value in ("display", "input", "keys") else native_launch(argv)
        if not launched:
            raise Error("The native terminal launcher is unavailable")
        result = ""
    else:
        result = command(argv)
    if name == "profile" and command(["powerprofilesctl", "get"]) != value:
        raise Error("The power profile did not change")
    if name == "audio-default":
        from .details import audio
        if not any(row["active"] and str(row["id"]) == argv[1] for rows in audio().values() for row in rows):
            raise Error("The default audio device did not change")
    if name == "panel" and value in PANELS and result != "ok":
        raise PanelUnavailable("The requested native panel is unavailable in the current bar")
    if result == "unhandled":
        raise Error("The native service cannot perform this action now")
    if name in ("comms-clear", "comms-action") and result != "ok":
        raise Error("The notification action is no longer available")
    # Do not forward arbitrary native output to a QML log.
    return {"schema_version": SCHEMA, "action": name, "ok": True}


def terminal(action, page=None):
    if action not in ("open", "close", "toggle"):
        raise Error("Unknown Terminal action")
    if page is not None:
        if action != "open" or page not in PAGES:
            raise Error("Choose an available Terminal page with open")
        if page == "tailnet" and not status.shutil.which("tailscale"):
            raise Error("Tailnet is not installed")
        monitors = json.loads(command(["hyprctl", "-j", "monitors"]))
        focused = next((row["name"] for row in monitors if row.get("focused")), "")
        if not re.fullmatch(r"[\w.-]{1,120}", focused) or command(["omarchy-shell", "wuling.terminal." + focused, "page", page]) != "ok":
            raise PanelUnavailable("The requested Terminal page is unavailable")
    else:
        route(action, "wuling.terminal")
    return {"schema_version": SCHEMA, "action": action, "ok": True}
