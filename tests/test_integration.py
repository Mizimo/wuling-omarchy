"""Native settings and key ownership survive independent user changes."""
import json
import io
from contextlib import redirect_stdout
from unittest.mock import patch
from test_foundations import InstallHome
from wuling import Error, paths
from wuling import integration, lifecycle


class IntegrationTests(InstallHome):
    def test_arrival_rule_upgrade_and_removal_preserve_surrounding_hyprland_config(self):
        _, bindings = integration.locations()
        bindings.parent.mkdir(parents=True, exist_ok=True)
        bindings.write_text('-- personal before\n')
        legacy = '\n'.join(line for line in integration.BINDING.splitlines() if 'layer_rule' not in line) + '\n'
        with patch.object(integration, "BINDING", legacy):
            lifecycle.install(True)
        bindings.write_text(bindings.read_text() + '-- personal after\n')
        lifecycle.install(True)
        self.assertEqual(bindings.read_text().count('^wuling-session-arrival$'), 1)
        lifecycle.install(True)
        lifecycle.uninstall(True)
        self.assertEqual(bindings.read_text(), '-- personal before\n-- personal after\n')

    def test_untested_version_requires_normal_consent_and_preserves_update_choices(self):
        original = self.fake_command
        def untested(argv, **kwargs):
            return "4.5.0rc3-1" if argv == ["omarchy", "version"] else original(argv, **kwargs)
        with patch("wuling.lifecycle.command", side_effect=untested), redirect_stdout(io.StringIO()) as output:
            with patch("builtins.input", return_value="n"), self.assertRaises(Error):
                lifecycle.install(False, False)
            self.assertIsNone(lifecycle.manifest())
            self.assertIn("has not been tested", output.getvalue())
            self.assertIn("4.0.6, 4.5.0-rc2", output.getvalue())
            self.assertIn("may remain native", output.getvalue())
            lifecycle.install(True)
            shell, _ = integration.locations()
            data = json.loads(shell.read_text())
            data.setdefault("disabledPlugins", []).append("wuling.sound")
            shell.write_text(json.dumps(data))
            lifecycle.set_config("labels", "false")
            before = (self.home / ".config/wuling/overrides.toml").read_bytes()
            lifecycle.install(True)
            self.assertEqual(json.loads(shell.read_text()), data)
            self.assertEqual((self.home / ".config/wuling/overrides.toml").read_bytes(), before)
            self.assertFalse(lifecycle.manifest()["compatibility"]["tested"])

    def test_active_other_replacement_is_refused_without_changes(self):
        shell, _ = integration.locations()
        other = self.home / ".config/omarchy/plugins/fixture.osd"
        other.mkdir(parents=True)
        (other / "manifest.json").write_text(json.dumps({"id":"fixture.osd","omarchy":{"clonedFrom":"omarchy.osd"}}))
        data = json.loads(shell.read_text())
        data["plugins"] = [{"id":"fixture.osd"}]
        shell.write_text(json.dumps(data))
        before = shell.read_text()
        with self.assertRaises(Error):
            lifecycle.install(True)
        self.assertEqual(shell.read_text(), before)
        self.assertIsNone(lifecycle.manifest())

    def test_edited_clone_entry_is_preserved_but_disabled_on_removal(self):
        lifecycle.install(True)
        shell, _ = integration.locations()
        data = json.loads(shell.read_text())
        entry = next(row for row in data["plugins"] if integration.identity(row)=="wuling.osd")
        entry["custom"] = "keep"
        shell.write_text(json.dumps(data))
        lifecycle.uninstall(True)
        result = json.loads(shell.read_text())
        self.assertIn(entry, result["plugins"])
        self.assertIn("wuling.osd", result["disabledPlugins"])
        self.assertNotIn("omarchy.osd", result["disabledPlugins"])

    def test_missing_native_module_leaves_native_notifications_enabled(self):
        with patch("wuling.notifications.compatibility", return_value={"ok":False,"reason":"Missing fixture module"}):
            lifecycle.install(True)
        shell, _ = integration.locations()
        data = json.loads(shell.read_text())
        self.assertNotIn("wuling.notifications", [integration.identity(r) for r in data.get("plugins",[])])
        self.assertNotIn("omarchy.notifications", data.get("disabledPlugins",[]))
        self.assertIn("wuling.notifications", lifecycle.manifest()["integration"]["unavailable"])

    def test_clone_restores_native_but_keeps_an_original_disable(self):
        shell, _ = integration.locations()
        original = json.loads(shell.read_text())
        original["disabledPlugins"] = ["omarchy.osd"]
        shell.write_text(json.dumps(original))
        lifecycle.install(True)
        installed = json.loads(shell.read_text())
        self.assertIn({"id": "wuling.osd"}, installed["plugins"])
        self.assertNotIn("wuling.osd", installed.get("cloneSourceRestores", []))
        lifecycle.uninstall(True)
        self.assertEqual(json.loads(shell.read_text()), original)

    def test_upgrade_adds_new_clone_once_and_preserves_intervening_user_edit(self):
        sources = integration.installed_sources()
        old_sources = [p for p in sources if p.parent.name in ("bar", "terminal")]
        with patch("wuling.integration.installed_sources", return_value=old_sources):
            lifecycle.install(True)
        shell, _ = integration.locations()
        data = json.loads(shell.read_text())
        data["personal"] = "keep this edit"
        shell.write_text(json.dumps(data))
        lifecycle.install(True)
        result = json.loads(shell.read_text())
        self.assertEqual(sum(integration.identity(row) == "wuling.osd" for row in result["plugins"]), 1)
        lifecycle.install(True)
        self.assertEqual(json.loads(shell.read_text()), result)
        lifecycle.uninstall(True)
        result = json.loads(shell.read_text())
        self.assertEqual(result["personal"], "keep this edit")
        self.assertNotIn("omarchy.osd", result.get("disabledPlugins", []))

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

    def test_existing_dispatch_key_is_refused_before_writes(self):
        before = lifecycle.config_snapshot()
        real = self.fake_command
        def native(argv):
            if argv == ["hyprctl", "-j", "binds"]:
                return '[{"modmask":64,"key":"D","arg":"custom-command"}]'
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
        # Match native clone-disable: it also consumes the restoration flags.
        data.pop("cloneSourceRestores", None)
        data.pop("disabledPlugins", None)
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
