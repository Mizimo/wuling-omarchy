"""Content gate for the optional early theme capture, never for theme changes."""
import hashlib
import json
import os
from pathlib import Path
from . import ROOT, SCHEMA


def compatibility():
    try:
        contracts = json.loads((ROOT / "plugins/session/native-theme.json").read_text())["contracts"]
        upstream = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
        hashes = {}
        for name in {name for contract in contracts.values() for name in contract["files"]}:
            file = upstream / name
            hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
        matches = [(name, contract) for name, contract in contracts.items()
                   if all(hashes[file] == expected for file, expected in contract["files"].items())]
        if len(matches) != 1:
            return {"schema_version": SCHEMA, "ok": False, "reason": "Installed theme modules do not match a tested contract"}
        name, contract = matches[0]
        # A quick per-switch recheck in the shell, of the same bytes this
        # contract just accepted: Qt.md5 hashes a file's UTF-8 text.
        recheck = {}
        for file in contract["files"]:
            data = (upstream / file).read_bytes()
            data.decode("utf-8")
            recheck[str(upstream / file)] = hashlib.md5(data).hexdigest()
        return {"schema_version": SCHEMA, "ok": True, "contract": name, "recheck": recheck,
                "background_ms": contract["background_ms"], "scaled_duration": contract["scaled_duration"], "settle_ms": contract["settle_ms"]}
    except (OSError, ValueError, KeyError) as exc:
        return {"schema_version": SCHEMA, "ok": False, "reason": str(exc)}
