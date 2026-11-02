"""Exit action timing lives outside the animation and its QML object lifetime."""

from pathlib import Path
import fcntl
import json
import math
import os
import subprocess
import sys
import threading
import time
import uuid
from . import Error, ROOT, SCHEMA, atomic_write, command, paths, settings, theme
from . import actions, dispatch, power


def arm():
    """Prepare during the open menu; only a confirmed line can start an exit.

    Fork after receipt so the action's timer survives QML/Process destruction.
    Before receipt this child is owned by the open menu and collects nothing.
    """
    # Prime lazy stdlib imports before the hold; this creates no visual tree.
    Path("/").as_uri()
    dispatch.enabled("wuling.session")
    print("ready", flush=True)
    raw = sys.stdin.readline(16385)
    if not raw or len(raw) > 16384:
        return {"schema_version": SCHEMA, "ok": False}
    validated(raw)
    pid = os.fork()
    if pid == 0:
        os.setsid()
        fd = os.open(os.devnull, os.O_RDWR)
        for target in (0, 1, 2):
            os.dup2(fd, target)
        if fd > 2:
            os.close(fd)
        try:
            run(raw)
        finally:
            os._exit(0)
    return {"schema_version": SCHEMA, "ok": True}


def ipc(method, argument=""):
    env = {**os.environ, "OMARCHY_SHELL_IPC_TIMEOUT": "0.35s"}
    try:
        result = subprocess.run(["omarchy-shell", "wuling.session", method, argument],
                                text=True, capture_output=True, timeout=.6, env=env)
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"


def runtime():
    root = os.environ.get("XDG_RUNTIME_DIR")
    if not root:
        raise Error("No graphical session runtime directory")
    directory = Path(root) / "wuling"
    if directory.is_symlink():
        raise Error("Session runtime directory is a symlink")
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.stat().st_uid != os.getuid():
        raise Error("Session runtime directory belongs to another user")
    return directory


def validated(raw):
    if len(raw) > 16384:
        raise Error("Exit request is too large")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("id") not in {"system." + name for name in power.DANGEROUS}:
        raise Error("Invalid exit selection")
    action = data.get("action")
    if not isinstance(action, str) or not action or len(action) > 8192 or "\0" in action:
        raise Error("Invalid native System action")
    started = data.get("started")
    if not isinstance(started, (int, float)) or not math.isfinite(started) or abs(time.time() * 1000 - started) > 30000:
        raise Error("Exit request has no recent hold completion time")
    return {"id": data["id"], "action": action, "started": started, "preview": data.get("preview") is True}


def mark_url(resolved, directory):
    if resolved["theme"] in settings.tokens()["themes"]:
        path = paths()["current"] / "theme/unlock.png"
        if path.is_file():
            return path.as_uri(), None
    # The distributable vector is ours; replace only its declared colour.
    source = ROOT / "plugins/session/assets/mark.svg"
    if source.is_file():
        text = source.read_text().replace("currentColor", resolved["colors"]["paper-0"]["value"])
        path = directory / "mark.svg"
        path.write_text(text)
        return path.as_uri(), path
    return "", None


def compositor():
    """Capture process identity once; stale Hyprland sockets are not liveness."""
    try:
        value = subprocess.run(["hyprctl", "instances", "-j"], capture_output=True, text=True, timeout=.3)
        for row in json.loads(value.stdout):
            if row.get("instance") == os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
                pid = int(row["pid"])
                return pid, Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        pass
    return None


def alive(identity):
    if identity is None:
        return True
    try:
        return Path(f"/proc/{identity[0]}/stat").read_text().rsplit(")", 1)[1].split()[19] == identity[1]
    except (OSError, IndexError):
        return False


def clear_lease(directory, token):
    path = directory / "exit-osd.json"
    try:
        if json.loads(path.read_text()).get("token") == token:
            path.unlink()
    except (OSError, ValueError):
        pass


