"""Persistent notification data stays bounded, private, and message-only."""
from pathlib import Path
import json
import os
import stat
import subprocess
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, ROOT, notifications


class NotificationStateTests(IsolatedHome):
    def test_writer_ack_coalescing_recovery_and_finite_budget(self):
        code = (ROOT / "plugins/notifications/WriterState.js").read_text().replace('.pragma library', '')
        subprocess.run(["node", "-e", code + r'''
const assert=require('assert'), ok=JSON.stringify({schema_version:1,ok:true});
const s=create();enqueue(s,'old');assert.equal(send(s),'old');
enqueue(s,'new');assert.equal(send(s),'');assert(acknowledge(s,ok));
assert.equal(s.latest,'new');assert.equal(send(s),'new');
for(const reply of ['garbage','{}','null','{"schema_version":1,"ok":false}','{"schema_version":1,"ok":"true"}']) {
    assert(!acknowledge(s,reply));assert.equal(s.latest,'new');
}
assert.equal(failed(s,10000,'exit'),1000);assert.equal(send(s),'new');
assert(acknowledge(s,ok));assert.equal(s.latest,'');
enqueue(s,'after-recovery');assert.equal(send(s),'after-recovery');
assert.equal(failed(s,12000,'exit'),5000);assert.equal(send(s),'after-recovery');
assert.equal(failed(s,18000,'exit'),30000);assert.equal(send(s),'after-recovery');
assert.equal(failed(s,49000,'exit'),0);assert(s.halted);
enqueue(s,'latest-while-stopped');assert.equal(s.latest,'latest-while-stopped');assert.equal(send(s),'');
const t=create();assert.equal(failed(t,10000,'exit'),1000);
assert.equal(failed(t,610000,'exit'),1000);assert.equal(t.attempts,1);
assert(!acknowledge(t,ok));
'''], check=True)

    def test_writer_health_requires_enabled_provider_reply(self):
        with patch("wuling.dispatch.enabled", return_value=True), patch.object(notifications, "probe", return_value="ok"):
            self.assertFalse(notifications.writer_health()["ok"])
        with patch("wuling.dispatch.enabled", return_value=False), patch.object(notifications, "probe") as probe:
            self.assertTrue(notifications.writer_health()["ok"])
            probe.assert_not_called()
        health={"schema_version":1,"ok":False,"stopped":True,"reason":"Notification writer exited (code 9)"}
        with patch("wuling.dispatch.enabled", return_value=True), patch.object(notifications, "probe", return_value=json.dumps(health)):
            self.assertEqual(notifications.writer_health()["reason"],health["reason"])

    def test_writer_warning_claim_survives_shell_restart_but_not_new_session(self):
        directory=self.home / "runtime";directory.mkdir()
        with patch("wuling.session.runtime", return_value=directory), patch.dict(os.environ, {"HYPRLAND_INSTANCE_SIGNATURE":"fixture-session-one"}):
            self.assertTrue(notifications.claim_warning()["claimed"])
            self.assertFalse(notifications.claim_warning()["claimed"])
        with patch("wuling.session.runtime", return_value=directory), patch.dict(os.environ, {"HYPRLAND_INSTANCE_SIGNATURE":"fixture-session-two"}):
            self.assertTrue(notifications.claim_warning()["claimed"])
        self.assertEqual(len(list(directory.iterdir())),1)

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
