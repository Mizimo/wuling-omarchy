"""On-demand launcher data and argv execution; no resident collector."""

from pathlib import Path
import configparser
import fcntl
import json
import locale
import math
import os
import shlex
import shutil
import subprocess
import time
from . import Error, SCHEMA, atomic_write, command, paths


class AgentUnavailable(Error):
    code = "agent_unavailable"


def enabled(identifier):
    from .integration import identity
    path = paths()["home"] / ".config/omarchy/shell.json"
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    return identifier not in data.get("disabledPlugins", []) and (
        identifier.startswith("omarchy.") or any(identity(row) == identifier for row in data.get("plugins", [])))


def state_path():
    return paths()["state"] / "dispatch.json"


def history():
    path = state_path()
    empty = {"owner": "wuling.dispatch", "schema_version": SCHEMA, "apps": {}, "run": [], "ask": []}
    if path.is_symlink() or path.parent.is_symlink():
        raise Error("Dispatch state is a symlink; preserve it and choose a normal state path")
    if not path.exists():
        return empty
    if path.stat().st_size > 256 * 1024:
        raise Error("Dispatch history is too large")
    try:
        raw = json.loads(path.read_text())
    except ValueError as exc:
        raise Error("Dispatch history is invalid; preserve it before resetting") from exc
    if not isinstance(raw, dict) or raw.get("owner") != empty["owner"]:
        raise Error("Dispatch history is not owned by WULING")
    for kind in ("run", "ask"):
        if isinstance(raw.get(kind), list):
            empty[kind] = [s[:4096] for s in raw[kind] if isinstance(s, str)][:30]
    if isinstance(raw.get("apps"), dict):
        for key, row in list(raw["apps"].items())[:512]:
            if isinstance(row, dict) and isinstance(row.get("count"), (int, float)) and isinstance(row.get("last"), (int, float)):
                if math.isfinite(row["count"]) and math.isfinite(row["last"]):
                    empty["apps"][key] = {"count": max(0, min(100000, row["count"])), "last": row["last"]}
    return empty


def remember(kind, value):
    path = state_path()
    if path.parent.is_symlink():
        raise Error("Dispatch state directory is a symlink")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    lock = path.parent / ".dispatch.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        data = history()
        if kind == "apps":
            old = data["apps"].get(value, {})
            data["apps"][value] = {"count": min(100000, old.get("count", 0) + 1), "last": time.time()}
            data["apps"] = dict(sorted(data["apps"].items(), key=lambda pair: pair[1]["last"], reverse=True)[:512])
        else:
            data[kind] = [value] + [s for s in data[kind] if s != value][:29]
        atomic_write(path, json.dumps(data, ensure_ascii=False), 0o600)


def applications():
    roots = [Path(os.environ.get("XDG_DATA_HOME", paths()["home"] / ".local/share"))]
    roots += [Path(p) for p in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if p]
    desktops = set(filter(None, os.environ.get("XDG_CURRENT_DESKTOP", "Hyprland").split(":")))
    lang = (os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or locale.getlocale()[0] or "en").split(".")[0]
    hidden = set()
    omarchy = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
    for path in (omarchy / "default/omarchy/launcher.hides", paths()["home"] / ".config/omarchy/launcher.hides"):
        if path.is_file():
            hidden.update(line.strip().removesuffix(".desktop") for line in path.read_text().splitlines())
    seen, result = set(), []
    for root in roots:
        directory = root / "applications"
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.desktop")):
            identifier = str(path.relative_to(directory)).replace("/", "-")
            if identifier in seen:
                continue
            seen.add(identifier)  # A hidden user entry masks the system entry too.
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            parser.optionxform = str
            try:
                if identifier.removesuffix(".desktop") in hidden or path.stat().st_size > 256 * 1024:
                    continue
                parser.read_string(path.read_text())
                entry = parser["Desktop Entry"]
            except (OSError, UnicodeError, configparser.Error, KeyError):
                continue
            if entry.get("Type", "Application") != "Application" or any(entry.get(k, "false").lower() == "true" for k in ("Hidden", "NoDisplay")):
                continue
            only, exclude = set(entry.get("OnlyShowIn", "").split(";")), set(entry.get("NotShowIn", "").split(";"))
            if entry.get("OnlyShowIn") and not only & desktops or exclude & desktops:
                continue
            if entry.get("TryExec") and not shutil.which(entry["TryExec"]):
                continue
            def translated(key):
                return entry.get(key + "[" + lang + "]", entry.get(key + "[" + lang.split("_")[0] + "]", entry.get(key, "")))
            if not entry.get("Exec"):
                continue
            result.append({"id": identifier, "name": translated("Name") or identifier,
                           "detail": translated("GenericName") or translated("Comment"), "icon": entry.get("Icon", ""),
                           "terminal": entry.get("Terminal", "false").lower() == "true", "exec": entry["Exec"],
                           "path": str(path), "cwd": entry.get("Path", ""), "categories": entry.get("Categories", "")})
    return result


