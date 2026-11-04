"""Read the native key list on demand, without dispatching a listed action."""
import json
import os
from pathlib import Path
import re
import signal
from . import Error, SCHEMA, status

GROUPS = ("SHELL", "WINDOWS", "NAVIGATE", "APPS", "SYSTEM", "OTHER")
MODIFIERS = ((64, "SUPER"), (1, "SHIFT"), (4, "CTRL"), (8, "ALT"), (2, "CAPS"), (16, "MOD2"), (32, "MOD3"), (128, "MOD5"))


def key_name(value):
    value = value.upper()
    return {"GRAVE": "~", "ASCIICIRCUM": "^", "MOUSE:272": "LEFT MOUSE BUTTON", "MOUSE:273": "RIGHT MOUSE BUTTON", "MOUSE:274": "MIDDLE MOUSE BUTTON", "CONTROL": "CTRL"}.get(value, value)


def keycode_names():
    # The installed helper uses the active leading XKB layout too. Resolving
    # codes here is only for comparison, not for guessing a Lua action.
    args = ["xkbcli", "compile-keymap"]
    for option, flag in (("kb_layout", "--layout"), ("kb_variant", "--variant")):
        try:
            value = json.loads(status.probe(["hyprctl", "-j", "getoption", "input:" + option], timeout=2) or "{}").get("str", "").split(",")[0]
        except (ValueError, AttributeError):
            value = ""
        if value and re.fullmatch(r"[A-Za-z0-9_-]+", value):
            args.extend((flag, value))
    compiled = status.probe(args, timeout=3) or ""
    codes = dict(re.findall(r"<([A-Za-z0-9_]+)>\s*=\s*([0-9]+)\s*;", compiled))
    symbols = dict(re.findall(r"key\s+<([A-Za-z0-9_]+)>\s*\{\s*\[\s*([^,\s\]]+)", compiled))
    result = {"10": "1", "11": "2", "12": "3", "13": "4", "14": "5", "15": "6", "16": "7", "17": "8", "18": "9", "19": "0", "20": "MINUS", "21": "EQUAL", "59": "COMMA", "60": "PERIOD", "61": "SLASH"}
    result.update({code: key_name(symbols[name]) for name, code in codes.items() if symbols.get(name) not in (None, "NoSymbol")})
    try:
        platform = {key_name(key): key_name(label) for key, label in (line.split() for line in Path("/usr/share/omarchy-platform/key-names").read_text().splitlines() if len(line.split()) == 2)}
        result = {code: platform.get(symbol, symbol) for code, symbol in result.items()}
        result.update(platform)
    except OSError:
        pass
    return result


def supplement(rows, text, names):
    def identity(caps):
        return tuple(sorted(key_name(cap) for cap in caps[:-1])), key_name(caps[-1])
    seen = {identity(caps) for row in rows for caps in row["keys"]}
    records = re.split(r"^bind[^\n]*\n", text, flags=re.M)
    if len(records) < 2 or records[0].strip():
        raise Error("The active keybinding format is not supported")
    additions = []
    for record in records[1:]:
        fields = dict(re.findall(r"^\t([a-z]+): (.*)$", record, re.M))
        if not {"key", "keycode", "modmask", "dispatcher", "description"} <= fields.keys():
            raise Error("The active keybinding format is not supported")
        key = fields["key"].rsplit(" + ", 1)[-1]
        if key.startswith("switch:"):
            continue
        if not key and fields["keycode"] != "0":
            key = "code:" + fields["keycode"]
        if not key:
            raise Error("An active key has no readable key or keycode")
        try:
            mask = int(fields["modmask"])
            if not 0 <= mask <= 255:
                raise ValueError()
        except ValueError:
            raise Error("The active key modifier format is not supported") from None
        caps = [label for bit, label in MODIFIERS if mask & bit]
        # Keep the physical Copilot code even when a keyboard calls it F23.
        named = names.get(key[5:], key) if key.startswith("code:") and key != "code:201" else names.get(key_name(key), key)
        caps.append(named if named.startswith("code:") else key_name(named))
        ident = identity(caps)
        if ident in seen:
            continue
        seen.add(ident)
        description = fields["description"].strip()
        label = "" if description else "lua-undescribed" if fields["dispatcher"] == "__lua" else "binding-undescribed"
        additions.append({"description": description or ("Lua binding · no description" if label == "lua-undescribed" else "Binding · no description"), "description_key": label, "keys": [caps], "group": "OTHER", "source": "hyprctl binds"})
    return rows + additions


