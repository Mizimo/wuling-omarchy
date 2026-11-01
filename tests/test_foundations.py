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
from wuling import jsonc, lifecycle, owned, settings, theme


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


class InstallTests(IsolatedHome):
    def setUp(self):
        super().setUp()
        paths()["current"].mkdir(parents=True)
        (paths()["current"] / "theme.name").write_text("tokyo-night\n")
        (self.home / ".agents/skills").mkdir(parents=True)
        (self.home / ".config/example").mkdir(parents=True)
        (self.home / ".config/example/theme").write_text("tokyo-night\n")
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
        if argv[:3] == ["omarchy", "theme", "set"]:
            (paths()["current"] / "theme.name").write_text(argv[3] + "\n")
            (self.home / ".config/example/theme").write_text(argv[3] + "\n")
        return ""

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

    def test_failing_theme_hook_restores_configuration(self):
        before = lifecycle.config_snapshot()
        original = self.fake_command
        def failing(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv == ["omarchy", "theme", "set", "wuling"]:
                (self.home / ".config/example/created-by-hook").write_text("partial")
                raise Error("injected official hook failure")
            return result
        with patch("wuling.lifecycle.command", side_effect=failing), self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
        self.assertFalse((paths()["data"] / "current").exists())


if __name__ == "__main__":
    unittest.main()
