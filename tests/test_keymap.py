"""Native key list parsing preserves opaque user descriptions and alternatives."""
import re
import unittest
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, keymap


class KeymapTests(IsolatedHome):
    def test_native_rows_preserve_every_alternative_and_unknown_description(self):
        rows = keymap.parse("SUPER + W / SUPER + Q → Close window\nSUPER CTRL ALT + F9 → Field specimen → $(example)\nXF86AudioMute → Mute audio\n")
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["keys"], [["SUPER", "W"], ["SUPER", "Q"]])
        self.assertEqual(rows[1]["description"], "Field specimen → $(example)")
        self.assertEqual(rows[1]["group"], "OTHER")
        self.assertEqual(rows[2]["keys"], [["XF86AudioMute"]])

    def test_localized_description_uses_catalog_only_for_grouping(self):
        rows = keymap.parse("SUPER + 2 → Fixture 2", [(re.compile(r"^Fixture [0-9]+$"), "Switch to workspace %1")])
        self.assertEqual(rows[0]["group"], "NAVIGATE")
        self.assertEqual(rows[0]["description"], "Fixture 2")

    def test_changed_or_missing_source_is_an_error_not_an_empty_success(self):
        for response in (None, "", '{"new":"format"}', "SUPER + K\t→ Keybindings", "SUPER + K → "):
            with self.subTest(response=response), patch.object(keymap.status, "probe", return_value=response), self.assertRaises(Error):
                keymap.snapshot()

    def test_supplement_only_missing_chords_keeps_unknown_lua_opaque(self):
        def binding(key, description="", mask=0, code=0):
            return f"bindd\n\tmodmask: {mask}\n\tkey: {key}\n\tkeycode: {code}\n\tdescription: {description}\n\tdispatcher: __lua\n\targ: 123\n\n"
        rows = keymap.parse("SUPER CTRL + SLASH → Keymap\nSUPER + W / SUPER + Q → Close window")
        raw = (binding("SUPER CTRL + code:61", "Keymap", 68)
               + binding("Q", "Close window", 64)
               + binding("", "Agent", 0, 201)
               + binding("Z", mask=76)
               + binding("code:999", mask=1)
               + binding("switch:on:Lid Switch"))
        out = keymap.supplement(rows, raw, {"61": "SLASH", "201": "F23"})
        self.assertEqual(len(out), 5)
        self.assertEqual([r["keys"] for r in out[2:]], [[["code:201"]], [["SUPER", "CTRL", "ALT", "Z"]], [["SHIFT", "code:999"]]])
        self.assertTrue(all(r["group"] == "OTHER" for r in out[2:]))
        self.assertEqual(out[3]["description_key"], "lua-undescribed")
        self.assertNotIn("123", str(out))

    def test_description_containing_binding_does_not_split_a_record(self):
        raw = "bindd\n\tmodmask: 0\n\tkey: Z\n\tkeycode: 0\n\tdescription: My binding → note\n\tdispatcher: __lua\n"
        self.assertEqual(keymap.supplement([], raw, {})[0]["description"], "My binding → note")
        for broken in ("", "[]", "bind\n\tkey: X\n", raw.replace("modmask: 0", "modmask: what")):
            with self.subTest(broken=broken), self.assertRaises(Error):
                keymap.supplement([], broken, {})


if __name__ == "__main__":
    unittest.main()
