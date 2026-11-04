"""On-demand Terminal pages; no reader changes device or session state."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import calendar
import json
import math
import os
import re
import shutil
import time
from . import ROOT
from . import devices, status


def parallel(readers):
    # A page owns at most four independent probes. The status collector cancels
    # their process groups before joining this scope when the page closes.
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {key: pool.submit(reader) for key, reader in readers.items()}
        return {key: future.result() for key, future in pending.items()}


def json_value(argv, fallback):
    try:
        value = json.loads(status.probe(argv) or "null")
        return value if isinstance(value, type(fallback)) else fallback
    except ValueError:
        return fallback


def cpu_name():
    match = re.search(r"^(?:model name|Hardware)\s*:\s*(.+)$", status.text(status.PROC / "cpuinfo"), re.M)
    return status.label(match[1]) if match else ""


class Performance:
    def __init__(self):
        self.previous = {}
        self.processes = {}
        self.at = None
        self.history = []
        self.hz = os.sysconf("SC_CLK_TCK")
        self.page_size = os.sysconf("SC_PAGE_SIZE")
        self.telemetry = status.Telemetry()

    def read(self):
        now = time.monotonic()
        ticks = {}
        for line in status.text(status.PROC / "stat", 1048576).splitlines():
            fields = line.split()
            if fields and re.fullmatch(r"cpu\d*", fields[0]):
                try:
                    values = [int(value) for value in fields[1:9]]
                    ticks[fields[0]] = (sum(values), sum(values[3:5]))
                except ValueError:
                    continue
        def usage(key):
            if key not in self.previous or key not in ticks:
                return None
            total, idle = (value - before for value, before in zip(ticks[key], self.previous[key]))
            return max(0, min(100, 100 * (total-idle)/total)) if total > 0 and idle >= 0 else None
        percent = usage("cpu")
        threads = [{"name": key, "percent": usage(key)} for key in sorted(ticks, key=lambda key: int(key[3:] or -1)) if key != "cpu"]
        self.history = (self.history + [percent])[-60:]
        process_ticks, rows = {}, []
        for folder in status.PROC.iterdir():
            if not folder.name.isdecimal():
                continue
            raw = status.text(folder / "stat", 8192)
            end = raw.rfind(")")
            fields = raw[end+2:].split()
            try:
                identity = (int(folder.name), int(fields[19]))
                value = int(fields[11]) + int(fields[12])
                process_ticks[identity] = value
                delta = value - self.processes[identity] if identity in self.processes else None
                cpu = 100 * delta / self.hz / (now-self.at) if delta is not None and delta >= 0 and self.at and now > self.at else None
                rows.append({"pid": identity[0], "name": status.label(raw[raw.index("(")+1:end], 80),
                             "cpu": cpu, "rss": max(0, int(fields[21])) * self.page_size})
            except (IndexError, ValueError):
                continue
        self.previous, self.processes, self.at = ticks, process_ticks, now
        # Retain the union of both top lists so changing sort never starts another reader.
        top = {row["pid"]: row for row in sorted(rows, key=lambda row: row["cpu"] or 0, reverse=True)[:12]
               + sorted(rows, key=lambda row: row["rss"], reverse=True)[:12]}
        sample = self.telemetry.read()
        memory = {key: int(value)*1024 for key, value in re.findall(r"^(\w+):\s+(\d+) kB$", status.text(status.PROC / "meminfo"), re.M)}
        total, used = sample["memory_total"] or 0, sample["memory_used"] or 0
        cached = min(max(0, total-used), max(0, memory.get("Cached", 0)+memory.get("Buffers", 0)+memory.get("SReclaimable", 0)-memory.get("Shmem", 0)))
        frequency = [float(value) for value in re.findall(r"^cpu MHz\s*:\s*([0-9.]+)$", status.text(status.PROC / "cpuinfo", 1048576), re.M)]
        load = [status.number(value) for value in status.text(status.PROC / "loadavg").split()[:3]]
        return {"cpu_percent": percent, "load": load, "temperature_c": sample["temperature_c"],
                "frequency_mhz": sum(frequency)/len(frequency) if frequency else None, "cpu_name": cpu_name(),
                "uptime_seconds": status.clock()["uptime_seconds"], "history": list(self.history), "threads": threads,
                "memory": {"total": total, "used": used, "cache": cached, "free": max(0, total-used-cached),
                           "swap_total": memory.get("SwapTotal", 0), "swap_used": max(0, memory.get("SwapTotal", 0)-memory.get("SwapFree", 0))},
                "processes": list(top.values())}


class Power:
    def __init__(self):
        self.history = []
        self.history_due = 0

    def read(self):
        service = "org.freedesktop.UPower"
        with ThreadPoolExecutor(max_workers=4) as pool:
            base = {key: pool.submit(reader) for key, reader in {
                "root": lambda: devices.properties("system", service, "/org/freedesktop/UPower", service),
                "devices": lambda: devices.call("system", service, "/org/freedesktop/UPower", service, "EnumerateDevices"),
                "display": lambda: devices.call("system", service, "/org/freedesktop/UPower", service, "GetDisplayDevice"),
                "profiles": lambda: devices.properties("system", "org.freedesktop.UPower.PowerProfiles",
                                                        "/org/freedesktop/UPower/PowerProfiles", "org.freedesktop.UPower.PowerProfiles"),
            }.items()}
            values = base["devices"].result()
            names = values[0] if values and isinstance(values[0], list) else []
            names = [name for name in sorted(value for value in names if isinstance(value, str))[:16]
                     if re.fullmatch(r"/org/freedesktop/UPower/devices/[A-Za-z0-9_]+", name)]
            # Start pack reads as soon as enumeration arrives; a slow profile
            # helper must not delay independent battery information.
            pending = {name: pool.submit(devices.properties, "system", service, name, service+".Device") for name in names}
            now = time.monotonic()
            if now >= self.history_due:
                display = base["display"].result()
                path = display[0] if display and isinstance(display[0], str) else ""
                if re.fullmatch(r"/org/freedesktop/UPower/devices/[A-Za-z0-9_]+", path):
                    pending["history"] = pool.submit(devices.call, "system", service, path, service+".Device", "GetHistory", "suu", "charge", "86400", "96")
            data = {key: future.result() for key, future in pending.items()}
            base = {key: future.result() for key, future in base.items()}
        root = base["root"]
        packs = []
        states = {1:"charging", 2:"discharging", 3:"empty", 4:"full", 5:"pending-charge", 6:"pending-discharge"}
        for path in names:
            row = data[path]
            if row.get("Type") != 2 or row.get("PowerSupply") is not True:
                continue
            full = status.number(row.get("EnergyFull"))
            present = row.get("IsPresent") is True and full is not None and full > 0
            packs.append({"name": status.label(str(row.get("NativePath") or "Battery").rsplit("/",1)[-1], 64),
                          "present": present, "percent": status.number(row.get("Percentage"), high=100) if present else None,
                          "state": states.get(row.get("State"), "unknown") if present else "absent",
                          "health": status.number(row.get("Capacity"), high=100) if present else None,
                          "full": full, "energy": status.number(row.get("Energy")), "watts": status.number(row.get("EnergyRate")),
                          "time_full": status.number(row.get("TimeToFull")), "time_empty": status.number(row.get("TimeToEmpty"))})
        available = [row for row in packs if row["present"]]
        full = sum(row["full"] for row in available)
        energy = sum(row["energy"] or 0 for row in available)
        energy_known = all(row["energy"] is not None for row in available)
        state = "charging" if any(row["state"] == "charging" for row in available) else "discharging" if root.get("OnBattery") else "full" if available and all(row["state"] == "full" for row in available) else "unknown"
        seconds = max((row["time_full" if state == "charging" else "time_empty"] or 0 for row in available), default=0)
        if now >= self.history_due:
            values = data.get("history", [])
            rows = values[0] if values and isinstance(values[0], list) else []
            cutoff = time.time()-86400
            self.history = sorted([{"time": row[0], "percent": row[1]} for row in rows[:192]
                                   if isinstance(row, list) and len(row) >= 3 and status.number(row[0]) is not None
                                   and row[0] >= cutoff and status.number(row[1], low=-1) is not None and 0 <= row[1] <= 100 and row[2] != 0], key=lambda row: row["time"])
            self.history_due = now+60
        # This is the public source read by powerprofilesctl. Its Python/GLib
        # startup is unnecessary for a read; mutations still use Omarchy.
        profile_state = base["profiles"]
        profiles = [row.get("Profile", {}).get("data") for row in profile_state.get("Profiles", []) if isinstance(row, dict)]
        profiles = [value for value in profiles if value in ("power-saver", "balanced", "performance")]
        return {"percent": min(100,100*energy/full) if full and energy_known else None, "state": state, "seconds": seconds or None,
                "watts": sum(row["watts"] for row in available) if available and all(row["watts"] is not None for row in available) else None,
                "supply": "battery" if root.get("OnBattery") is True else "ac" if root.get("OnBattery") is False else "unknown",
                "packs": packs, "history": self.history, "profiles": profiles,
                "profile": profile_state.get("ActiveProfile") if profiles else None}


def audio():
    data = parallel({"nodes": lambda: json_value(["pw-dump"], []),
                     "availability": lambda: status.probe_json(["omarchy-audio-sink-availability"]),
                     "volume": lambda: status.probe(["omarchy-audio-output-sink"])})
    values = [row for row in data["nodes"] if isinstance(row, dict)]
    defaults = {}
    for row in values:
        if row.get("type") == "PipeWire:Interface:Metadata" and row.get("props", {}).get("metadata.name") == "default":
            for entry in row.get("metadata", []):
                if not isinstance(entry, dict):
                    continue
                value = entry.get("value")
                if isinstance(value, dict):
                    defaults[entry.get("key")] = value.get("name")
    availability, volume_name = data["availability"], data["volume"]
    result = {"outputs": [], "inputs": [], "streams": []}
    for row in values:
        if row.get("type") != "PipeWire:Interface:Node":
            continue
        info = row.get("info") or {}
        props = info.get("props") or {}
        kind = {"Audio/Sink":"outputs", "Audio/Source":"inputs", "Audio/Source/Virtual":"inputs", "Stream/Output/Audio":"streams"}.get(props.get("media.class"))
        name = str(props.get("node.name") or "")
        if not kind or type(row.get("id")) is not int or type(props.get("object.serial")) is not int:
            continue
        if name == "quickshell" or kind == "streams" and name.startswith("omarchy_speaker_tuning"):
            continue
        params = {}
        for param in info.get("params", {}).get("Props", []):
            if isinstance(param, dict):
                params.update(param)
        channels = [number for value in params.get("channelVolumes", []) if (number := status.number(value)) is not None]
        volume = max(0, max(channels)) if channels else status.number(params.get("volume"))
        result[kind].append({"id": row["id"], "serial": props.get("object.serial"), "name": status.label(name, 256),
                             "label": status.label(props.get("node.description") or props.get("application.name") or props.get("node.nick") or name, 160),
                             "volume": 100*math.cbrt(volume) if volume is not None else None, "muted": params.get("mute") is True,
                             "active": name == defaults.get("default.audio."+("sink" if kind == "outputs" else "source")),
                             "available": availability.get(name) is not False, "volume_target": name == volume_name})
    for key in result:
        result[key].sort(key=lambda row:(not row["active"], row["label"].casefold()))
    return result


class System:
    def __init__(self):
        self.static = None
        release = dict(line.split("=",1) for line in status.text(Path("/etc/os-release")).splitlines() if "=" in line)
        # Local identity can be displayed while bounded native version probes
        # complete. It is collected only when this page is requested.
        self.initial = {"host": status.label(status.text(Path("/etc/hostname")).strip()),
                        "os": status.label(release.get("PRETTY_NAME", "").strip('"')),
                        "kernel": os.uname().release, "cpu": cpu_name(),
                        "release": status.record(ROOT / "release.json")}

    def read(self):
        if self.static is None:
            native = parallel({"gpu": lambda: status.probe(["lspci"]), "omarchy": lambda: status.probe(["omarchy", "version"]),
                               "hyprland": lambda: status.probe(["Hyprland", "--version"]), "quickshell": lambda: status.probe(["qs", "--version"])})
            gpu = native["gpu"] or ""
            gpu = "; ".join(line.split(": ",1)[-1] for line in gpu.splitlines() if re.search(r"VGA|3D controller|Display controller", line))
            self.static = {**self.initial, "gpu": status.label(gpu, 256),
                           "omarchy": status.label(native["omarchy"]),
                           "hyprland": status.label((native["hyprland"] or "").split(" built ")[0]),
                           "quickshell": status.label((native["quickshell"] or "").split(" (")[0])}
        disks = shutil.disk_usage("/")
        monitors = json_value(["hyprctl", "-j", "monitors"], [])
        return {**self.static, "disk_used": disks.used, "disk_total": disks.total,
                "uptime_seconds": status.clock()["uptime_seconds"],
                "displays": [{"name": status.label(row.get("name")), "width": row.get("width"), "height": row.get("height"),
                              "refresh": row.get("refreshRate"), "scale": row.get("scale")} for row in monitors],
                "input_method": status.label(status.probe(["fcitx5-remote", "-n"])) if shutil.which("fcitx5-remote") else ""}


def calendar_today():
    now = datetime.now().astimezone()
    return {"year": now.year, "month": now.month, "day": now.day, "weekday": now.isoweekday(),
            "iso_week": now.isocalendar().week, "iso_year": now.isocalendar().year,
            "day_of_year": now.timetuple().tm_yday, "days_in_year": 366 if calendar.isleap(now.year) else 365,
            "date": now.strftime("%Y-%m-%d"), "zone": now.strftime("%Z · UTC%z")}