class ActionDeadline:
    """The visual IPC is allowed to stall; the confirmed action is not."""
    def __init__(self, action, due):
        self.action, self.due = action, due
        self.wake = threading.Event()
        self.sent = None
        self.error = None
        self.thread = threading.Thread(target=self.deliver)
        self.thread.start()

    def deliver(self):
        self.wake.wait(max(0, self.due - time.time()))
        try:
            self.sent = time.time()
            subprocess.Popen(["bash", "-c", self.action], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as exc:
            self.error = exc

    def expedite(self):
        self.wake.set()

    def join(self):
        self.thread.join()
        if self.error:
            raise Error("The native exit action could not be launched") from self.error


def run(raw):
    request = validated(raw)
    directory = runtime()
    descriptor = os.open(directory / "exit.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"schema_version": SCHEMA, "ok": False, "busy": True}
        token = uuid.uuid4().hex
        temporary = directory / ("exit-" + token)
        temporary.mkdir(mode=0o700)
        mark = None
        shown = False
        reduced = False
        resolved = {"language": "en"}
        try:
            resolved = theme.resolve()
            reduced = resolved["settings"]["motion"]["value"] == "reduced"
            permitted = (request["preview"] or resolved["settings"]["session.exit"]["value"]) and dispatch.enabled("wuling.session")
        except (Error, OSError, ValueError, KeyError):
            permitted = False
        delay = (120 if reduced else 560) if permitted else 0
        due = request["started"] / 1000 + delay / 1000
        action = None if request["preview"] else ActionDeadline(request["action"], due)
        try:
            try:
                if permitted:
                    url, mark = mark_url(resolved, temporary)
                    payload = {"token": token, "started": request["started"], "reduced": reduced, "mark": url,
                               "ground": resolved["colors"]["ink-2"]["value"], "accent": resolved["colors"]["fill"]["value"]}
                    if not request["preview"]:
                        until = request["started"] + (120 if reduced else 560) + 10000
                        atomic_write(directory / "exit-osd.json", json.dumps({"owner":"wuling.session", "token":token, "until":until}), 0o600)
                    shown = ipc("begin", json.dumps(payload)) == "ready"
                    if shown and not request["preview"]:
                        # Dismiss an OSD already visible before the stamp, too.
                        try:
                            subprocess.Popen(["omarchy-shell", "osd", "close"], stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except OSError:
                            pass
            except (Error, OSError, ValueError, KeyError):
                # Visual setup is optional. It must never swallow the action.
                shown = False
            if not shown:
                clear_lease(directory, token)
                if action:
                    action.expedite()
            if request["preview"]:
                time.sleep(max(0, due - time.time()) + 1.5 if shown else 0)
                return {"schema_version": SCHEMA, "ok": True, "preview": True, "overlay": shown}
            action.join()
            if not shown:
                return {"schema_version": SCHEMA, "ok": True, "overlay": False}
            identity = compositor()
            # Refresh once from the actual dispatch time; normal expiry and
            # the worker's give-back share the same ten-second deadline.
            until = action.sent + 10
            atomic_write(directory / "exit-osd.json", json.dumps({"owner":"wuling.session", "token":token, "until":until*1000}), 0o600)
            while time.time() < until:
                if not alive(identity):
                    return {"schema_version": SCHEMA, "ok": True, "ended": True}
                time.sleep(.1)
            ipc("finish", token)
            shown = False
            clear_lease(directory, token)
            language = resolved.get("language", "en")
            title, body = {
                "zh-TW": ("工作階段仍在執行", "退出動作未結束工作階段，已返回桌面。"),
                "zh-CN": ("会话仍在运行", "退出操作未结束会话，已返回桌面。"),
            }.get(language, ("Session is still running", "The exit action did not end the session. The desktop is available again."))
            subprocess.Popen(["notify-send", "-a", "WULING", title, body], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return {"schema_version": SCHEMA, "ok": True, "ended": False}
        finally:
            if action:
                action.join()
            if shown:
                ipc("finish", token)
            clear_lease(directory, token)
            if mark:
                mark.unlink(missing_ok=True)
            try:
                temporary.rmdir()
            except OSError:
                pass


def preview(kind):
    if kind not in ("arrival", "exit"):
        raise Error("Choose arrival or exit")
    if command(["omarchy-shell", "lock", "isLocked"]) != "false":
        raise Error("Unlock before previewing session motion")
    if kind == "arrival":
        if not dispatch.enabled("wuling.session") or ipc("arrival") != "ready":
            raise Error("Enable WULING session motion before previewing Arrival")
    else:
        actions.route("open", "wuling.power", '{"previewExit":true}')
    return {"schema_version": SCHEMA, "ok": True, "preview": kind}