def group(description):
    value = description.casefold()
    patterns = (
        ("NAVIGATE", r"workspace|scratchpad|focus (?:left|right|up|down|on)"),
        ("WINDOWS", r"window|full screen|full width|tiling|floating|universal (?:copy|paste|cut)"),
        ("SHELL", r"menu|keybindings|field terminal|dispatch|keymap|notification|clipboard|emoji|bar |reminder|show (?:time|weather|calendar)|^activity$|background switcher"),
        ("SYSTEM", r"volume|audio|brightness|microphone|lock|suspend|reboot|shutdown|power|nightlight|screenshot|screenrecord|bluetooth|wi-fi|tailnet|monitor|display|zoom|webcam|battery|network|color picker|transcode"),
        ("APPS", r"terminal|browser|file manager|calculator|editor|agent|music|video|notes|tmux|herdr|chatgpt|docker|email|signal|obsidian|google photos|^calendar$"),
    )
    return next((name for name, pattern in patterns if re.search(pattern, value)), "OTHER")


def chords(value):
    result = []
    for alternative in value.split(" / "):
        parts = alternative.strip().split(" + ")
        if len(parts) == 1:
            caps = parts
        elif len(parts) == 2:
            modifiers = parts[0].split()
            if any(modifier not in ("SUPER", "CTRL", "CONTROL", "SHIFT", "ALT", "MOD2", "MOD3", "MOD5") for modifier in modifiers):
                raise Error("The native keybinding format is not supported")
            caps = modifiers + [parts[1].strip()]
        else:
            raise Error("The native keybinding format is not supported")
        if not all(caps) or len(caps) > 8:
            raise Error("The native keybinding format is not supported")
        result.append(caps)
    return result


def original_descriptions():
    language = status.probe(["omarchy-language"], timeout=2) or "en"
    if not re.fullmatch(r"[A-Za-z0-9-]+", language) or language == "en":
        return []
    catalog = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "default/i18n" / language / "keybindings.json"
    try:
        values = json.loads(catalog.read_text())
        return [(re.compile("^" + re.sub(r"%[0-9]+", r"[0-9]+", re.escape(value)) + "$"), key)
                for key, value in values.items() if isinstance(value, str) and value]
    except (OSError, ValueError, AttributeError):
        return []


def parse(text, translations=()):
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        keys, separator, description = line.partition(" → ")
        description = description.strip()
        if not separator or not description or len(line) > 8192 or any(ord(c) < 32 for c in line):
            raise Error("The native keybinding format is not supported")
        original = next((original for pattern, original in translations if pattern.fullmatch(description)), description)
        rows.append({"description": description, "keys": chords(keys), "group": group(original), "source": "native"})
    if not rows:
        raise Error("The native key list is unavailable; use Omarchy's Keybindings menu")
    return rows


def snapshot():
    # The QML reader can be closed during the native helper's source scan.
    # Cancel its whole subprocess group rather than leaving that scan behind.
    def stop(signum, frame):
        status.stop_probes()
        raise SystemExit(128 + signum)
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        value = status.probe(["omarchy-menu-keybindings", "--print"], timeout=8)
        if value is None:
            raise Error("Cannot read the native keys; use Omarchy's Keybindings menu")
        rows = parse(value, original_descriptions())
        raw = status.probe(["hyprctl", "binds"], timeout=3)
        if raw is None:
            raise Error("Cannot read the active keys; use Omarchy's Keybindings menu")
        rows = supplement(rows, raw, keycode_names())
        return {"schema_version": SCHEMA, "groups": list(GROUPS), "rows": rows, "source": "omarchy-menu-keybindings --print + hyprctl binds"}
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
