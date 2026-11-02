"""Owned additions to native JSON and Lua; unrelated settings survive removal."""

from copy import deepcopy
from pathlib import Path
import json
import os
from . import Error, ROOT, paths
from . import jsonc, owned

IDS = ("wuling.bar", "wuling.terminal", "wuling.osd", "wuling.notifications", "wuling.dispatch", "wuling.power", "wuling.session")
BINDINGS = ((68, "G", 42, "Field Terminal", "wuling terminal toggle"),
            (64, "D", 32, "Dispatch", "wuling dispatch toggle"))
BINDING = ('o.bind("SUPER + CTRL + G", "Field Terminal", "wuling terminal toggle")\n'
           'o.bind("SUPER + D", "Dispatch", "wuling dispatch toggle")\n')


def add_independent(data, record):
    adopted = record.setdefault("independent", [])
    for path in installed_sources():
        manifest = json.loads(path.read_text())
        identifier = manifest["id"]
        if identifier not in ("wuling.dispatch", "wuling.power", "wuling.session") or identifier in adopted:
            continue
        if any(identity(row) == identifier for row in data.get("plugins", [])) or identifier in data.get("disabledPlugins", []):
            raise Error(f"Native configuration already mentions unowned {identifier}")
        data.setdefault("plugins", []).append({"id": identifier})
        adopted.append(identifier)


def installed_sources():
    return sorted((ROOT / "plugins").glob("*/manifest.json"))


def add_replacements(data, record):
    """Adopt new components once, using the native clone restoration contract."""
    adopted = record.setdefault("replacements", {})
    for path in installed_sources():
        manifest = json.loads(path.read_text())
        clone = manifest["id"]
        source = manifest.get("omarchy", {}).get("clonedFrom")
        if not source or clone in adopted:
            continue
        if clone == "wuling.notifications":
            from . import notifications
            gate = notifications.compatibility()
            if not gate["ok"]:
                record.setdefault("unavailable", {})[clone] = gate["reason"]
                continue
            record.get("unavailable", {}).pop(clone, None)
        if any(identity(entry) == clone for entry in data.get("plugins", [])):
            raise Error(f"Native configuration already mentions unowned {clone}")
        # A user may already have another replacement. Never silently install
        # a second owner of the same IPC target/server.
        for entry in data.get("plugins", []):
            other = identity(entry)
            if not isinstance(other, str) or "/" in other or other in (".", ".."):
                continue
            if other in data.get("disabledPlugins", []):
                continue
            other_path = paths()["home"] / ".config/omarchy/plugins" / other / "manifest.json"
            if other_path.is_file():
                try:
                    other_manifest = json.loads(other_path.read_text())
                except ValueError as exc:
                    raise Error(f"Cannot inspect active plugin {other}") from exc
                if other_manifest.get("omarchy", {}).get("clonedFrom") == source:
                    raise Error(f"{other} already replaces {source}; disable it before installing {clone}")
        disabled = data.setdefault("disabledPlugins", [])
        restores = data.setdefault("cloneSourceRestores", [])
        if clone in disabled or clone in restores:
            raise Error(f"Native configuration has an unowned setting for {clone}")
        adopted[clone] = {"source": source, "disabled_before": source in disabled}
        data.setdefault("plugins", []).append({"id": clone})
        if source not in disabled:
            disabled.append(source)
            restores.append(clone)
        if not restores:
            data.pop("cloneSourceRestores", None)


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
        if not all(isinstance(data.get(key, []), list) and all(isinstance(item, str) for item in data.get(key, []))
                   for key in ("disabledPlugins", "cloneSourceRestores")):
            raise ValueError("Expected native plugin state arrays")
        return data
    except ValueError as exc:
        raise Error("Native shell.json is invalid; preserve it and correct its structure first") from exc


