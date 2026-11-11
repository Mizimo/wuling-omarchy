"""Installed-module gate and bounded private state. Never log message text."""
from pathlib import Path
import hashlib
import fcntl
import html
import json
import os
import re
import sys
import tempfile
import time
from . import Error, ROOT, SCHEMA, command, paths
from . import settings
from .status import probe

LIMIT = 100
TTL = 86400
MAX_INPUT = 4 * 1024 * 1024
STRINGS = {"key":120, "execArgv":32768, "execActions":32768, "glyph":16,
           "app":256, "appIcon":256, "summary":2048, "body":32768,
           "rawBody":32768, "source":253, "groupKey":1024}
NUMBERS = ("originalId", "senderPid", "urgency", "expireTimeout", "duration", "ts", "closed_ts", "remaining", "deadline")
CODE_WORDS = re.compile(r"\b(?:code|otp|verification|verify|passcode|pin|2fa|security\s+key|confirm(?:ation)?)\b|驗證|验证|認證|认证|動態密碼|动态密码", re.I)
CODE_SHAPE = re.compile(r"(?<!\w)(?:[A-Z]-)?(?:\d{4,8}|\d{2,4}[ -]\d{2,5}|[A-Z0-9]{5,8})(?!\w)")


def compatibility():
    try:
        contracts = json.loads((ROOT / "plugins/notifications/native-modules.json").read_text())["contracts"]
        upstream = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "shell/plugins/notifications"
        hashes = {}
        for name in {name for contract in contracts.values() for name in contract}:
            file = upstream / name
            hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
        matches = [name for name, contract in contracts.items()
                   if all(hashes[module] == expected for module, expected in contract.items())]
        if len(matches) != 1:
            mismatches = {name: [module for module, expected in contract.items() if hashes[module] != expected]
                          for name, contract in contracts.items()}
            raise Error("Installed notification modules do not match one known contract: " + json.dumps(mismatches))
        contract_name = matches[0]
        template = ROOT / "plugins/notifications" / {"4.0.6": "Rules406.qml.in", "4.5.0": "Rules450.qml.in"}[contract_name]
        qml = template.read_text()
        for name in contracts[contract_name]:
            qml = qml.replace("@" + name + "@", json.dumps((upstream / name).resolve().as_uri()))
        return {"schema_version": SCHEMA, "ok": True, "contract": contract_name, "qml": qml}
    except (Error, OSError, ValueError, KeyError) as exc:
        return {"schema_version": SCHEMA, "ok": False, "reason": str(exc)}


def filename():
    return paths()["state"] / "notifications.json"


def safe_number(value):
    return value if type(value) in (float, int) and abs(value) < 1e15 else 0