def terminal_argv(app):
    """Desktop Exec field expansion without passing metadata through a shell."""
    try:
        words = shlex.split(app["exec"])
    except ValueError as exc:
        raise Error("The application has an invalid Exec command") from exc
    result = []
    for word in words:
        if word in ("%f", "%F", "%u", "%U", "%d", "%D", "%n", "%N", "%v", "%m"):
            continue
        if word == "%i":
            if app["icon"]:
                result += ["--icon", app["icon"]]
            continue
        value, i = "", 0
        while i < len(word):
            if word[i] != "%":
                value += word[i]; i += 1; continue
            i += 1
            if i == len(word) or word[i] not in "%ck":
                raise Error("Unsupported embedded desktop field code")
            value += {"%": "%", "c": app["name"], "k": app["path"]}[word[i]]
            i += 1
        result.append(value)
    if not result:
        raise Error("The terminal application has no executable")
    return ["omarchy-launch-tui", *result]


def clipboard():
    if not enabled("omarchy.clipboard"):
        return []
    path = paths()["home"] / ".local/state/omarchy/clipboard-history.json"
    try:
        if path.stat().st_size > 16 * 1024 * 1024:
            return []
        rows = json.loads(path.read_text())
    except (OSError, ValueError):
        return []
    if not isinstance(rows, list):
        return []
    result = []
    for index, row in enumerate(rows[:500]):
        if not isinstance(row, dict):
            continue
        if row.get("type") == "text" and isinstance(row.get("text"), str):
            result.append({"id": index, "type": "text", "name": row["text"][:4096], "detail": "", "mime": "text/plain"})
        elif row.get("type") == "image" and isinstance(row.get("path"), str):
            result.append({"id": index, "type": "image", "name": Path(row["path"]).name, "detail": row.get("mime", "image/png"), "path": row["path"], "mime": row.get("mime", "image/png")})
    return result


def snapshot():
    saved = history()
    apps = applications()
    for app in apps:
        use = saved["apps"].get(app["id"], {})
        app["frecency"] = math.log1p(use.get("count", 0)) * 10 + (30 / (1 + max(0, time.time() - use.get("last", 0)) / 86400) if use else 0)
        for key in ("exec", "path", "cwd"):
            app.pop(key)
    return {"schema_version": SCHEMA, "apps": apps, "clip": clipboard(), "clip_enabled": enabled("omarchy.clipboard"), "run": saved["run"], "ask": saved["ask"]}


def detached(argv, cwd=None):
    subprocess.Popen(argv, cwd=cwd or None, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def native_launch(argv, new_session=False):
    # wl-copy deliberately outlives its caller. Inherited capture pipes keep
    # communicate() waiting after the helper has already returned; no output
    # is needed here, only the launcher status.
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=15, start_new_session=new_session)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def activate(kind, value):
    if kind not in ("apps", "clip", "run", "calc", "ask") or not isinstance(value, str) or not value or len(value) > 4096 or "\0" in value:
        raise Error("Invalid Dispatch selection")
    if kind == "apps":
        app = next((a for a in applications() if a["id"] == value), None)
        if app is None:
            raise Error("The application was removed or hidden; reopen Dispatch")
        argv = terminal_argv(app) if app["terminal"] else ["uwsm-app", "--", "gtk-launch", app["id"]]
        detached(argv, app["cwd"] if app["terminal"] else None)
        remember(kind, value)
    elif kind == "clip":
        if not value.isdecimal():
            raise Error("Invalid clipboard index")
        row = next((r for r in clipboard() if r["id"] == int(value)), None)
        if row is None:
            raise Error("The clipboard entry is no longer available")
        argv = ["omarchy-clipboard-paste-text", "--shift-insert", "--history-index", value] if row["type"] == "text" else ["omarchy-clipboard-paste-file", row["mime"], row["path"]]
        detached(argv)
    elif kind == "calc":
        # The small parser lives in the view; copying accepts only its number.
        try:
            if not math.isfinite(float(value)):
                raise ValueError()
        except ValueError as exc:
            raise Error("No finite calculation result to copy") from exc
        if not native_launch(["omarchy-clipboard-paste-text", "--copy-only", value]):
            raise Error("The result could not be copied")
    else:
        if kind == "run":
            detached(["omarchy-launch-tui", "bash", "-lc", value])
        else:
            if not native_launch(["omarchy", "agent", "prompt", value]):
                raise AgentUnavailable("The native agent could not be launched; check the default agent configuration")
        remember(kind, value)
    return {"schema_version": SCHEMA, "ok": True, "mode": kind}


def cleanup():
    path = state_path()
    if path.parent.is_symlink() or path.is_symlink():
        return
    try:
        if path.exists() and json.loads(path.read_text()).get("owner") == "wuling.dispatch":
            path.unlink()
            lock = path.parent / ".dispatch.lock"
            if lock.is_file() and not lock.is_symlink():
                lock.unlink()
    except (OSError, ValueError, AttributeError):
        pass
