"""Observable settings and installation invariants without a display."""
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin/lib"))
from wuling import Error, paths
from wuling import jsonc, lifecycle, owned, settings, theme, theme_effects


class IsolatedHome(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wuling-test-")
        self.home = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {"HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"), "XDG_DATA_HOME": str(self.home / ".local/share"),
            "XDG_STATE_HOME": str(self.home / ".local/state"), "XDG_RUNTIME_DIR": str(self.home)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()


class SettingsTests(IsolatedHome):
    def test_local_setting_does_not_scan_unrelated_configuration(self):
        with patch("wuling.lifecycle.config_snapshot", side_effect=AssertionError("unexpected native snapshot")):
            lifecycle.set_config("language", "zh-Hant")
        self.assertEqual(settings.load()["language"], "zh-Hant")

    def test_bad_tokens_fail_before_generation(self):
        source = settings.tokens()
        source["type"]["sizes"]["body"] = -1
        with self.assertRaises(Error):
            settings.validate_tokens(source)

    def test_reapply_uses_installed_native_refresh_wrapper(self):
        with patch("wuling.lifecycle.command") as native:
            lifecycle.apply_theme("wuling", preserve_background=True)
        native.assert_called_once_with(["omarchy", "theme", "refresh"])

    def test_preserve_comments_and_other_tables(self):
        old = '# my settings\nlabels = true # keep note\n[menu]\nselected = "edge"\n[terminal]\nsections = ["clock", "agent"]\n'
        new = settings.updated_text(old, "menu.selected", "fill")
        self.assertIn('# my settings\nlabels = true # keep note', new)
        self.assertEqual(settings.load(new)["terminal.sections"], ["clock", "agent"])
        self.assertEqual(settings.load(new)["menu.selected"], "fill")
        other = settings.updated_text(old, "sounds", "off")
        self.assertEqual(settings.load(other)["sounds"], "off")
        self.assertIn('[menu]\nselected = "edge"', other)

    def test_invalid_settings_never_write(self):
        for key, raw in (("labels", "maybe"), ("terminal.sections", '["clock","clock"]'),
                         ("sounds", "loud"), ("not_a_setting", "x")):
            with self.subTest(key=key), self.assertRaises(Error):
                lifecycle.set_config(key, raw)
        self.assertFalse(paths()["config"].exists())

    def test_theme_and_user_origins(self):
        resolved = theme.resolve("wuling-hud-paper", {"labels": False})
        self.assertEqual(resolved["geometry"]["bar_height"]["value"], 32)
        self.assertEqual(resolved["settings"]["menu.selected"]["value"], "fill")
        self.assertEqual(resolved["settings"]["labels"], {"value": False, "origin": "overrides.toml"})

    def test_external_palette_keeps_field_geometry(self):
        current = paths()["current"] / "theme"
        current.mkdir(parents=True)
        (current / "colors.toml").write_text('background = "#101010"\nforeground = "#EEEEEE"\naccent = "#ABCDEF"\n')
        resolved = theme.resolve("another-theme", {})
        self.assertEqual(resolved["preset"], "field")
        self.assertEqual(resolved["colors"]["fill"]["value"], "#ABCDEF")
        self.assertEqual(resolved["colors"]["line"]["value"], theme.mix("#EEEEEE", "#101010", .18))


class OwnershipTests(IsolatedHome):
    def test_font_backup_is_outside_discovery_and_still_rolls_back(self):
        fonts = self.home / ".local/share/fonts/wuling"
        fonts.mkdir(parents=True)
        (fonts / "face.ttf").write_bytes(b"old")
        source = self.home / "new-fonts"
        source.mkdir()
        (source / "face.ttf").write_bytes(b"new")
        with self.assertRaises(RuntimeError):
            with owned.Transaction() as tx:
                tx.replace(fonts, source=source, backup_root=paths()["state"] / "font-backups")
                self.assertEqual(list(fonts.parent.rglob("*.ttf")), [fonts / "face.ttf"])
                self.assertEqual((fonts / "face.ttf").read_bytes(), b"new")
                raise RuntimeError("injected activation failure")
        self.assertEqual((fonts / "face.ttf").read_bytes(), b"old")
        self.assertFalse(paths()["state"].exists())

    def test_exception_rolls_back_all_resources(self):
        file = self.home / "shared/file"
        file.parent.mkdir()
        file.write_text("original")
        try:
            with owned.Transaction() as tx:
                tx.replace(file, data="new")
                tx.replace(self.home / "added/deep/file", data="new")
                raise RuntimeError("injected")
        except RuntimeError:
            pass
        self.assertEqual(file.read_text(), "original")
        self.assertFalse((self.home / "added").exists())

    def test_interrupted_journal_recovers_before_next_operation(self):
        file = self.home / "file"
        file.write_text("old")
        tx = owned.Transaction()
        tx.__enter__()
        tx.replace(file, data="new")
        owned.recover()
        self.assertEqual(file.read_text(), "old")
        self.assertFalse(tx.path.exists())
        self.assertFalse(paths()["state"].exists())

    def test_failure_preserves_preexisting_empty_state_directory(self):
        paths()["state"].mkdir(parents=True)
        with self.assertRaises(RuntimeError):
            with owned.Transaction():
                raise RuntimeError("injected")
        self.assertTrue(paths()["state"].is_dir())

    def test_theme_member_insertion_removal_preserves_unrelated_bytes(self):
        originals = ['{ // personal\n "editor.fontSize":14,\n}\n', '{}\n', '{"other":{"nested":true}}']
        for original in originals:
            installed = theme_effects.replace_member(original, '\"Omarchy\"')
            self.assertEqual(theme_effects.replace_member(installed, None), original)
        original = '{"first":1, "workbench.colorTheme":"old", "last":2}'
        changed = theme_effects.replace_member(original, '\"new\"')
        self.assertEqual(theme_effects.replace_member(changed, '\"old\"'), original)
        self.assertEqual(json.loads(theme_effects.replace_member(changed, None)), {"first":1, "last":2})

    def test_recovery_preserves_concurrent_edit(self):
        file = self.home / "file"
        file.write_text("old")
        tx = owned.Transaction()
        tx.__enter__()
        tx.replace(file, data="new")
        file.write_text("user changed this")
        with self.assertRaises(Error):
            owned.recover()
        self.assertEqual(file.read_text(), "user changed this")
        self.assertTrue(tx.path.exists())

    def test_owned_block_preserves_surrounding_text_and_refuses_edits(self):
        before = '-- user binding\n'
        written = owned.block(before, "bindings", 'binding()\n')
        block = written[len(before):]
        with self.assertRaises(Error):
            owned.block(written.replace('binding()', 'edited()'), "bindings", 'next()\n', block)
        restored = owned.block(written + '-- another user line\n', "bindings", None, block)
        self.assertEqual(restored, before + '-- another user line\n')

    def test_jsonc_slot_preserves_comments_and_other_member_edits(self):
        before = '{ // personal\n "logo": {"source":"old"}, "modules": ["os"],\n}\n'
        written, record = jsonc.set_member(before, "logo", {"source": "new"})
        edited = written.replace('["os"]', '["os", "memory"]')
        restored = jsonc.remove_member(edited, record)
        self.assertEqual(restored, before.replace('["os"]', '["os", "memory"]'))
        with self.assertRaises(Error):
            jsonc.remove_member(written.replace('"new"', '"personal"'), record)

    def test_owned_block_restores_missing_final_newline(self):
        before = '-- original without newline'
        written = owned.block(before, "bindings", 'binding()\n')
        recorded = written[len(before):]
        updated = owned.block(written, "bindings", 'next()\n', recorded)
        self.assertEqual(owned.block(updated, "bindings", None, updated[len(before):]), before)

    def test_desktop_restores_only_its_values(self):
        original = {"keys": {"color-scheme": "'prefer-dark'", "gtk-theme": "'Personal'", "icon-theme": "'Original'"},
                    "dump": "original", "database": None, "mode": 0o600}
        current = {"keys": {"color-scheme": "'prefer-light'", "gtk-theme": "'Adwaita'", "icon-theme": "'UserChanged'"}}
        calls = []
        def native(argv):
            calls.append(argv)
            return "contains unrelated user changes" if argv[1] == "dump" else ""
        with patch("wuling.lifecycle.command", side_effect=native):
            lifecycle.restore_desktop(original, current)
        self.assertIn(["dconf", "write", "/org/gnome/desktop/interface/gtk-theme", "'Personal'"], calls)
        self.assertIn(["dconf", "write", "/org/gnome/desktop/interface/icon-theme", "'UserChanged'"], calls)


class InstallHome(IsolatedHome):
    def setUp(self):
        super().setUp()
        paths()["current"].mkdir(parents=True)
        (paths()["current"] / "theme.name").write_text("tokyo-night\n")
        (self.home / ".agents/skills").mkdir(parents=True)
        (self.home / ".config/Code/User").mkdir(parents=True)
        (self.home / ".config/Code/User/settings.json").write_text('{"workbench.colorTheme":"tokyo-night","editor.fontSize":14}\n')
        native = self.home / ".config/omarchy/shell.json"
        native.parent.mkdir(parents=True, exist_ok=True)
        native.write_text('{"bar":{"layout":{"left":[],"center":[],"right":[]}},"plugins":[]}\n')
        self.command_patch = patch("wuling.lifecycle.command", side_effect=self.fake_command)
        self.command_patch.start()
        self.euid_patch = patch("wuling.lifecycle.os.geteuid", return_value=1000)
        self.euid_patch.start()

    def tearDown(self):
        self.command_patch.stop()
        self.euid_patch.stop()
        super().tearDown()

    def fake_command(self, argv, **kwargs):
        if argv == ["omarchy", "version"]:
            return "4.0.6-1"
        if argv == ["hyprctl", "-j", "binds"]:
            return "[]"
        if argv[:3] == ["omarchy", "theme", "set"]:
            (paths()["current"] / "theme.name").write_text(argv[3] + "\n")
            path = self.home / ".config/Code/User/settings.json"
            path.write_text(theme_effects.replace_member(path.read_text(), json.dumps(argv[3])))
        return ""


class InstallTests(InstallHome):
    def test_repeated_install_remove_preserves_user_state(self):
        before = lifecycle.config_snapshot()
        lifecycle.install(True)
        lifecycle.install(True)
        self.assertFalse((self.home / ".claude").exists())
        self.assertTrue((self.home / ".agents/skills/wuling").is_symlink())
        lifecycle.uninstall(True)
        lifecycle.uninstall(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
        self.assertFalse((self.home / ".agents/skills/wuling").exists())
        self.assertFalse((self.home / ".local/bin/wuling").exists())

    def test_existing_name_conflict_leaves_everything_unchanged(self):
        theme_path = paths()["themes"] / "wuling"
        theme_path.mkdir(parents=True)
        (theme_path / "mine").write_text("user")
        before = lifecycle.config_snapshot()
        with self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
        self.assertFalse((paths()["data"] / "current").exists())
        self.assertEqual((theme_path / "mine").read_text(), "user")

    def test_repeated_menu_changes_leave_clean_owned_themes(self):
        lifecycle.install(True)
        for mode in ("fill", "edge", "fill"):
            lifecycle.set_config("menu.selected", mode)
            record = lifecycle.manifest()
            lifecycle.plan_install(record)
            for name in settings.tokens()["themes"]:
                self.assertFalse(list((paths()["themes"] / name).glob(".wuling-*")))
        lifecycle.install(True)
        self.assertEqual(settings.load()["menu.selected"], "fill")

    def test_optional_fastfetch_removes_only_its_entry(self):
        path = self.home / ".config/fastfetch/config.jsonc"
        path.parent.mkdir()
        original = '{ // keep my modules\n "modules": ["os"],\n}\n'
        path.write_text(original)
        lifecycle.install(True, True)
        path.write_text(path.read_text().replace('["os"]', '["os", "memory"]'))
        lifecycle.uninstall(True)
        self.assertEqual(path.read_text(), original.replace('["os"]', '["os", "memory"]'))

    def test_edited_theme_and_override_survive_removal(self):
        lifecycle.install(True)
        lifecycle.set_config("labels", "false")
        user_file = paths()["themes"] / "wuling" / "custom.txt"
        user_file.write_text("my theme edit")
        with self.assertRaises(Error):
            lifecycle.install(True)
        with self.assertRaises(Error):
            lifecycle.set_config("menu.selected", "fill")
        lifecycle.uninstall(True)
        self.assertEqual(user_file.read_text(), "my theme edit")
        self.assertFalse(settings.load()["labels"])

    def test_mid_install_failure_leaves_no_resources(self):
        before = lifecycle.config_snapshot()
        real_replace = owned.Transaction.replace
        calls = 0
        def failing(tx, *args, **kwargs):
            nonlocal calls
            real_replace(tx, *args, **kwargs)
            calls += 1
            if calls == 3:
                raise Error("injected copy failure")
        with patch.object(owned.Transaction, "replace", failing), self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
        self.assertFalse((paths()["data"] / "current").exists())
        self.assertFalse(paths()["state"].exists())

    def test_failing_theme_hook_restores_only_attributed_configuration(self):
        before = lifecycle.config_snapshot()
        original = self.fake_command
        def failing(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv == ["omarchy", "theme", "set", "wuling"]:
                (self.home / ".config/unattributed-hook-file").write_text("partial")
                raise Error("injected official hook failure")
            return result
        with patch("wuling.lifecycle.command", side_effect=failing), self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
        self.assertFalse((paths()["data"] / "current").exists())

    def test_concurrent_application_write_is_never_journalled_or_undone(self):
        from threading import Event, Thread
        import base64
        paused, release = Event(), Event()
        unrelated = self.home / ".config/unrelated-app/session.json"
        unrelated.parent.mkdir()
        unrelated.write_text("old draft")
        editor = self.home / ".config/Code/User/settings.json"
        sentinel = "independent private draft"
        errors = []
        original = self.fake_command
        def native(argv, **kwargs):
            if argv == ["omarchy", "theme", "set", "wuling"]:
                paused.set()
                if not release.wait(10):
                    raise RuntimeError("fixture barrier timed out")
            return original(argv, **kwargs)
        def install():
            try:
                lifecycle.install(True)
            except BaseException as exc:
                errors.append(exc)
        with patch("wuling.lifecycle.command", side_effect=native):
            worker = Thread(target=install)
            worker.start()
            try:
                self.assertTrue(paused.wait(10))
                journal = (paths()["state"] / "transaction.json").read_text()
                self.assertNotIn("unrelated-app", journal)
                self.assertNotIn("editor.fontSize", journal)
                unrelated.write_text(sentinel)
                editor.write_text(editor.read_text().replace('"editor.fontSize":14', '"editor.fontSize":17'))
            finally:
                release.set()
                worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        record = (paths()["state"] / "install.json").read_text()
        self.assertNotIn(sentinel, record)
        self.assertNotIn(base64.b64encode(sentinel.encode()).decode(), record)
        self.assertNotIn("unrelated-app", record)
        self.assertNotIn("editor.fontSize", record)
        lifecycle.uninstall(True)
        self.assertEqual(unrelated.read_text(), sentinel)
        self.assertEqual(json.loads(editor.read_text()), {"workbench.colorTheme":"tokyo-night", "editor.fontSize":17})

    def test_legacy_unscoped_records_cannot_restore_unrelated_paths(self):
        import base64
        path = self.home / ".config/unrelated.txt"
        path.write_text("new")
        changes = {"unrelated.txt": {"before": {"data":base64.b64encode(b"old").decode(),"mode":0o644},
                                    "after": {"data":base64.b64encode(b"new").decode(),"mode":0o644}}}
        with owned.Transaction() as tx:
            lifecycle.restore_effects(tx, changes, {})
        self.assertEqual(path.read_text(), "new")


class UsageTests(unittest.TestCase):
    def test_all_parser_errors_are_json(self):
        import subprocess
        for args in (["unknown"], [], ["theme","bad"], ["status","--bad"], ["theme","resolve","--theme"]):
            with self.subTest(args=args):
                result = subprocess.run([str(ROOT / "bin/wuling"), *args],capture_output=True,text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                value = json.loads(result.stdout)
                self.assertEqual(value["schema_version"], 1)
                self.assertEqual(value["error"]["code"], "wuling_error")


if __name__ == "__main__":
    unittest.main()
