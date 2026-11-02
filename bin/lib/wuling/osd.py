"""On-demand display names for an OSD; no collectors or saved device data."""

import json
from . import Error, SCHEMA
from .status import probe


def device(kind):
    if kind not in ("input", "output"):
        raise Error("OSD device must be input or output")
    name = probe(["omarchy-audio-output-sink"] if kind == "output" else ["pactl", "get-default-source"])
    try:
        rows = json.loads(probe(["pactl", "-f", "json", "list", "sinks" if kind == "output" else "sources"]) or "null")
    except ValueError:
        rows = None
    label = ""
    if name and isinstance(rows, list):
        selected = next((row for row in rows if isinstance(row, dict) and row.get("name") == name), {})
        label = selected.get("description", "")
    return {"schema_version": SCHEMA, "kind": kind, "name": label[:256] if isinstance(label, str) else ""}
