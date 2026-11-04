"""Config page: resolved WULING settings and native Omarchy entry points."""
from pathlib import Path
import os
from . import Error, jsonc, paths, theme


def snapshot():
    resolved = theme.resolve()
    background = paths()["current"] / "background"
    return {"settings": {key: entry["value"] for key, entry in resolved["settings"].items()},
            "theme": resolved["theme"] or "", "background": background.resolve().name if background.exists() else ""}


def native(value):
    if value in ("display", "input", "keys"):
        filename = {"display": "monitors.lua", "input": "input.lua", "keys": "bindings.lua"}[value]
        path = paths()["home"] / ".config/hypr" / filename
        if not path.is_file():
            raise Error("The native configuration file is unavailable")
        return ["omarchy-launch-config-editor", str(path)]
    routes = {"theme": ("appearance.theme", "style.theme"),
              "background": ("appearance.background", "style.background"),
              "font": ("appearance.font", "style.font"), "default-apps": ("setup.default",)}
    if value not in routes:
        raise Error("Unknown native configuration entry")
    # Select an installed route by content, not a version string. The menu
    # remains responsible for its providers, user extensions and actions.
    source = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "default/omarchy/omarchy-menu.jsonc"
    try:
        entries = jsonc.loads(source.read_text())
    except (OSError, Error):
        raise Error("The native configuration menu is unavailable") from None
    route = next((route for route in routes[value] if isinstance(entries, dict) and isinstance(entries.get(route), dict)), None)
    if not route:
        raise Error("The native configuration menu entry is unavailable")
    return ["omarchy-menu", "summon", route]
