"""On-demand, bounded Terminal data. Never starts an agent collector or daemon."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import html
import math
import os
import re
import signal
import shutil
import subprocess
import threading
import time
from . import Error, SCHEMA, paths

OVERVIEW_SECTIONS = ("clock", "link", "levels", "signal", "agent", "telemetry", "comms")
SECTIONS = OVERVIEW_SECTIONS + ("performance", "power", "audio", "system", "calendar", "wifi", "bluetooth", "tailnet", "config")
PROC = Path("/proc")
SYS = Path("/sys")
_stopping = threading.Event()
_children = set()
_children_lock = threading.Lock()


def stop_probes():
    with _children_lock:
        _stopping.set()
        for child in _children:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def text(path, limit=65536):
    try:
        with path.open() as stream:
            return stream.read(limit)
    except (OSError, UnicodeError):
        return ""


def record(path):
    try:
        value = json.loads(text(path, 1024 * 1024))
        return value if isinstance(value, dict) else {}
    except ValueError:
        return {}


def number(value, low=0, high=None):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return min(high, max(low, result)) if high is not None and math.isfinite(result) else max(low, result) if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def label(value, limit=160):
    return "".join(c for c in str(value or "") if c >= " " and c != "\x7f")[:limit]


def probe(argv, timeout=3):
    """Read commands have a deadline, including their subprocess descendants.

    Only selected fields reach stdout. Never echo a command's stderr, account
    record, network peer list or service response into a shell log.
    """
    try:
        with _children_lock:
            if _stopping.is_set():
                return None
            child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, start_new_session=True,
                                     env={**os.environ, "LC_ALL": "C.UTF-8"})
            _children.add(child)
        with child:
            try:
                output, _ = child.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.communicate()
                return None
            except BaseException:
                # A page may close during an initial synchronous device read.
                # Popen's context manager otherwise waits for that child.
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.communicate()
                raise
            return output.strip() if child.returncode == 0 else None
    except (OSError, UnicodeError):
        return None
    finally:
        if "child" in locals():
            with _children_lock:
                _children.discard(child)


def probe_json(argv):
    try:
        data = json.loads(probe(argv) or "null")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def clock():
    now = datetime.now().astimezone()
    uptime = text(PROC / "uptime").split()
    return {"iso": now.isoformat(), "epoch_ms": round(now.timestamp() * 1000),
            "time": now.strftime("%H:%M:%S"), "date": now.strftime("%Y-%m-%d"),
            "weekday": now.isoweekday(), "zone": now.tzname(),
            "uptime_seconds": number(uptime[0]) if uptime else None}


def agent_usage():
    # Omarchy owns both scheduling and credentials. Read only its display
    # records, projecting the handful of fields this compact surface needs.
    folder = paths()["state"].parent / "omarchy/agents/usage"
    config = record(paths()["home"] / ".config/omarchy/shell.json")
    if "omarchy.agents" in config.get("disabledPlugins", []):
        return []
    providers = {}
    for entries in config.get("bar", {}).get("layout", {}).values():
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and entry.get("id") == "omarchy.agents":
                    providers = entry.get("providers", {})
    default = text(paths()["home"] / ".config/omarchy/defaults/agent").strip()
    result = []
    for path in sorted(folder.glob("*.json"))[:64]:
        data = record(path)
        identity = data.get("id", "")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", identity):
            continue
        if isinstance(providers, dict) and isinstance(providers.get(identity), dict) and providers[identity].get("enabled") is False:
            continue
        limits = []
        raw_limits = data.get("limits", [])
        for limit in raw_limits[:12] if isinstance(raw_limits, list) else []:
            if not isinstance(limit, dict):
                continue
            fraction = number(limit.get("percent"), low=-1, high=1)
            if fraction is None or fraction < 0:
                continue
            resets = label(limit.get("resetsAt"), 64)
            try:
                reset_at = datetime.fromisoformat(resets.replace("Z", "+00:00")).timestamp()
            except (ValueError, OverflowError):
                reset_at = None
            if reset_at is not None and reset_at <= time.time():
                fraction, resets = 0, ""
            limits.append({"label": label(limit.get("label")), "title": label(limit.get("title")),
                           "fraction": fraction, "resets_at": resets})
        used = any((number(data.get(key)) or 0) > 0 for key in
                   ("totalPrompts", "totalSessions", "todayPrompts", "todaySessions", "activeDays"))
        if not limits and not used and not isinstance(data.get("balance"), dict):
            continue
        result.append({"id": identity, "name": label(data.get("name") or identity), "default": identity == default,
                       "plan": label(data.get("tierLabel")), "limits": limits})
    return result


def default_agent_name():
    identity = text(paths()["home"] / ".config/omarchy/defaults/agent", 128).strip()
    if not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", identity):
        return ""
    data = record(paths()["state"].parent / "omarchy/agents/usage" / (identity + ".json"))
    return label(data.get("name") or identity)


def links():
    # Active connection metadata only: never scan or log network names.
    def wifi():
        devices = probe(["nmcli", "-t", "-f", "TYPE", "device", "status"])
        if devices and "wifi" in devices.splitlines():
            state = probe(["nmcli", "radio", "wifi"])
            network = ""
            active = probe(["nmcli", "-t", "-f", "UUID,TYPE", "connection", "show", "--active"])
            for line in (active or "").splitlines():
                identifier, _, kind = line.partition(":")
                if kind in ("802-11-wireless", "wifi") and re.fullmatch(r"[0-9a-fA-F-]{36}", identifier):
                    network = label(probe(["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", "uuid", identifier]))
                    break
            return {"id": "wifi", "active": state == "enabled", "state": state,
                    "network": network, "panel": "omarchy.network", "action": "wifi"}
    def bluetooth():
        from .radios import bluetooth_present
        if bluetooth_present():
            state = probe(["omarchy-bluetooth-power", "is-on"])
            return {"id": "bluetooth", "active": state is not None,
                    "panel": "omarchy.bluetooth", "action": "bluetooth"}
    def tailscale():
        data = probe_json(["tailscale", "status", "--json"])
        if shutil.which("tailscale"):
            return {"id": "tailscale", "active": data.get("BackendState") == "Running",
                    "state": label(data.get("BackendState", "Unavailable")), "panel": "omarchy.tailscale", "action": "tailscale"}
    def dnd():
        state = probe(["omarchy-shell", "notifications", "isDnd"])
        if state in ("on", "off"):
            return {"id": "dnd", "active": state == "on", "panel": "notifications", "action": "dnd"}
    def night():
        if shutil.which("omarchy-toggle-nightlight") and shutil.which("hyprsunset"):
            data = probe_json(["omarchy-toggle-nightlight", "--status"])
            return {"id": "night", "active": data.get("temperature") is not None and data.get("enabled") is True,
                    "panel": "omarchy.monitor", "action": "night"}
    def power():
        state = probe(["powerprofilesctl", "get"])
        if state in ("power-saver", "balanced", "performance"):
            return {"id": "power", "active": state != "balanced", "state": state,
                    "panel": "omarchy.power", "action": "power"}
    with ThreadPoolExecutor(max_workers=6) as pool:
        return [value for value in pool.map(lambda fn: fn(), (wifi, bluetooth, tailscale, dnd, night, power)) if value]


def volume():
    sink = probe(["omarchy-audio-output-sink"])
    if not sink:
        return None
    raw = probe(["pactl", "get-sink-volume", sink])
    match = re.search(r"(\d+)%", raw or "")
    if not match:
        return None
    return {"percent": min(100, int(match[1])),
            "muted": probe(["pactl", "get-sink-mute", sink]) == "Mute: yes"}


def levels():
    with ThreadPoolExecutor(max_workers=2) as pool:
        audio = pool.submit(volume)
        display = pool.submit(probe, ["omarchy-brightness-display"])
        raw = display.result()
        return {"volume": audio.result(), "brightness": number(raw, high=100)}


def media():
    from .devices import media_times
    data = probe_json(["omarchy-shell", "media", "status"])
    if data.get("hasPlayer") is not True:
        return None
    return {key: label(data.get(key)) for key in ("identity", "title", "artist", "album")} | {
        "art_url": str(data.get("artUrl") or "")[:8192],
        "desktop_entry": label(data.get("desktopEntry")),
        "playing": data.get("playing") is True, "can_next": data.get("canGoNext") is True,
        "can_previous": data.get("canGoPrevious") is True,
        "can_toggle": data.get("canTogglePlaying") is True, **media_times(data)}


class Telemetry:
    def __init__(self):
        self.previous = None
        self.history = {key: [] for key in ("cpu", "memory", "temperature")}

    def read(self):
        cpu = text(PROC / "stat").splitlines()
        ticks = [int(n) for n in cpu[0].split()[1:9]] if cpu and cpu[0].startswith("cpu ") else []
        current = (sum(ticks), sum(ticks[3:5])) if len(ticks) >= 5 else None
        used = None
        if current and self.previous:
            total, idle = (a - b for a, b in zip(current, self.previous))
            if total > 0 and idle >= 0:
                used = max(0, min(100, 100 * (total - idle) / total))
        self.previous = current
        memory = dict(re.findall(r"^(\w+):\s+(\d+) kB$", text(PROC / "meminfo"), re.M))
        total = int(memory.get("MemTotal", 0)) * 1024
        available = int(memory.get("MemAvailable", 0)) * 1024
        memory_used = max(0, total - available) if "MemAvailable" in memory else None
        temperatures = []
        for device in sorted((SYS / "class/hwmon").glob("hwmon*")):
            if text(device / "name").strip() not in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
                continue
            for sensor in device.glob("temp*_input"):
                raw = number(text(sensor).strip(), low=-273)
                if raw is not None and 0 < raw < 150000:
                    temperatures.append(raw / 1000)
        temperature = max(temperatures) if temperatures else None
        samples = {"cpu": used, "memory": 100 * memory_used / total if total and memory_used is not None else None,
                   "temperature": temperature}
        for key, sample in samples.items():
            self.history[key] = (self.history[key] + [sample])[-40:]
        return {"cpu_percent": used, "memory_used": memory_used, "memory_total": total or None,
                "temperature_c": temperature, "history": dict(self.history)}


def comms():
    marker = probe_json(["omarchy-shell", "wuling.notifications", "log"])
    if marker.get("provider") != "wuling.notifications":
        return {"available": False, "items": []}
    from . import notifications
    try:
        rows = notifications.read()["history"]
        def plain(value):
            value = re.sub(r"<(?:br\s*/?|/p|/div)\s*>", "\n", str(value or ""), flags=re.I)
            return html.unescape(re.sub(r"<[^>]*>", "", value))
        def deeds(row):
            result = [{"index": -1, "label": ""}] if row["execArgv"] else []
            if marker.get("contract") == "4.5.0-rc2":
                try:
                    extra = json.loads(row["execActions"] or "[]")
                    if isinstance(extra, list) and len(extra) <= 3:
                        result += [{"index": i, "label": label(plain(entry["label"]), 80)}
                                   for i, entry in enumerate(extra) if isinstance(entry, dict)
                                   and isinstance(entry.get("label"), str) and isinstance(entry.get("argv"), list)]
                except ValueError:
                    pass
            return result
        return {"available": True, "items": [{"key": row["key"], "app": label(row["app"], 80),
                "summary": plain(row["summary"]), "body": plain(row["body"]), "time": row["ts"],
                "actions": deeds(row)} for row in sorted(rows, key=lambda r: r["ts"], reverse=True)]}
    except (Error, OSError, ValueError):
        return {"available": True, "items": [], "error": "Notification history is unavailable"}


class Collector:
    def __init__(self, sections=None):
        _stopping.clear()
        from .devices import battery_rows
        from . import details, radios
        self.sections = set(OVERVIEW_SECTIONS if sections is None else sections)
        if "telemetry" in self.sections:
            self.sections.add("batteries")
        self.telemetry = Telemetry()
        self.latest = {}
        self.readers = {"link": links, "levels": levels, "signal": media, "agent": agent_usage, "comms": comms, "batteries": battery_rows}
        for name, factory in (("performance", details.Performance), ("power", details.Power), ("system", details.System), ("wifi", radios.Wifi)):
            if name in self.sections:
                reader = factory()
                self.readers[name] = reader.read
                if hasattr(reader, "initial"):
                    self.latest[name] = reader.initial
        self.readers.update(audio=details.audio, calendar=details.calendar_today)
        self.readers.update(bluetooth=radios.bluetooth, tailnet=radios.tailnet)
        if "config" in self.sections:
            from .configuration import snapshot
            self.readers["config"] = snapshot
        self.pool = ThreadPoolExecutor(max_workers=5)
        self.pending = {}
        self.due = {}
        self.serial = 0
        self.ready = threading.Event()

    def read(self, wait=False):
        now = time.monotonic()
        for name, reader in self.readers.items():
            if name not in self.sections:
                continue
            if name not in self.pending and now >= self.due.get(name, 0):
                self.due.pop(name, None)
                self.pending[name] = self.pool.submit(reader)
                self.pending[name].add_done_callback(lambda _: self.ready.set())
            future = self.pending.get(name)
            if future and (wait or future.done()):
                try:
                    self.latest[name] = future.result()
                    if name == "agent":
                        self.latest["default_agent"] = default_agent_name()
                except (OSError, ValueError, TypeError, AttributeError):
                    self.latest[name] = None
                del self.pending[name]
                self.serial += 1
                self.due[name] = now + (1 if name in ("signal", "comms", "performance", "audio") else 2 if name in ("levels", "power", "wifi", "bluetooth", "tailnet") else 30 if name == "calendar" else 5)
        if "clock" in self.sections and now >= self.due.get("clock", 0):
            self.latest["clock"] = clock()
            self.due["clock"] = now + 1
            self.serial += 1
        if "telemetry" in self.sections and now >= self.due.get("telemetry", 0):
            self.latest["telemetry"] = self.telemetry.read()
            self.due["telemetry"] = now + 1
            self.serial += 1
        return {"schema_version": SCHEMA, "phase": "C", "sampled_at": datetime.now().astimezone().isoformat(),
                "capabilities": {"status_collection": True, "agent_collection": False},
                "pending": sorted(self.pending), **self.latest}

    def close(self):
        stop_probes()
        self.pool.shutdown(wait=True, cancel_futures=True)


def collect(sections=None):
    collector = Collector(sections)
    try:
        return collector.read(wait=True)
    finally:
        collector.close()


def watch(sections=None):
    def stop(signum, frame):
        raise KeyboardInterrupt
    original = signal.signal(signal.SIGTERM, stop)
    collector = Collector(sections)
    previous = None
    try:
        while True:
            collector.ready.clear()
            start = time.monotonic()
            sample = collector.read()
            revision = (collector.serial, tuple(sample["pending"]))
            if revision != previous:
                print(json.dumps(sample, ensure_ascii=False, separators=(",", ":")), flush=True)
                previous = revision
            interval = min(1, max(.01, min(collector.due.values(), default=start+1)-start))
            collector.ready.wait(max(.01, interval - (time.monotonic() - start)))
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        collector.close()
        signal.signal(signal.SIGTERM, original)
