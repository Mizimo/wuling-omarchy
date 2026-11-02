"""The audited native theme writers, never a snapshot of application profiles.

Both supported releases edit only workbench.colorTheme in these config files.
Other retints publish outside .config or signal running apps. See
research/theme-effect-scope.md for the source audit and deliberate exclusions.
"""
from pathlib import Path
import base64
import json
import re
from . import Error, atomic_write
from . import jsonc

FILES = tuple(f"{editor}/User/settings.json" for editor in
              ("Code", "Code - Insiders", "VSCodium", "Cursor"))
DIRECTORIES = tuple(sorted({str(parent) for name in FILES
                            for parent in Path(name).parents if str(parent) != "."}))
KEY = "workbench.colorTheme"


def project(text, mode=0o644):
    found = jsonc.members(text)
    span = found.get(KEY)
    return {"member": text[slice(*span)] if span else None, "mode": mode,
            "scaffold": text if re.fullmatch(r"\s*\{\s*\}\s*", text) else None}


def safe_path(rel):
    root = Path.home() / ".config"
    path = root / rel
    return path if not any(p.is_symlink() for p in [path, *path.parents]) else None


def snapshot():
    result = {}
    for rel in DIRECTORIES:
        path = safe_path(rel)
        if path and path.is_dir():
            result[rel] = {"directory": True}
    for rel in FILES:
        path = safe_path(rel)
        if not path or not path.is_file():
            continue
        try:
            result[rel] = project(path.read_text(), path.stat().st_mode & 0o777)
        except (Error, UnicodeError):
            # Do not retain or rewrite an unparseable/shared configuration.
            result[rel] = {"unmanaged": True}
    return result


def normalize_entry(rel, entry):
    if entry is None:
        return None
    if rel in DIRECTORIES:
        return {"directory": True} if entry.get("directory") else {"unmanaged": True}
    if "data" in entry:
        try:
            # Migrate a legacy record only for the audited file, projecting
            # away every unrelated field before any new journal is written.
            return project(base64.b64decode(entry["data"]).decode(), entry.get("mode", 0o644))
        except (Error, UnicodeError, ValueError):
            return {"unmanaged": True}
    if "member" in entry:
        return {key: entry.get(key) for key in ("member", "mode", "scaffold")}
    return {"unmanaged": True}


def normalize(values):
    return {rel: normalize_entry(rel, value) for rel, value in values.items()
            if rel in FILES or rel in DIRECTORIES}


def changes(before, after):
    before, after = normalize(before), normalize(after)
    result = {}
    for rel in FILES:
        old, new = before.get(rel), after.get(rel)
        if old != new and any(value and value.get("member") is not None for value in (old, new)):
            result[rel] = {"before": old, "after": new}
            for directory in DIRECTORIES:
                if rel.startswith(directory + "/") and before.get(directory) != after.get(directory):
                    result[directory] = {"before": before.get(directory), "after": after.get(directory)}
    return result


def normalize_changes(values):
    return {rel: {side: normalize_entry(rel, change.get(side)) for side in ("before", "after")}
            for rel, change in values.items() if rel in FILES or rel in DIRECTORIES}


def replace_member(text, value):
    """Change just the native theme member, retaining other bytes/comments."""
    found = jsonc.members(text)
    if KEY in found:
        start, end = found[KEY]
        if value is not None:
            return text[:start] + value + text[end:]
        tokens = [t for t in jsonc.TOKEN.finditer(text)
                  if not t.group().isspace() and not t.group().startswith(("//", "/*"))]
        first = next(i for i, token in enumerate(tokens) if token.start() == start) - 2
        last = next(i for i, token in enumerate(tokens) if token.end() == end)
        left, right = tokens[first].start(), end
        if tokens[last + 1].group() == ",":
            right = tokens[last + 1].end()
        elif tokens[first - 1].group() == ",":
            left = tokens[first - 1].start()
        # Native sed inserts one space before a newly added first member.
        if left > 0 and text[left - 1:left] == " " and text[:left - 1].endswith("{"):
            left -= 1
        return text[:left] + text[right:]
    if value is None:
        return text
    point = text.index("{") + 1
    return text[:point] + " " + json.dumps(KEY) + ": " + value + ("," if found else "") + text[point:]


def restore(values, current, tx=None):
    preserved = []
    current = normalize(current)
    for rel, change in sorted(normalize_changes(values).items(), key=lambda row: row[0].count("/"), reverse=True):
        old, last = change["before"], change["after"]
        observed = current.get(rel)
        path = safe_path(rel)
        if not path or any(x and x.get("unmanaged") for x in (old, last, observed)):
            preserved.append(rel)
            continue
        if rel in DIRECTORIES:
            if old is None and path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
            continue
        # The pre-retint observation protects a user-selected theme, even if
        # applying the previous native theme overwrites it again meanwhile.
        desired = old if observed == last else observed
        if observed != last and observed != old:
            preserved.append(rel)
        if not path.exists():
            # Never recreate a profile the user removed.
            continue
        try:
            text = path.read_text()
            restored = replace_member(text, desired.get("member") if desired else None)
            empty = re.fullmatch(r"\s*\{\s*\}\s*", restored) is not None
            if desired and desired.get("scaffold") is not None and empty:
                restored = desired["scaffold"]
            if desired is None and empty:
                tx.replace(path, delete=True) if tx else path.unlink()
            elif restored != text:
                mode = path.stat().st_mode & 0o777
                tx.replace(path, data=restored, mode=mode) if tx else atomic_write(path, restored, mode)
        except (Error, OSError, UnicodeError):
            preserved.append(rel)
    return preserved
