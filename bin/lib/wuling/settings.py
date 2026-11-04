"""Typed overrides without executing configuration or discarding comments."""

import json
import re
import tomllib
from . import Error, ROOT, paths, read_json

ENUMS = {
    "menu.selected": ("edge", "fill"),
    "sounds": ("essential", "full", "off"),
    "motion": ("full", "reduced"),
    "language": ("auto", "en", "zh-Hant", "zh-Hans"),
}


class InvalidMusic(Error):
    code = "invalid_music"


def check_music(value):
    """Inspect with pw-play's existing decoder; never play a validation stream.

    Validate only a new assignment. A removed old file must not break the
    settings reader, uninstall, or editing an unrelated key.
    """
    import ctypes
    import os
    import stat
    from pathlib import Path
    class Info(ctypes.Structure):
        _fields_ = [("frames", ctypes.c_int64), ("samplerate", ctypes.c_int),
                    ("channels", ctypes.c_int), ("format", ctypes.c_int),
                    ("sections", ctypes.c_int), ("seekable", ctypes.c_int)]
    try:
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError()
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError()
            library = ctypes.CDLL("libsndfile.so.1")
            library.sf_open_fd.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(Info), ctypes.c_int]
            library.sf_open_fd.restype = ctypes.c_void_p
            library.sf_close.argtypes = [ctypes.c_void_p]
            library.sf_close.restype = ctypes.c_int
            info = Info()
            handle = library.sf_open_fd(fd, 0x10, ctypes.byref(info), 0)
            if not handle:
                raise ValueError()
            library.sf_close(handle)
            if info.frames <= 0 or info.channels <= 0 or info.samplerate <= 0:
                raise ValueError()
        finally:
            os.close(fd)
    except (OSError, ValueError, AttributeError):
        raise InvalidMusic("Choose an existing audio file supported by pw-play, using an absolute path or ~/.") from None


def tokens():
    data = read_json(ROOT / "tokens/wuling.json")
    if not data or data.get("schema_version") != 1:
        raise Error("Unsupported token schema; reinstall a complete WULING release.")
    validate_tokens(data)
    return data


def validate_tokens(data):
    required = {"schema_version", "palettes", "omarchy_colors", "type", "geometry", "motion", "sound", "defaults", "presets", "themes"}
    if set(data) != required or set(data["palettes"]) != {"mist", "paper"} or set(data["presets"]) != {"field", "hud"}:
        raise Error("Incomplete or unknown token sections")
    expected = {"labels", "menu.selected", "terminal.sections", "sounds", "motion", "session.arrival", "session.exit", "session.theme", "language", "login_music"}
    if set(data["defaults"]) != expected:
        raise Error("Settings keys differ from the supported schema")
    for palette in data["palettes"].values():
        if any(not isinstance(v, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", v) for v in palette.values()):
            raise Error("Palette values must be six-digit RGB colours")
        if any(role not in palette for role in data["omarchy_colors"].values()):
            raise Error("Omarchy colour mapping refers to a missing palette role")
    for key, value in data["type"]["sizes"].items():
        if type(value) not in (int, float) or not 1 <= value <= 256:
            raise Error(f"Invalid type size: {key}")
    for key, value in data["geometry"].items():
        if type(value) not in (int, float) or value < 0:
            raise Error(f"Invalid geometry: {key}")
    for key, value in data["motion"].items():
        if isinstance(value, list):
            valid = len(value) == 4 and all(type(n) in (int, float) and 0 <= n <= 1 for n in value)
        else:
            valid = type(value) in (int, float) and 0 <= value <= 5000
        if not valid:
            raise Error(f"Invalid motion token: {key}")
    if not 0 <= data["sound"]["gain"] <= 1:
        raise Error("Sound gain must be between zero and one")
    for spec in data["themes"].values():
        if spec["preset"] not in data["presets"] or spec["palette"] not in data["palettes"]:
            raise Error("Theme refers to an unknown preset or palette")


def flatten(data, prefix=""):
    result = {}
    for key, value in data.items():
        name = prefix + key
        if isinstance(value, dict):
            result.update(flatten(value, name + "."))
        else:
            result[name] = value
    return result


def validate(key, value):
    defaults = tokens()["defaults"]
    if key not in defaults:
        raise Error(f"Unknown setting {key!r}. Supported: {', '.join(defaults)}")
    if key in ("labels", "session.arrival", "session.exit", "session.theme") and type(value) is not bool:
        raise Error(f"{key} must be true or false")
    if key in ENUMS and value not in ENUMS[key]:
        raise Error(f"{key} must be one of: {', '.join(ENUMS[key])}")
    if key == "terminal.sections":
        allowed = defaults[key]
        if (not isinstance(value, list) or any(not isinstance(x, str) or x not in allowed for x in value)
                or len(value) != len(set(value))):
            raise Error(f"terminal.sections must be a unique list from: {', '.join(allowed)}")
    if key == "login_music" and (not isinstance(value, str) or "\0" in value or "\n" in value):
        raise Error("login_music must be a path string, or an empty string to disable it")
    return value


def load(text=None):
    path = paths()["config"] / "overrides.toml"
    try:
        text = text if text is not None else (path.read_text() if path.exists() else "")
        data = flatten(tomllib.loads(text))
    except (OSError, ValueError) as exc:
        raise Error(f"Invalid overrides in {path}: {exc}") from exc
    if "schema_version" in data and data.pop("schema_version") != 1:
        raise Error("Unsupported overrides schema_version; keep a backup before migrating.")
    return {key: validate(key, value) for key, value in data.items()}


def parse_value(key, raw):
    if key in ("labels", "session.arrival", "session.exit", "session.theme"):
        value = {"true": True, "false": False}.get(raw, raw)
    elif key == "terminal.sections":
        try:
            value = json.loads(raw) if raw.lstrip().startswith("[") else raw.replace(",", " ").split()
        except ValueError as exc:
            raise Error("terminal.sections needs a JSON list or space-separated names") from exc
    else:
        value = raw
    return validate(key, value)


def updated_text(original, key, value):
    """Change one assignment, preserving unrelated text and TOML tables."""
    load(original)
    encoded = json.dumps(value, ensure_ascii=False)
    lines = original.splitlines(keepends=True)
    section = ""
    matches = []
    for index, line in enumerate(lines):
        table = re.match(r"\s*\[([^\[\]]+)\]\s*(?:#.*)?$", line)
        if table:
            section = table.group(1).strip().strip('"')
        assign = re.match(r'(\s*)([\w.-]+|"[^"\n]+")\s*=\s*(.*)', line)
        if assign:
            local = assign.group(2).strip('"')
            full = f"{section}.{local}" if section else local
            if full == key:
                matches.append(index)
                # Comments are preserved when they are outside quoted strings.
                tail = assign.group(3)
                quoted = escaped = False
                comment = ""
                for i, char in enumerate(tail):
                    if char == '"' and not escaped:
                        quoted = not quoted
                    if char == "#" and not quoted:
                        comment = " " + tail[i:].rstrip()
                        break
                    escaped = char == "\\" and not escaped
                lines[index] = f"{assign.group(1)}{assign.group(2)} = {encoded}{comment}\n"
    if not matches:
        # A quoted dotted key at the document root cannot change table context.
        lines.insert(0, f"{json.dumps(key)} = {encoded}\n")
    result = "".join(lines)
    expected = {**load(original), key: value}
    if load(result) != expected:
        raise Error("This TOML layout cannot be edited safely; edit the setting explicitly in overrides.toml.")
    return result
