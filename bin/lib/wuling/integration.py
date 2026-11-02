"""Owned additions to native JSON and Lua; unrelated settings survive removal."""

from copy import deepcopy
from pathlib import Path
import json
import os
from . import Error, ROOT, paths
from . import owned

IDS = ("wuling.bar", "wuling.terminal")
BINDING = 'o.bind("SUPER + CTRL + G", "Field Terminal", "wuling terminal toggle")\n'


def installed_sources():
    return sorted((ROOT / "plugins").glob("*/manifest.json"))


def locations():
    root = paths()["home"] / ".config"
    return root / "omarchy/shell.json", root / "hypr/bindings.lua"


def identity(entry):
    return entry if isinstance(entry, str) else entry.get("id") if isinstance(entry, dict) else None


def parse(text):
    try:
        data = json.loads(text)
        if not isinstance(data, dict) or not isinstance(data.get("bar", {}), dict):
            raise ValueError("Expected a shell object")
        if not isinstance(data.get("bar", {}).get("layout", {}), dict) or not isinstance(data.get("plugins", []), list):
            raise ValueError("Expected native bar layout and plugin list")
        if not all(isinstance(items, list) for items in data.get("bar", {}).get("layout", {}).values()):
            raise ValueError("Expected bar section arrays")
        return data
    except ValueError as exc:
        raise Error("Native shell.json is invalid; preserve it and correct its structure first") from exc


def prepare(previous, execute):
    shell, bindings = locations()
    if shell.is_symlink() or bindings.is_symlink():
        raise Error("Native shell or bindings is a symlink; leave it under its existing manager")
    prior = (previous or {}).get("integration")
    if shell.exists():
        before = shell.read_text()
    else:
        default = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "config/omarchy/shell.json"
        if not default.is_file():
            raise Error("Cannot find native shell configuration; start an Omarchy session first")
        before = default.read_text()
    data = parse(before)
    old_bindings = bindings.read_text() if bindings.exists() else ""
    # Query the compositor's effective bindings, including dynamically loaded
    # user Lua. A textual scan alone would miss aliases and generated bindings.
    try:
        effective = json.loads(execute(["hyprctl", "-j", "binds"]))
        if not isinstance(effective, list):
            raise ValueError()
    except ValueError as exc:
        raise Error("Cannot inspect active keybindings; install from the Omarchy session") from exc
    owned_matches = 0
    for entry in effective:
        if entry.get("modmask") != 68 or entry.get("submap", ""):
            continue
        if str(entry.get("key", "")).upper() != "G" and entry.get("keycode") != 42:
            continue
        if prior and (entry.get("arg") == "wuling terminal toggle" or
                      entry.get("dispatcher") == "__lua" and entry.get("description") == "Field Terminal"):
            owned_matches += 1
            if owned_matches > 1:
                raise Error("Super+Ctrl+G has duplicate bindings; resolve them before updating")
            continue
        raise Error("Super+Ctrl+G is already bound; no files changed")
    written = owned.block(old_bindings, "bindings", BINDING, prior["bindings"]["written"] if prior else None)
    if prior:
        # Preserve deliberate native enable/disable, layout, and inline settings.
        return {"shell_text": before, "bindings_text": written, "record": deepcopy(prior)}
    entries = list(data.get("plugins", []))
    for group in data.get("bar", {}).get("layout", {}).values():
        entries.extend(group)
    if any(identity(entry) in IDS for entry in entries) or data.get("bar", {}).get("id") in IDS:
        raise Error("Native configuration already mentions WULING plugins that this installer does not own")
    changed = deepcopy(data)
    bar = changed.setdefault("bar", {})
    bar["id"] = "wuling.bar"
    bar.setdefault("layout", {}).setdefault("right", []).append({"id": "wuling.terminal"})
    return {"shell_text": json.dumps(changed, ensure_ascii=False, indent=2) + "\n", "bindings_text": written,
            "record": {"shell": {"before": before, "installed": changed, "created": not shell.exists()},
                       "bindings": {"written": written[len(old_bindings):], "created": not bindings.exists()}}}


def write(tx, prepared):
    shell, bindings = locations()
    for path, data in ((shell, prepared["shell_text"]), (bindings, prepared["bindings_text"])):
        tx.replace(path, data=data, mode=path.stat().st_mode & 0o777 if path.exists() else 0o644)


def remove_shell(text, record):
    data = parse(text)
    if data == record["installed"]:
        return record["before"], []
    # Omarchy's own commands reformat JSON. Compare owned values semantically,
    # then remove only those entries; an unrelated setting is never reverted.
    before = parse(record["before"])
    result = deepcopy(data)
    preserved = []
    if result.get("bar", {}).get("id") == "wuling.bar":
        if "id" in before.get("bar", {}):
            result["bar"]["id"] = before["bar"]["id"]
        else:
            result["bar"].pop("id", None)
    def retain(entry, target):
        if identity(entry) != target:
            return True
        if isinstance(entry, str) or entry == {"id": target}:
            return False
        preserved.append(target)
        return True
    for section, entries in result.get("bar", {}).get("layout", {}).items():
        result["bar"]["layout"][section] = [entry for entry in entries if retain(entry, "wuling.terminal")]
    # A native disable can already have removed our entries. Restore exact
    # original bytes only if all remaining values equal the baseline.
    return (record["before"] if result == before else json.dumps(result, ensure_ascii=False, indent=2) + "\n"), preserved


def remove(tx, record):
    preserved = []
    shell, bindings = locations()
    for path, key in ((shell, "shell"), (bindings, "bindings")):
        try:
            if path.is_symlink():
                raise Error("User replaced shared configuration with a symlink")
            if not path.exists():
                continue
            if key == "shell":
                restored, kept = remove_shell(path.read_text(), record[key])
                preserved.extend(kept)
                delete = record[key]["created"] and restored == record[key]["before"]
            else:
                restored = owned.block(path.read_text(), "bindings", None, record[key]["written"])
                delete = record[key]["created"] and restored == ""
            tx.replace(path, delete=True) if delete else tx.replace(path, data=restored, mode=path.stat().st_mode & 0o777)
        except (Error, OSError):
            preserved.append(str(path))
    return preserved


def is_owned_config(path):
    return path in ("omarchy/shell.json", "hypr/bindings.lua") or path.startswith("omarchy/plugins/wuling.") or path == "omarchy/plugins"
