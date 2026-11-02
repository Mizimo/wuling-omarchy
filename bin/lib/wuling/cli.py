"""Stable command contracts for humans, agents and QML consumers."""

from pathlib import Path
import argparse
import json
import re
import shutil
from . import Error, ROOT, SCHEMA, command, paths
from . import actions, dispatch, lifecycle, notifications, osd, power, session, settings, status, theme


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def commands():
    rows = []
    for path in sorted((ROOT / "bin").glob("wuling-*")):
        meta = {}
        for line in path.read_text().splitlines():
            found = re.fullmatch(r"# omarchy:([\w-]+)=(.*)", line)
            if found:
                meta[found.group(1)] = found.group(2)
        if not meta.get("summary"):
            raise Error(f"Missing command metadata: {path.name}")
        rows.append({"command": "wuling " + path.name.removeprefix("wuling-").replace("-", " "), **meta})
    return {"schema_version": SCHEMA, "commands": rows}


def doctor():
    checks = []
    def add(name, ok, detail, remedy=""):
        checks.append({"name": name, "ok": ok, "detail": detail, "remedy": remedy if not ok else ""})
    try:
        version = lifecycle.compatibility()
        add("omarchy", True, version)
    except Error as exc:
        add("omarchy", False, str(exc), "Use a tested Omarchy release; run Omarchy's official update command.")
    for executable in ("omarchy", "omarchy-shell", "qs", "fc-match", "fc-cache", "dconf", "python3", "bash", "jq"):
        add("command:" + executable, shutil.which(executable) is not None, shutil.which(executable), "Restore the stock Omarchy dependency using omarchy pkg add.")
    try:
        settings.load()
        add("overrides", True, "Valid")
    except Error as exc:
        add("overrides", False, str(exc), "Correct the reported key in overrides.toml, preserving other settings.")
    record = lifecycle.manifest()
    add("installation", record is not None, "Owned installation" if record else "Not installed", "Run ./install from a complete WULING checkout.")
    if record:
        for name, entry in record["resources"].items():
            add("owned:" + entry["kind"], lifecycle.same_resource(Path(name), entry["stamp"]), name,
                "The resource changed or disappeared. Preserve user edits before reinstalling; do not force overwrite.")
    for family in ("Geist", "Geist Mono", "Barlow Condensed", "Material Symbols Sharp", "Noto Sans CJK TC"):
        try:
            actual = command(["fc-match", "-f", "%{family}", family])
            add("font:" + family, family in actual.split(","), actual, "Reinstall WULING fonts; CJK comes from Omarchy's noto-fonts-cjk.")
        except Error as exc:
            add("font:" + family, False, str(exc), "Check fontconfig and the user font directory.")
    plugins = sorted((ROOT / "plugins").glob("*/manifest.json"))
    if (ROOT / "plugins/notifications/native-modules.json").is_file():
        gate = notifications.compatibility()
        add("notifications:compatibility", gate["ok"], gate.get("version") or gate.get("reason"),
            "Keep Omarchy's native notifications enabled until WULING supports the installed modules.")
    for plugin in plugins:
        try:
            add("plugin:" + plugin.parent.name, True, command(["omarchy", "plugin", "validate", str(plugin.parent)]))
        except Error as exc:
            add("plugin:" + plugin.parent.name, False, str(exc), "Install a complete compatible WULING plugin artifact.")
    add("plugins", True, {"shipped": len(plugins), "note": "No product plugins in phase B" if not plugins else "Validated shipped manifests"})
    return {"schema_version": SCHEMA, "ok": all(row["ok"] for row in checks), "checks": checks}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"schema_version": SCHEMA, "error": {"code": "wuling_error", "message": message}})
        self.exit(2)


