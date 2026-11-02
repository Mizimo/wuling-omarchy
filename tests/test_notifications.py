"""Persistent notification data stays bounded, private, and message-only."""
from pathlib import Path
import json
import os
import stat
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, notifications


class NotificationStateTests(IsolatedHome):
    def test_first_dnd_uses_compatible_native_state_without_writing_it(self):
        for version, relative in (("4.0.6", "notifications.json"), ("4.5.0-rc2", "notifications/quiet.json")):
            with self.subTest(version=version):
                native = self.home / ".local/state/omarchy" / relative
                native.parent.mkdir(parents=True, exist_ok=True)
                native.write_text('{"version":3,"dnd":true}\n')
                before = native.read_bytes()
                gate = {"ok":True, "version":version}
                self.assertTrue(notifications.read(gate)["dnd"])
                self.assertFalse(notifications.read({"ok":False})["dnd"])
                notifications.write({"schema_version":1,"dnd":False,"live":[],"history":[]})
                self.assertFalse(notifications.read(gate)["dnd"])
                self.assertEqual(native.read_bytes(), before)
                notifications.filename().unlink()

    def state(self, rows):
        return {"schema_version":1,"dnd":False,"live":rows,"history":rows}

    def test_codes_in_markup_and_metadata_never_reach_disk(self):
        row = {"key":"test", "summary":"Verification code", "body":"<b>123456</b>",
               "execArgv":'["echo","123456"]', "app":"sender-123456", "image":"secret-file",
               "closed_ts":1000, "ts":1000}
        with patch("wuling.notifications.time.time", return_value=1000):
            notifications.write(self.state([row]))
        content = notifications.filename().read_text()
        self.assertNotIn("123456", content)
        self.assertNotIn("secret-file", content)
        self.assertIn("Verification notification", content)
        self.assertEqual(stat.S_IMODE(notifications.filename().stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(notifications.filename().parent.stat().st_mode), 0o700)

    def test_history_retention_and_limit_and_no_images_or_links(self):
        rows = [{"key":f"r-{i}","summary":"hello","closed_ts":100000-i,"image":"private","link":"private"} for i in range(150)]
        result = notifications.normalise(self.state(rows), now=100000)
        self.assertEqual(len(result["history"]),100)
        self.assertFalse(any("image" in r or "link" in r for r in result["history"]))
        self.assertEqual(notifications.normalise(self.state(rows),now=200000)["history"], [])

    def test_write_and_read_refuse_symlink(self):
        target = self.home / "personal"
        target.write_text("keep")
        notifications.filename().parent.mkdir(parents=True)
        notifications.filename().symlink_to(target)
        with self.assertRaises(Error): notifications.write(self.state([]))
        with self.assertRaises(Error): notifications.read()
        self.assertEqual(target.read_text(),"keep")

    def test_payload_size_is_bounded_before_disk(self):
        row={"key":"long","summary":"title"*1000,"body":"文"*100000,"closed_ts":100000}
        result=notifications.normalise(self.state([row]),now=100000)
        self.assertLessEqual(len(json.dumps(result["history"][0],ensure_ascii=False).encode()),4096)
        self.assertLessEqual(len(json.dumps(result["live"][0],ensure_ascii=False).encode()),16384)

    def test_removal_deletes_messages_but_never_follows_symlink(self):
        notifications.write(self.state([]))
        notifications.cleanup_state()
        self.assertFalse(notifications.filename().exists())
        target=self.home / "personal"
        target.write_text("keep")
        notifications.filename().parent.mkdir(parents=True, exist_ok=True)
        notifications.filename().symlink_to(target)
        notifications.cleanup_state(installed=True)
        self.assertFalse(notifications.filename().is_symlink())
        self.assertEqual(target.read_text(), "keep")
