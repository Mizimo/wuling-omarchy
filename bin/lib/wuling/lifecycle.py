"""User-level installation with explicit ownership, consent and rollback."""

from pathlib import Path
import json
import os
import re
import shutil
import tempfile
from . import Error, ROOT, command, paths, read_json
from . import integration, jsonc, owned, settings, theme, theme_effects

OWNER = "org.wuling.desktop"
PAYLOAD = ("bin", "tokens", "theme", "fonts", "skills", "kit", "plugins", "sounds")
SKILL_DIRS = (".agents/skills", ".claude/skills", ".codex/skills", ".pi/agent/skills", ".hermes/skills")
DESKTOP_KEYS = ("color-scheme", "gtk-theme", "icon-theme")
DESKTOP_VALUES = {
    "color-scheme": ("'prefer-dark'", "'prefer-light'"),
    "gtk-theme": ("'Adwaita-dark'", "'Adwaita'"),
    "icon-theme": ("'Yaru-yellow'", "'Yaru-olive'"),
}


def desktop_snapshot():
    return {"keys": {key: command(["dconf", "read", "/org/gnome/desktop/interface/" + key]) for key in DESKTOP_KEYS}}


def restore_desktop(original, current, last=None):
    if not original:
        return
    for key in DESKTOP_KEYS:
        value = current["keys"][key]
        ours = value in DESKTOP_VALUES[key] if last is None else value == last["keys"][key]
        desired = original["keys"][key] if ours else value
        address = "/org/gnome/desktop/interface/" + key
        command(["dconf", "write", address, desired] if desired else ["dconf", "reset", address])


def compatibility():
    version = command(["omarchy", "version"])
    if re.fullmatch(r"4\.0\.6(?:-[0-9.]+)?", version):
        boundary = "4.0.6"
    elif re.fullmatch(r"4\.5\.0-?rc2(?:-[0-9.]+)?", version):
        boundary = "4.5.0-rc2"
    else:
        raise Error(f"Omarchy {version} is not in the tested 4.0.6 / 4.5.0-rc2 compatibility set.")
    return {"installed": version, "boundary": boundary}


def manifest():
    data = read_json(paths()["state"] / "install.json")
    if data is not None and (data.get("owner") != OWNER or data.get("schema_version") != 1):
        raise Error("Existing WULING state is not a recognised installation; refusing to overwrite it")
    if data:
        data["theme_effects"] = theme_effects.normalize_changes(data.get("theme_effects", {}))
        if data.get("desktop"):
            data["desktop"] = {"keys": {key: data["desktop"].get("keys", {}).get(key, "") for key in DESKTOP_KEYS}}
    return data


def same_resource(path, record):
    return owned.stamp(path) == record


def save_manifest(tx, data):
    tx.replace(paths()["state"] / "install.json", data=json.dumps(data, indent=2) + "\n", mode=0o600)


def config_snapshot():
    """Read only the audited theme fields, never unrelated profile contents."""
    return theme_effects.snapshot()


def apply_theme(name, preserve_background=False):
    if preserve_background:
        # The installed official wrapper preserves backgrounds and, on 4.5,
        # waits for retints before our transaction records their effects.
        command(["omarchy", "theme", "refresh"])
    else:
        env = os.environ.copy()
        env["OMARCHY_THEME_WAIT"] = "1"
        env.pop("OMARCHY_THEME_SKIP_BACKGROUND", None)
        command(["omarchy", "theme", "set", name], env=env)


def apply_in_transaction(tx, name, preserve_background=False):
    tx.data["theme_restore"] = {"name": theme.active_name(), "before": config_snapshot(), "desktop": desktop_snapshot()}
    tx.flush()
    try:
        apply_theme(name, preserve_background)
    finally:
        # Even a failing official command may already have changed app files.
        tx.data["theme_restore"]["after"] = config_snapshot()
        tx.data["theme_restore"]["desktop_after"] = desktop_snapshot()
        tx.flush()


def restore_external(data):
    """Roll back official theme effects while preserving intervening edits."""
    if not data or not data.get("name"):
        return
    before, after = data["before"], data.get("after")
    if after is None:
        if theme.active_name() == data["name"]:
            return
        raise Error("Interrupted during the official theme command; journal retained. Inspect and restore the previous theme before recovery.")
    current = config_snapshot()
    desktop_current = desktop_snapshot()
    apply_theme(data["name"])
    restore_desktop(data.get("desktop"), desktop_current, data.get("desktop_after"))
    theme_effects.restore(effects(before, after), current)