def project(row, limit, history=False):
    if not isinstance(row, dict) or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", str(row.get("key", ""))):
        return None
    out = {key: row.get(key, "")[:bound] if isinstance(row.get(key, ""), str) else "" for key, bound in STRINGS.items()}
    out.update({key: safe_number(row.get(key, 0)) for key in NUMBERS})
    # Match the 4.5 persistence boundary on both versions. The installed 4.5
    # module performs its own detection first; this is also a defensive check
    # for 4.0.6 and a state file supplied to the public command.
    plain = re.sub(r"<[^>]*>", " ", html.unescape(" ".join(str(row.get(key, "")) for key in ("summary", "rawBody", "body"))))
    secret = row.get("code") or row.get("codes") or (CODE_WORDS.search(plain) and CODE_SHAPE.search(plain))
    redacted = row.get("summary") == "Verification notification" and row.get("body") == "[redacted]"
    if secret or redacted:
        for key in STRINGS:
            if key != "key":
                out[key] = ""
        out.update(summary="Verification notification", body="[redacted]", rawBody="[redacted]")
    if out["rawBody"] == out["body"]:
        out["rawBody"] = ""
    if history:
        out["closed_reason"] = row.get("closed_reason", "") if re.fullmatch(r"[a-z]{1,32}", str(row.get("closed_reason", ""))) else ""
    def size():
        return len(json.dumps(out, ensure_ascii=False).encode())
    while size() > limit and (out["body"] or out["rawBody"]):
        out["body"] = out["body"][:len(out["body"]) * 3 // 4]
        out["rawBody"] = out["rawBody"][:len(out["rawBody"]) * 3 // 4]
    if size() > limit:
        out["execArgv"] = out["execActions"] = ""
    while size() > limit and out["summary"]:
        out["summary"] = out["summary"][:len(out["summary"]) * 3 // 4]
    return out


def normalise(data, now=None):
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA:
        raise Error("Invalid notification state schema")
    now = time.time() if now is None else now
    def rows(key, bound):
        source = data.get(key, [])
        if not isinstance(source, list):
            raise Error("Invalid notification rows")
        result = []
        seen = set()
        for raw in source[:LIMIT]:
            row = project(raw, bound, key == "history")
            if not row or row["key"] in seen:
                continue
            if key == "history" and not now - TTL < row["closed_ts"] <= now + 60:
                continue
            seen.add(row["key"])
            result.append(row)
        return result
    return {"schema_version": SCHEMA, "owner": "wuling.notifications", "dnd": data.get("dnd") is True,
            "live": rows("live", 16384), "history": rows("history", 4096)}


def native_dnd(gate):
    if not gate.get("ok"):
        return False
    relative = {"4.0.6": "notifications.json", "4.5.0": "notifications/quiet.json"}.get(gate.get("contract"))
    if not relative:
        return False
    path = paths()["home"] / ".local/state/omarchy" / relative
    try:
        if path.stat().st_size > 262144:
            return False
        raw = json.loads(path.read_text())
        return isinstance(raw, dict) and raw.get("dnd") is True
    except (OSError, ValueError):
        return False


def read(gate=None):
    path = filename()
    if path.is_symlink():
        raise Error("Notification state is a symlink; refusing to follow it")
    if not path.exists():
        return {"schema_version": SCHEMA, "dnd": native_dnd(gate or compatibility()), "live": [], "history": []}
    if path.stat().st_size > MAX_INPUT:
        raise Error("Notification state exceeds its size limit")
    return normalise(json.loads(path.read_text()))


def write(data):
    clean = normalise(data)
    directory = paths()["state"]
    if directory.is_symlink() or filename().is_symlink():
        raise Error("Notification state path is a symlink; refusing to replace it")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.stat().st_uid != os.getuid():
        raise Error("Notification state directory has another owner")
    directory.chmod(0o700)
    fd, temporary = tempfile.mkstemp(prefix=".notifications-", dir=directory)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(clean, stream, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
        os.replace(temporary, filename())
    finally:
        Path(temporary).unlink(missing_ok=True)


def persist():
    # One line at a time, bounded before JSON parsing. No file content or
    # subprocess response is echoed into shell logs or acknowledgements.
    while True:
        line = sys.stdin.buffer.readline(MAX_INPUT + 1)
        if not line:
            return
        try:
            if len(line) > MAX_INPUT:
                raise Error("Notification update exceeds its size limit")
            write(json.loads(line))
            reply = {"schema_version": SCHEMA, "ok": True}
        except (Error, OSError, ValueError):
            reply = {"schema_version": SCHEMA, "ok": False, "reason": "Cannot persist notification state"}
        print(json.dumps(reply), flush=True)


def writer_health():
    from .dispatch import enabled
    if not enabled("wuling.notifications"):
        return {"schema_version": SCHEMA, "ok": True, "enabled": False, "reason": "Plugin disabled"}
    try:
        raw = probe(["omarchy-shell", "wuling.notifications", "writer"])
        value = json.loads(raw or "null")
        if isinstance(value, dict) and value.get("schema_version") == SCHEMA and type(value.get("ok")) is bool:
            return {**value, "enabled": True}
    except (ValueError, TypeError):
        pass
    return {"schema_version": SCHEMA, "ok": False, "enabled": True,
            "reason": "Enabled notification writer has no health response"}


def claim_warning():
    """One warning per compositor session, including plugin/shell restarts."""
    from .session import runtime
    identity = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    if not identity:
        raise Error("No compositor session identity")
    marker = runtime() / "notification-writer-warning"
    fd = os.open(marker, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "r+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        token = hashlib.sha256(identity.encode()).hexdigest()
        if stream.read(128) == token:
            return {"schema_version": SCHEMA, "claimed": False}
        stream.seek(0); stream.truncate(); stream.write(token)
        return {"schema_version": SCHEMA, "claimed": True}


def fallback():
    # The native clone contract restores only a previously enabled source.
    command(["omarchy", "plugin", "disable", "wuling.notifications"])
    return {"schema_version": SCHEMA, "ok": True}


def cleanup_state(installed=False):
    directory = paths()["state"]
    if directory.is_symlink():
        raise Error("Notification state directory is a symlink; refusing to follow it")
    target = filename()
    if target.is_symlink():
        if installed:
            target.unlink()
        return
    if target.is_file():
        try:
            ours = json.loads(target.read_text()).get("owner") == "wuling.notifications"
        except (ValueError, OSError):
            ours = False
        if installed or ours:
            target.unlink()
    for temporary in directory.glob(".notifications-*"):
        if temporary.is_file() and not temporary.is_symlink() and temporary.stat().st_uid == os.getuid():
            temporary.unlink()
    try:
        directory.rmdir()
    except OSError:
        pass


def terminals():
    try:
        monitors = json.loads(probe(["hyprctl", "-j", "monitors"]) or "[]")
    except ValueError:
        monitors = []
    result = {}
    for monitor in monitors if isinstance(monitors, list) else []:
        name = monitor.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[\w.-]{1,120}", name):
            continue
        try:
            row = json.loads(probe(["omarchy-shell", "wuling.terminal." + name, "geometry"]) or "null")
            if isinstance(row, dict):
                result[name] = row
        except ValueError:
            pass
    return result


def boot():
    gate = compatibility()
    if gate["ok"]:
        gate["state"] = read(gate)
    return gate


def open_history():
    resolved = settings.tokens()["defaults"]["terminal.sections"]
    if "comms" not in settings.load().get("terminal.sections", resolved):
        return {"schema_version": SCHEMA, "opened": False}
    try:
        monitors = json.loads(probe(["hyprctl", "-j", "monitors"]) or "[]")
        focused = next((row.get("name", "") for row in monitors if row.get("focused")), "")
        if not re.fullmatch(r"[\w.-]{1,120}", focused):
            return {"schema_version": SCHEMA, "opened": False}
        response = probe(["omarchy-shell", "wuling.terminal." + focused, "history"])
        return {"schema_version": SCHEMA, "opened": response == "ok"}
    except (ValueError, TypeError):
        return {"schema_version": SCHEMA, "opened": False}
