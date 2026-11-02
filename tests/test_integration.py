"""Native settings and key ownership survive independent user changes."""
import json
from unittest.mock import patch
from test_foundations import InstallHome
from wuling import Error, paths
from wuling import integration, lifecycle


class IntegrationTests(InstallHome):
    def test_native_lua_binding_allows_update_but_duplicate_does_not(self):
        lifecycle.install(True)
        real = self.fake_command
        binding = {"modmask":68,"key":"G","dispatcher":"__lua","arg":"9","description":"Field Terminal"}
        count = 1
        def native(argv):
            if argv == ["hyprctl", "-j", "binds"]:
                return json.dumps([binding] * count)
            return real(argv)
        with patch("wuling.lifecycle.command", side_effect=native):
            lifecycle.install(True)
            before = lifecycle.config_snapshot()
            count = 2
            with self.assertRaises(Error):
                lifecycle.install(True)
            self.assertEqual(lifecycle.config_snapshot(), before)

    def test_existing_effective_key_is_refused_before_writes(self):
        before = lifecycle.config_snapshot()
        real = self.fake_command
        def native(argv):
            if argv == ["hyprctl", "-j", "binds"]:
                return '[{"modmask":68,"key":"G","arg":"custom-command"}]'
            return real(argv)
        with patch("wuling.lifecycle.command", side_effect=native), self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
        self.assertFalse((paths()["data"] / "current").exists())

    def test_update_preserves_disabled_plugin_and_removal_keeps_native_edits(self):
        lifecycle.install(True)
        shell, bindings = integration.locations()
        data = json.loads(shell.read_text())
        data["bar"]["position"] = "bottom"
        data["bar"].pop("id")
        data["plugins"] = []
        data["bar"]["layout"]["right"] = []
        shell.write_text(json.dumps(data))
        bindings.write_text('-- personal note\n' + bindings.read_text())
        lifecycle.install(True)
        self.assertEqual(json.loads(shell.read_text()), data)
        lifecycle.uninstall(True)
        self.assertEqual(json.loads(shell.read_text()), data)
        self.assertEqual(bindings.read_text(), '-- personal note\n')

    def test_removal_preserves_edited_owned_block_and_widget_settings(self):
        lifecycle.install(True)
        shell, bindings = integration.locations()
        data = json.loads(shell.read_text())
        data["bar"]["layout"]["right"][0]["custom"] = True
        shell.write_text(json.dumps(data))
        changed = bindings.read_text().replace('Field Terminal', 'My panel')
        bindings.write_text(changed)
        lifecycle.uninstall(True)
        result = json.loads(shell.read_text())
        self.assertEqual(result["bar"]["layout"]["right"], [{"id":"wuling.terminal","custom":True}])
        self.assertNotIn("id", result["bar"])
        self.assertEqual(bindings.read_text(), changed)

    def test_changed_owned_block_refuses_update(self):
        lifecycle.install(True)
        shell, bindings = integration.locations()
        bindings.write_text(bindings.read_text().replace('Field Terminal', 'My panel'))
        before = lifecycle.config_snapshot()
        with self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(lifecycle.config_snapshot(), before)