def prepare(previous, execute):
    shell, bindings = locations()
    if shell.is_symlink() or bindings.is_symlink():
        raise Error("Native shell or bindings is a symlink; leave it under its existing manager")
    prior = (previous or {}).get("integration")
    def with_menu(result):
        if any(p.parent.name == "power" for p in installed_sources()):
            from . import power
            text, menu = power.prepare_extension(prior.get("menu") if prior else None)
            result["menu_text"] = text
            result["record"]["menu"] = menu
        return result
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
    owned_matches = {}
    for entry in effective:
        for mask, key, code, title, action in BINDINGS:
            if entry.get("modmask") != mask or entry.get("submap", ""):
                continue
            if str(entry.get("key", "")).upper() != key and entry.get("keycode") != code:
                continue
            if prior and action in prior["bindings"]["written"] and (entry.get("arg") == action or
                          entry.get("dispatcher") == "__lua" and entry.get("description") == title):
                owned_matches[key] = owned_matches.get(key, 0) + 1
                if owned_matches[key] > 1:
                    raise Error(f"{title} has duplicate bindings; resolve them before updating")
                continue
            raise Error(f"The {title} key is already bound; no files changed")
    written = owned.block(old_bindings, "bindings", BINDING, prior["bindings"]["written"] if prior else None)
    if prior:
        # Preserve deliberate enable/disable and layout choices. Only components
        # newly shipped in this upgrade receive their first-install defaults.
        record = deepcopy(prior)
        changed = deepcopy(data)
        add_replacements(changed, record)
        add_independent(changed, record)
        record["bindings"]["written"] = ("\n" if prior["bindings"]["written"].startswith("\n") else "") + owned.block("", "bindings", BINDING)
        return with_menu({"shell_text": before if changed == data else json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
                          "bindings_text": written, "record": record})
    entries = list(data.get("plugins", []))
    for group in data.get("bar", {}).get("layout", {}).values():
        entries.extend(group)
    if any(identity(entry) in IDS for entry in entries) or data.get("bar", {}).get("id") in IDS:
        raise Error("Native configuration already mentions WULING plugins that this installer does not own")
    changed = deepcopy(data)
    bar = changed.setdefault("bar", {})
    bar["id"] = "wuling.bar"
    bar.setdefault("layout", {}).setdefault("right", []).append({"id": "wuling.terminal"})
    record = {"shell": {"before": before, "installed": deepcopy(changed), "created": not shell.exists()},
              "bindings": {"written": written[len(old_bindings):], "created": not bindings.exists()}}
    add_replacements(changed, record)
    add_independent(changed, record)
    return with_menu({"shell_text": json.dumps(changed, ensure_ascii=False, indent=2) + "\n", "bindings_text": written,
                      "record": record})


def write(tx, prepared):
    shell, bindings = locations()
    for path, data in ((shell, prepared["shell_text"]), (bindings, prepared["bindings_text"])):
        tx.replace(path, data=data, mode=path.stat().st_mode & 0o777 if path.exists() else 0o644)
    if "menu_text" in prepared:
        from .power import extension_path
        path = extension_path()
        tx.replace(path, data=prepared["menu_text"], mode=path.stat().st_mode & 0o777 if path.exists() else 0o644)


def remove_shell(text, record, replacements=None, independent=None):
    data = parse(text)
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
    for clone, entry in (replacements or {}).items():
        result["plugins"] = [item for item in result.get("plugins", []) if retain(item, clone)]
        retained = any(identity(item) == clone for item in result["plugins"])
        if retained and clone not in result.setdefault("disabledPlugins", []):
            result["disabledPlugins"].append(clone)
        # The native command removes this flag when the user explicitly
        # disables a clone. Without it, do not override a later native choice.
        restores = result.get("cloneSourceRestores", [])
        if clone in restores:
            restores.remove(clone)
            if not entry["disabled_before"]:
                result["disabledPlugins"] = [item for item in result.get("disabledPlugins", []) if item != entry["source"]]
        for key in ("cloneSourceRestores", "disabledPlugins"):
            if key in result and not result[key]:
                result.pop(key)
    for identifier in independent or []:
        result["plugins"] = [item for item in result.get("plugins", []) if retain(item, identifier)]
        disabled = result.setdefault("disabledPlugins", [])
        if any(identity(row) == identifier for row in result["plugins"]):
            if identifier not in disabled:
                disabled.append(identifier)
        elif identifier in disabled:
            disabled.remove(identifier)
        if not disabled:
            result.pop("disabledPlugins", None)
    # A native disable can already have removed our entries. Restore exact
    # original bytes only if all remaining values equal the baseline.
    return (record["before"] if result == before else json.dumps(result, ensure_ascii=False, indent=2) + "\n"), preserved


def remove(tx, record):
    preserved = []
    if record.get("menu"):
        from .power import extension_path
        path = extension_path()
        if path.exists():
            try:
                if path.is_symlink():
                    raise Error("User replaced menu configuration with a symlink")
                text = path.read_text()
                try:
                    restored = jsonc.remove_member(text, record["menu"]["edit"])
                except Error:
                    current = jsonc.loads(text).get("system")
                    if not isinstance(current, dict) or current.get("action") != "wuling power toggle":
                        raise
                    # Keep edited labels/icons but do not leave our command
                    # pointing to an uninstalled executable.
                    current.pop("action")
                    before = record["menu"]["edit"].get("before")
                    old = jsonc.loads('{"system":' + before + '}').get("system", {}) if before else {}
                    if old.get("action"):
                        current["action"] = old["action"]
                    restored, _ = jsonc.set_member(text, "system", current)
                    preserved.append(str(path) + " (edited System fields)")
                if record["menu"]["created"] and restored == "{}\n":
                    tx.replace(path, delete=True)
                else:
                    tx.replace(path, data=restored, mode=path.stat().st_mode & 0o777)
            except (Error, OSError):
                preserved.append(str(path))
    shell, bindings = locations()
    for path, key in ((shell, "shell"), (bindings, "bindings")):
        try:
            if path.is_symlink():
                raise Error("User replaced shared configuration with a symlink")
            if not path.exists():
                continue
            if key == "shell":
                restored, kept = remove_shell(path.read_text(), record[key], record.get("replacements"), record.get("independent"))
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
    return path in ("omarchy/shell.json", "hypr/bindings.lua", "omarchy/extensions/omarchy-menu.jsonc") or path.startswith("omarchy/plugins/wuling.") or path == "omarchy/plugins"