def main(argv=None):
    parser = JsonArgumentParser(prog="wuling", description="WULING themes and desktop components for Omarchy")
    sub = parser.add_subparsers(dest="verb", required=True)
    cmd = sub.add_parser("commands", help="List supported commands and metadata")
    cmd.add_argument("--json", action="store_true")
    th = sub.add_parser("theme", help="Resolve active theme and user settings")
    th.add_argument("action", choices=["resolve"])
    th.add_argument("--theme", help="Inspect a shipped theme instead of the active theme")
    th.add_argument("--json", action="store_true")
    cfg = sub.add_parser("config", help="Read or edit typed user overrides")
    cfg.add_argument("action", choices=["get", "set"])
    cfg.add_argument("key", nargs="?")
    cfg.add_argument("value", nargs="?")
    cfg.add_argument("--json", action="store_true")
    state = sub.add_parser("status", help="Read live Terminal state on demand")
    state.add_argument("--json", action="store_true")
    state.add_argument("--watch", action="store_true", help="JSON lines once a second; stop when the surface closes")
    state.add_argument("--sections", nargs="+", choices=status.SECTIONS)
    action = sub.add_parser("action", help="Run a named native Terminal action")
    action.add_argument("name", choices=actions.NAMES)
    action.add_argument("value", nargs="?")
    term = sub.add_parser("terminal", help="Open or close the Field Terminal")
    term.add_argument("action", choices=["open", "close", "toggle"])
    launch = sub.add_parser("dispatch", help="Open Dispatch or read its on-demand data")
    launch.add_argument("action", choices=["open", "close", "toggle", "snapshot", "activate"])
    launch.add_argument("mode", nargs="?", choices=["apps", "clip", "run", "calc", "ask"])
    launch.add_argument("value", nargs="?")
    pwr = sub.add_parser("power", help="Open the native System actions as WULING cards")
    pwr.add_argument("action", choices=["open", "close", "toggle", "snapshot"])
    motion = sub.add_parser("session", help="Preview session motion or execute a confirmed exit")
    motion.add_argument("action", choices=["preview", "exit", "arm"])
    motion.add_argument("value", nargs="?")
    display = sub.add_parser("osd", help="Read OSD device state on demand")
    display.add_argument("action", choices=["device"])
    display.add_argument("kind", choices=["input", "output"])
    notices = sub.add_parser("notifications", help="Inspect notification compatibility and private state")
    notices.add_argument("action", choices=["compatibility", "state", "persist", "fallback", "boot", "terminals", "open-history"])
    sub.add_parser("doctor", help="Check versions, files, fonts and plugins").add_argument("--json", action="store_true")
    sub.add_parser("uninstall", help="Plan and remove unchanged owned resources").add_argument("--yes", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.verb == "commands":
            emit(commands())
        elif args.verb == "theme":
            if args.theme and args.theme not in settings.tokens()["themes"]:
                raise Error("--theme must name one of the four shipped WULING themes")
            emit(theme.resolve(args.theme))
        elif args.verb == "config":
            if args.action == "get":
                if args.value is not None:
                    raise Error("config get accepts at most a key")
                values = theme.resolve()["settings"]
                if args.key and args.key not in values:
                    settings.validate(args.key, None)
                emit({"schema_version": SCHEMA, "path": str(paths()["config"] / "overrides.toml"),
                      "settings": {args.key: values[args.key]} if args.key else values, "overrides": settings.load()})
            else:
                if args.key is None or args.value is None:
                    raise Error("Usage: wuling config set <key> <value>")
                emit(lifecycle.set_config(args.key, args.value))
        elif args.verb == "status":
            if args.watch:
                status.watch(args.sections)
            else:
                emit(status.collect(args.sections))
        elif args.verb == "action":
            emit(actions.run(args.name, args.value))
        elif args.verb == "terminal":
            emit(actions.terminal(args.action))
        elif args.verb == "dispatch":
            if args.action == "snapshot":
                if args.mode or args.value:
                    raise Error("dispatch snapshot takes no arguments")
                emit(dispatch.snapshot())
            elif args.action == "activate":
                emit(dispatch.activate(args.mode, args.value))
            else:
                if args.mode or args.value:
                    raise Error("Dispatch open/close/toggle takes no arguments")
                actions.route(args.action, "wuling.dispatch")
                emit({"schema_version": SCHEMA, "ok": True, "action": args.action})
        elif args.verb == "power":
            emit(power.snapshot() if args.action == "snapshot" else power.toggle(args.action))
        elif args.verb == "session":
            if args.action == "arm":
                if args.value is not None:
                    raise Error("session arm reads its confirmation from stdin")
                emit(session.arm())
            else:
                if args.value is None:
                    raise Error("session preview/exit requires a value")
                emit(session.preview(args.value) if args.action == "preview" else session.run(args.value))
        elif args.verb == "osd":
            emit(osd.device(args.kind))
        elif args.verb == "notifications":
            if args.action == "persist":
                notifications.persist()
            elif args.action == "compatibility":
                emit(notifications.compatibility())
            elif args.action == "state":
                emit(notifications.read())
            elif args.action == "boot":
                emit(notifications.boot())
            elif args.action == "terminals":
                emit({"schema_version": SCHEMA, "terminals": notifications.terminals()})
            elif args.action == "open-history":
                emit(notifications.open_history())
            else:
                emit(notifications.fallback())
        elif args.verb == "doctor":
            result = doctor()
            emit(result)
            return 0 if result["ok"] else 1
        elif args.verb == "uninstall":
            lifecycle.uninstall(args.yes)
    except (Error, OSError, ValueError) as exc:
        emit({"schema_version": SCHEMA, "error": {"code": getattr(exc, "code", "wuling_error"), "message": str(exc)}})
        return 1
    return 0
