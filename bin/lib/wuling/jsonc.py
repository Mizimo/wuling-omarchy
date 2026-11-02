"""Locate a top-level JSONC member without reformatting unrelated settings."""
import json
import re
from . import Error

TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/|[{}\[\]:,]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null|\s+', re.S)


def loads(text):
    """Read JSONC without treating comment/comma characters in strings as syntax."""
    tokens = []
    position = 0
    for match in TOKEN.finditer(text):
        if match.start() != position:
            raise Error("Unsupported JSONC syntax")
        position = match.end()
        value = match.group()
        if not value.isspace() and not value.startswith(("//", "/*")):
            tokens.append(value)
    if position != len(text):
        raise Error("Unsupported JSONC syntax")
    normal = "".join(value for i, value in enumerate(tokens)
                     if not (value == "," and i + 1 < len(tokens) and tokens[i + 1] in ("}", "]")))
    try:
        return json.loads(normal)
    except ValueError as exc:
        raise Error(f"Invalid JSONC: {exc}") from exc


def members(text):
    matches = list(TOKEN.finditer(text))
    position = 0
    tokens = []
    for token in matches:
        if token.start() != position:
            raise Error("Unsupported JSONC syntax; leave the file unchanged")
        position = token.end()
        raw = token.group()
        if not raw.isspace() and not raw.startswith(("//", "/*")):
            tokens.append(token)
    if position != len(text) or not tokens or tokens[0].group() != "{" or tokens[-1].group() != "}":
        raise Error("Expected a JSONC object")
    loads(text)
    result = {}
    index = 1
    while index < len(tokens) - 1:
        key = tokens[index]
        if not key.group().startswith('"') or tokens[index + 1].group() != ":":
            raise Error("Invalid JSONC member")
        name = json.loads(key.group())
        if name in result:
            raise Error(f"Duplicate JSONC member: {name}")
        first = index + 2
        end = first
        depth = 0
        while end < len(tokens):
            value = tokens[end].group()
            if depth == 0 and value in (",", "}"):
                break
            if value in ("{", "["):
                depth += 1
            elif value in ("}", "]"):
                depth -= 1
            end += 1
        result[name] = (tokens[first].start(), tokens[end - 1].end())
        index = end + (tokens[end].group() == ",")
    return result


def set_member(text, key, value, previous=None):
    """Return new text plus the exact owned edit needed for safe removal."""
    found = members(text)
    encoded = json.dumps(value, ensure_ascii=False)
    if previous is not None:
        if previous["kind"] == "insert":
            old = previous["written"]
            if text.count(old) != 1:
                raise Error(f"The owned {key} entry was edited; leaving it unchanged")
            written = previous["prefix"] + encoded + previous["suffix"]
            return text.replace(old, written, 1), {**previous, "written": written}
        if key not in found:
            raise Error(f"The owned {key} entry was removed")
        start, end = found[key]
        if text[start:end] != previous["written"]:
            raise Error(f"The owned {key} entry was edited; leaving it unchanged")
        return text[:start] + encoded + text[end:], {**previous, "written": encoded}
    if key in found:
        start, end = found[key]
        return text[:start] + encoded + text[end:], {"kind": "replace", "key": key, "before": text[start:end], "written": encoded}
    where = text.index("{") + 1
    prefix = '\n  // BEGIN WULING ' + key + '\n  ' + json.dumps(key) + ': '
    suffix = ("," if found else "") + '\n  // END WULING ' + key + '\n'
    written = prefix + encoded + suffix
    return text[:where] + written + text[where:], {"kind": "insert", "key": key, "prefix": prefix, "suffix": suffix, "written": written}


def remove_member(text, record):
    if record["kind"] == "insert":
        if text.count(record["written"]) != 1:
            raise Error("Owned JSONC block was edited; preserved")
        return text.replace(record["written"], "", 1)
    found = members(text)
    if record["key"] not in found:
        raise Error("Owned JSONC member was removed; preserved")
    start, end = found[record["key"]]
    if text[start:end] != record["written"]:
        raise Error("Owned JSONC member was edited; preserved")
    return text[:start] + record["before"] + text[end:]
