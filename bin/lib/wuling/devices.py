"""Bounded reads of public D-Bus device properties through stock systemd tools."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from .status import probe, label, number


def call(bus, destination, path, interface, method, *arguments):
    raw = probe(["busctl", "--" + bus, "--json=short", "call", destination,
                 path, interface, method, *arguments], timeout=1)
    try:
        value = json.loads(raw or "null")
        return value.get("data", []) if isinstance(value, dict) else []
    except ValueError:
        return []


def properties(bus, destination, path, interface):
    values = call(bus, destination, path, "org.freedesktop.DBus.Properties", "GetAll", "s", interface)
    values = values[0] if values and isinstance(values[0], dict) else {}
    return {key: value.get("data") for key, value in values.items() if isinstance(value, dict)}


def media_times(native):
    """Supplement Omarchy's selection only when public MPRIS proves one match."""
    absent = {"length": None, "position": None}
    if native.get("hasPlayer") is not True or native.get("playing") is not True:
        return absent
    values = call("user", "org.freedesktop.DBus", "/org/freedesktop/DBus",
                  "org.freedesktop.DBus", "ListNames")
    names = values[0] if values and isinstance(values[0], list) else []
    names = [name for name in names if isinstance(name, str)
             and re.fullmatch(r"org\.mpris\.MediaPlayer2\.[A-Za-z0-9_.-]+", name)]
    if not names or len(names) > 32:
        return absent

    def inspect(name):
        root = properties("user", name, "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2")
        if not root:
            return False  # An unreadable candidate cannot establish uniqueness.
        identity = str(root.get("Identity") or root.get("DesktopEntry") or "")
        if identity != str(native.get("identity") or "") or str(root.get("DesktopEntry") or "") != str(native.get("desktopEntry") or ""):
            return None
        data = properties("user", name, "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player")
        metadata = data.get("Metadata")
        if not isinstance(metadata, dict):
            return False
        metadata = {key: value.get("data") for key, value in metadata.items() if isinstance(value, dict)}
        artists = metadata.get("xesam:artist")
        projection = {"title": metadata.get("xesam:title") or "",
                      "artist": ", ".join(artists) if isinstance(artists, list) and all(isinstance(value, str) for value in artists) else "",
                      "album": metadata.get("xesam:album") or "", "artUrl": metadata.get("mpris:artUrl") or ""}
        if any(projection[key] != str(native.get(key) or "") for key in projection) or data.get("PlaybackStatus") != "Playing":
            return None
        length = number(metadata.get("mpris:length"), low=-1)
        position = number(data.get("Position"), low=-1)
        return {"length": length / 1000000 if length is not None and length > 0 else None,
                "position": position / 1000000 if position is not None and position >= 0 else None}

    with ThreadPoolExecutor(max_workers=min(4, len(names))) as pool:
        matches = [row for row in pool.map(inspect, names) if row is not None]
    return matches[0] if len(matches) == 1 and matches[0] is not False else absent


def battery_rows():
    service = "org.freedesktop.UPower"
    values = call("system", service, "/org/freedesktop/UPower", service, "EnumerateDevices")
    names = values[0] if values and isinstance(values[0], list) else []
    result = []
    states = {1: "charging", 2: "discharging", 3: "empty", 4: "full", 5: "pending-charge", 6: "pending-discharge"}
    for path in sorted(name for name in names if isinstance(name, str))[:16]:
        if not isinstance(path, str) or not re.fullmatch(r"/org/freedesktop/UPower/devices/[A-Za-z0-9_]+", path):
            continue
        data = properties("system", service, path, service + ".Device")
        if data.get("Type") != 2 or data.get("PowerSupply") is not True:
            continue
        full = number(data.get("EnergyFull"))
        present = data.get("IsPresent") is True and full is not None and full > 0
        result.append({"id": path.rsplit("/", 1)[-1], "name": label(str(data.get("NativePath") or "Battery").rsplit("/", 1)[-1], 64),
                       "present": present, "percent": number(data.get("Percentage"), high=100) if present else None,
                       "state": states.get(data.get("State"), "unknown") if present else "absent"})
    return result