def effects(before, after):
    return theme_effects.changes(before, after)


def restore_effects(tx, changes, current):
    return theme_effects.restore(changes, current, tx)


def prepare_payload(destination):
    destination.mkdir()
    for name in PAYLOAD:
        source = ROOT / name
        if source.exists():
            shutil.copytree(source, destination / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("LICENSE",):
        if (ROOT / name).is_file():
            shutil.copy2(ROOT / name, destination / name)


def plan_install(previous=None):
    p = paths()
    release = p["data"] / "current"
    resources = [(release, "release")]
    resources.extend((p["themes"] / name, "theme:" + name) for name in settings.tokens()["themes"])
    resources.extend(((p["home"] / ".local/share/fonts/wuling", "fonts"), (p["home"] / ".local/bin/wuling", "command")))
    for source in integration.installed_sources():
        identity = json.loads(source.read_text())["id"]
        resources.append((p["home"] / ".config/omarchy/plugins" / identity, "plugin:" + source.parent.name))
    for directory in SKILL_DIRS:
        parent = p["home"] / directory
        if parent.is_dir():
            resources.append((parent / "wuling", "skill"))
    old = (previous or {}).get("resources", {})
    conflicts = []
    for path, kind in resources:
        if str(path) in old:
            if not same_resource(path, old[str(path)]["stamp"]):
                conflicts.append(str(path))
        elif owned.exists(path):
            conflicts.append(str(path))
    if conflicts:
        raise Error("Not owned or edited; leaving everything unchanged: " + ", ".join(conflicts))
    return resources


def consent(plan, yes):
    print(plan, flush=True)
    if not yes:
        try:
            accepted = input("Proceed? [y/N] ").strip().lower() in ("y", "yes")
        except EOFError:
            accepted = False
        if not accepted:
            raise Error("Cancelled; no files changed. Use --yes for unattended execution.")


def install(yes=False, fastfetch=None):
    if os.geteuid() == 0:
        raise Error("Run the installer as your desktop user, without sudo.")
    with owned.locked():
        owned.recover()
        version = compatibility()
        previous = manifest()
        if previous and previous.get("fastfetch"):
            fastfetch = True
        elif fastfetch is None and not yes:
            try:
                fastfetch = input("Use the WULING mark in your fastfetch configuration? [y/N] ").strip().lower() in ("y", "yes")
            except EOFError:
                fastfetch = False
        resources = plan_install(previous)
        prepared = integration.prepare(previous, command) if integration.installed_sources() else None
        for source in integration.installed_sources():
            command(["omarchy", "plugin", "validate", str(source.parent)])
        overrides = settings.load()
        original = (previous or {}).get("original_theme") or theme.active_name()
        if not original:
            raise Error("No active Omarchy theme found; start an Omarchy session before installing.")
        fastfetch_path = Path.home() / ".config/fastfetch/config.jsonc"
        fastfetch_edit = None
        if fastfetch:
            if fastfetch_path.is_symlink():
                raise Error("fastfetch config is a symlink; leave it under its existing manager")
            old_text = fastfetch_path.read_text() if fastfetch_path.exists() else "{}\n"
            prior = (previous or {}).get("fastfetch")
            new_text, edit = jsonc.set_member(old_text, "logo", {"type": "kitty-direct", "source": str(paths()["data"] / "current/theme/fastfetch-logo.png"), "width": 16}, prior["edit"] if prior else None)
            fastfetch_edit = {"path": str(fastfetch_path), "edit": edit, "created": prior["created"] if prior else not fastfetch_path.exists()}
        consent("WULING installation plan\nRequired: Omarchy 4.0.6 or 4.5.0-rc2; installed: " + version["installed"]
                + "\nFiles/directories:\n" + "\n".join("  " + str(path) for path, _ in resources)
                + ("\nBar: WULING (native widgets retained). New keys: Super+Ctrl+G → Field Terminal, Super+D → Dispatch.\nComponents: bar, Terminal, OSD, notifications, Dispatch, power cards and exit motion. Notifications require compatible native modules. The System menu extension opens power cards; no native key changes. Updates preserve independent disablement; official shell restart after install." if prepared else "\nBuilt-ins changed: none. Keys added: none.")
                + ("\nUnavailable replacements: " + json.dumps(prepared["record"]["unavailable"]) if prepared and prepared["record"].get("unavailable") else "")
                + "\nDefault theme: wuling; updates keep the current theme. User overrides remain untouched."
                + ("\nFastfetch: replace only the logo member in " + str(fastfetch_path) if fastfetch else "\nFastfetch: unchanged (opt in with --fastfetch).")
                + "\nBoot unlock: optional official operation, not performed by this installer.", yes)
        before = config_snapshot()
        desktop_before = desktop_snapshot()
        active_before = theme.active_name()
        record = {"schema_version": 1, "owner": OWNER, "compatibility": version, "original_theme": original,
                  "resources": {}, "directories": list((previous or {}).get("directories", [])),
                  "theme_effects": (previous or {}).get("theme_effects", {})}
        record["desktop"] = (previous or {}).get("desktop", desktop_before)
        if fastfetch_edit:
            record["fastfetch"] = fastfetch_edit
        if prepared:
            record["integration"] = prepared["record"]
        with tempfile.TemporaryDirectory(prefix="wuling-stage-") as directory:
            staging = Path(directory)
            prepare_payload(staging / "release")
            for name in settings.tokens()["themes"]:
                target = staging / name
                shutil.copytree(ROOT / "theme" / name, target)
                for filename, text in theme.generated_text(name, overrides).items():
                    (target / filename).write_text(text)
            try:
                with owned.Transaction() as tx:
                    for path, kind in resources:
                        if kind == "release":
                            tx.replace(path, source=staging / "release")
                        elif kind.startswith("theme:"):
                            tx.replace(path, source=staging / kind.split(":", 1)[1])
                        elif kind == "fonts":
                            # Fontconfig scans hidden directories too. A sibling
                            # rollback copy becomes a second discoverable font;
                            # removing it after shell startup invalidates Qt's
                            # live font choices. Keep it outside the font tree.
                            if owned.stamp(path) != owned.stamp(ROOT / "fonts"):
                                tx.replace(path, source=ROOT / "fonts", backup_root=paths()["state"] / "font-backups")
                        elif kind == "command":
                            tx.replace(path, link=paths()["data"] / "current/bin/wuling")
                        elif kind == "skill":
                            tx.replace(path, link=paths()["data"] / "current/skills/wuling")
                        elif kind.startswith("plugin:"):
                            tx.replace(path, source=ROOT / "plugins" / kind.split(":", 1)[1])
                        record["resources"][str(path)] = {"kind": kind, "stamp": owned.stamp(path)}
                    if fastfetch_edit:
                        tx.replace(fastfetch_path, data=new_text)
                    if prepared:
                        integration.write(tx, prepared)
                    selected = active_before if previous else "wuling"
                    apply_in_transaction(tx, selected, preserve_background=bool(previous))
                    after = config_snapshot()
                    for key, value in effects(before, after).items():
                        if prepared and integration.is_owned_config(key):
                            continue
                        if key == "dconf/user":
                            continue
                        if key == "fastfetch/config.jsonc" and fastfetch_edit:
                            continue
                        existing = record["theme_effects"].get(key)
                        if existing and value["before"] == existing["after"]:
                            value["before"] = existing["before"]
                        record["theme_effects"][key] = value
                    record["directories"] = list(dict.fromkeys(record["directories"] + tx.data["directories"]))
                    save_manifest(tx, record)
                    command(["fc-cache", "-f", str(Path.home() / ".local/share/fonts/wuling")])
                    if prepared:
                        command(["hyprctl", "reload"])
                        command(["omarchy", "restart", "shell"])
            except Exception:
                # File changes are rolled back by Transaction. Reapply the prior
                # native theme after rollback so the running shell matches disk.
                if active_before and theme.active_name() != active_before:
                    apply_theme(active_before)
                if prepared:
                    command(["hyprctl", "reload"])
                    command(["omarchy", "restart", "shell"])
                raise
        print("WULING installed. Use wuling doctor to inspect the installation.")


def uninstall(yes=False):
    with owned.locked():
        owned.recover()
        record = manifest()
        if record is None:
            from . import dispatch, notifications
            dispatch.cleanup()
            notifications.cleanup_state()
            print("WULING is not installed; nothing changed.")
            return
        removable, preserved = [], []
        for name, entry in record["resources"].items():
            (removable if same_resource(Path(name), entry["stamp"]) else preserved).append(name)
        consent("WULING removal plan\nRemove unchanged owned resources:\n" + "\n".join("  " + name for name in removable)
                + "\nPreserve user overrides and edited resources:\n" + "\n".join("  " + name for name in preserved)
                + "\nRestore previous theme and unchanged owned native entries; retain edited configuration."
                + ("\nRestart the shell officially to release plugin IPC and reload the remaining keybindings." if record.get("integration") else ""), yes)
        with owned.Transaction() as tx:
            config_current = config_snapshot()
            if theme.active_name() in settings.tokens()["themes"]:
                desktop_current = desktop_snapshot()
                apply_in_transaction(tx, record["original_theme"])
                restore_desktop(record.get("desktop"), desktop_current)
            # Official theme restoration handles native output first. Restore
            # remaining unchanged effects, never a user's independently edited file.
            kept_effects = restore_effects(tx, record.get("theme_effects", {}), config_current)
            if record.get("integration"):
                preserved.extend(integration.remove(tx, record["integration"]))
            if record.get("fastfetch"):
                slot = record["fastfetch"]
                path = Path(slot["path"])
                try:
                    if path.is_symlink():
                        raise Error("fastfetch config was replaced with a symlink")
                    restored = jsonc.remove_member(path.read_text(), slot["edit"])
                    if slot["created"] and restored == "{}\n":
                        tx.replace(path, delete=True)
                    else:
                        tx.replace(path, data=restored)
                except (Error, OSError):
                    preserved.append(str(path))
            for name in removable:
                tx.replace(Path(name), delete=True)
            tx.replace(paths()["state"] / "install.json", delete=True)
        for directory in sorted(set(record.get("directories", [])), key=lambda x: len(Path(x).parts), reverse=True):
            try:
                Path(directory).rmdir()
            except OSError:
                pass
        for path in (paths()["data"], paths()["state"]):
            try:
                path.rmdir()
            except OSError:
                pass
        command(["fc-cache", "-f", str(Path.home() / ".local/share/fonts")])
        if record.get("integration"):
            command(["hyprctl", "reload"])
            command(["omarchy", "restart", "shell"])
        from . import dispatch, notifications
        dispatch.cleanup()
        notifications.cleanup_state(installed=True)
        print("WULING removed. User-owned configuration is preserved.")
        print("Native outputs outside the rollback list remain under Omarchy: theme-set hooks, editor extensions, agent palettes, Obsidian vault themes, Fcitx theme assets and browser policy. The previous theme was reapplied where applicable; these paths were not snapshotted or restored by WULING.")
        if preserved or kept_effects:
            print("Preserved changed paths: " + ", ".join(preserved + kept_effects))


def set_config(key, raw):
    value = settings.parse_value(key, raw)
    with owned.locked():
        owned.recover()
        path = paths()["config"] / "overrides.toml"
        original = path.read_text() if path.exists() else ""
        text = settings.updated_text(original, key, value)
        overrides = settings.load(text)
        record = manifest()
        if key == "menu.selected" and record is not None:
            for name in settings.tokens()["themes"]:
                target = paths()["themes"] / name
                entry = record["resources"].get(str(target))
                if not entry or not same_resource(target, entry["stamp"]):
                    raise Error(f"Installed theme was edited or removed: {target}; no settings changed")
        before = config_snapshot() if key == "menu.selected" and record is not None else {}
        with tempfile.TemporaryDirectory(prefix="wuling-config-") as directory, owned.Transaction() as tx:
            tx.replace(path, data=text, mode=0o600)
            if key == "menu.selected" and record is not None:
                for name in settings.tokens()["themes"]:
                    target = paths()["themes"] / name
                    staged = Path(directory) / name
                    shutil.copytree(target, staged)
                    for filename, content in theme.generated_text(name, overrides).items():
                        (staged / filename).write_text(content)
                    # Replace the theme as one owned resource. Per-file journal
                    # backups inside it would be staged by Omarchy and included
                    # in its manifest hash before transaction cleanup.
                    tx.replace(target, source=staged)
                    record["resources"][str(target)]["stamp"] = owned.stamp(target)
                if theme.active_name() in settings.tokens()["themes"]:
                    apply_in_transaction(tx, theme.active_name(), preserve_background=True)
                for name, effect in effects(before, config_snapshot()).items():
                    if name.startswith("wuling/") or name in ("wuling", "dconf/user"):
                        continue
                    if record.get("integration") and integration.is_owned_config(name):
                        continue
                    prior = record["theme_effects"].get(name)
                    if prior and prior["after"] == effect["before"]:
                        effect["before"] = prior["before"]
                    record["theme_effects"][name] = effect
                save_manifest(tx, record)
        return {"schema_version": 1, "key": key, "value": value, "path": str(path),
                "theme_reapplied": key == "menu.selected" and record is not None and theme.active_name() in settings.tokens()["themes"]}
