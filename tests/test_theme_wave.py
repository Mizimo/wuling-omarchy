"""Unknown or edited native internals disable only the optional wave."""
import hashlib
import json
import os
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import settings, theme_wave


class ThemeWaveTests(IsolatedHome):
    def test_content_gate_and_incomplete_installation(self):
        root = self.home / "wuling"
        native = self.home / "native"
        target = root / "plugins/session/native-theme.json"
        target.parent.mkdir(parents=True)
        source = native / "bin/omarchy-theme-set"
        source.parent.mkdir(parents=True)
        source.write_text("fixture early staging contract\n")
        target.write_text(json.dumps({"contracts": {"tested": {"files": {"bin/omarchy-theme-set": hashlib.sha256(source.read_bytes()).hexdigest()}, "background_ms":420, "scaled_duration":False, "settle_ms":67}}}))
        with patch.object(theme_wave, "ROOT", root), patch.dict(os.environ, {"OMARCHY_PATH": str(native)}):
            gate = theme_wave.compatibility()
            self.assertEqual(gate["contract"], "tested")
            self.assertEqual(gate["recheck"], {str(source): hashlib.md5(source.read_bytes()).hexdigest()})
            source.write_text("different staging order\n")
            self.assertFalse(theme_wave.compatibility()["ok"])
            source.unlink()
            self.assertFalse(theme_wave.compatibility()["ok"])
            target.unlink()
            self.assertFalse(theme_wave.compatibility()["ok"])

    def test_theme_switch_is_an_independent_boolean(self):
        self.assertTrue(settings.tokens()["defaults"]["session.theme"])
        self.assertIs(settings.parse_value("session.theme", "false"), False)
        values = settings.load(settings.updated_text('session.arrival=true\nsession.exit=false\n', 'session.theme', False))
        self.assertEqual(values, {"session.arrival":True, "session.exit":False, "session.theme":False})
