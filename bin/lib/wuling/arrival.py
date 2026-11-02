"""One bounded read for Arrival. No addresses, notification text or history."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import getpass
import json
import re
import socket
import time
from . import ROOT, SCHEMA, theme
from .status import probe, text


def prepare():
    started = time.monotonic()
    commands = {
        "compositor": ["hyprctl", "-j", "version"],
        "screens": ["hyprctl", "-j", "monitors"],
        "shell": ["omarchy", "version"],
        "link": ["nmcli", "-t", "-f", "DEVICE,STATE,TYPE", "device", "status"],
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {key: pool.submit(probe, argv, .22) for key, argv in commands.items()}
        resolved = theme.resolve()
        results = {key: job.result() for key, job in jobs.items()}
    within = time.monotonic() - started <= .3
    def plain(value, limit=120):
        return "".join(c for c in str(value or "") if c >= " " and c != "\x7f")[:limit]
    rows = []
    def row(key, value):
        rows.append({"key": key, "value": plain(value) if within and value else "—", "ok": bool(within and value)})
    try:
        value = json.loads(results["compositor"] or "null") or {}
        version = value.get("version", "")
    except (ValueError, AttributeError):
        version = ""
    row("compositor", "Hyprland " + version if version else "")
    row("shell", "omarchy-shell " + results["shell"] if results["shell"] else "")
    link = ""
    for line in (results["link"] or "").splitlines():
        fields = line.split(":")
        if len(fields) == 3 and fields[2] != "loopback" and fields[1].startswith("connected") and re.fullmatch(r"[\w.-]{1,32}", fields[0]):
            link = fields[0] + " · online"; break
    row("link", link)
    power = []
    battery_present = False
    for supply in sorted(Path("/sys/class/power_supply").glob("*")):
        kind = text(supply / "type").strip()
        if kind == "Battery":
            battery_present = True
            capacity = text(supply / "capacity").strip()
            power.append(supply.name + " " + (capacity + "%" if capacity.isdigit() else "—"))
        elif kind == "Mains" and text(supply / "online").strip() == "1":
            power.append("AC")
    if battery_present:
        row("power", " · ".join(power))
    row("operator", getpass.getuser())
    try:
        screens = json.loads(results["screens"] or "[]") if within else []
    except ValueError:
        screens = []
    return {"schema_version": SCHEMA, "host": plain(socket.gethostname(), 253).upper(),
            "resolved": resolved, "rows": rows, "copy": json.loads((ROOT / "plugins/session/i18n" / (resolved["language"] + ".json")).read_text()),
            "read_ms": round((time.monotonic()-started)*1000),
            "screens": [{"name": plain(s.get("name")), "width": s.get("width", 0),
                         "height": s.get("height", 0), "refresh": s.get("refreshRate", 0),
                         "focused": s.get("focused", False)} for s in screens if isinstance(s, dict)]}
