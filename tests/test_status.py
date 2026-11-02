"""Terminal consumes native state without duplicating collectors or actions."""

from pathlib import Path
from concurrent.futures import Future
import json
import tempfile
import unittest
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, paths
from wuling import actions, status


class StatusTests(IsolatedHome):
    def test_agent_projection_omits_accounts_and_expired_limits(self):
        folder = paths()["state"].parent / "omarchy/agents/usage"
        folder.mkdir(parents=True)
        (folder / "example.json").write_text(json.dumps({"id": "example", "name": "Example", "tierLabel": "Pro",
            "account": "must-not-escape", "authHelpText": "private", "limits": [
                {"label": "session", "percent": .8, "resetsAt": "2000-01-01T00:00:00Z"},
                {"label": "week", "percent": .4, "resetsAt": "2099-01-01T00:00:00Z"},
                {"label": "unknown", "percent": -1}]}))
        (folder / "bad.json").write_text('{"partial":')
        (folder / "empty.json").write_text('{"id":"empty","ready":true}')
        result = status.agent_usage()
        self.assertEqual(len(result), 1)
        self.assertEqual([x["fraction"] for x in result[0]["limits"]], [0, .4])
        self.assertNotIn("private", json.dumps(result))
        self.assertNotIn("must-not-escape", json.dumps(result))
        config = paths()["home"] / ".config/omarchy/shell.json"
        config.parent.mkdir(parents=True)
        config.write_text('{"bar":{"layout":{"right":[{"id":"omarchy.agents","providers":{"example":{"enabled":false}}}]}}}')
        self.assertEqual(status.agent_usage(), [])

    def test_telemetry_measures_delta_and_bounds_history(self):
        proc, sys = self.home / "proc", self.home / "sys"
        proc.mkdir()
        sensor = sys / "class/hwmon/hwmon0"
        sensor.mkdir(parents=True)
        (sensor / "name").write_text("coretemp\n")
        (sensor / "temp1_input").write_text("42000\n")
        (proc / "stat").write_text("cpu 10 0 10 80 0 0 0 0 0 0\n")
        (proc / "meminfo").write_text("MemTotal: 1000 kB\nMemAvailable: 400 kB\n")
        with patch.object(status, "PROC", proc), patch.object(status, "SYS", sys):
            sampler = status.Telemetry()
            self.assertIsNone(sampler.read()["cpu_percent"])
            (proc / "stat").write_text("cpu 20 0 20 100 0 0 0 0 0 0\n")
            result = sampler.read()
            self.assertEqual(result["cpu_percent"], 50)
            self.assertEqual(result["memory_used"], 600 * 1024)
            self.assertEqual(result["temperature_c"], 42)
            for _ in range(100):
                sampler.read()
            self.assertEqual(len(sampler.history["cpu"]), 40)

    def test_media_follows_native_selection_and_hides_paused(self):
        native = {"hasPlayer": True, "playing": True, "identity": "Example", "title": "Track",
                  "artist": "Artist", "artUrl": "private-path", "canGoNext": True}
        with patch.object(status, "probe_json", return_value=native) as probe:
            result = status.media()
            probe.assert_called_once_with(["omarchy-shell", "media", "status"])
        self.assertEqual(result["title"], "Track")
        self.assertTrue(result["can_next"])
        self.assertNotIn("private-path", json.dumps(result))
        with patch.object(status, "probe_json", return_value={**native, "playing": False}):
            self.assertIsNone(status.media())

    def test_disabled_sections_do_not_probe(self):
        with patch.object(status, "probe", side_effect=AssertionError("unexpected probe")):
            collector = status.Collector(["comms"])
            try:
                result = collector.read(wait=True)
                self.assertNotIn("clock", result)
                self.assertNotIn("agent", result)
                self.assertNotIn("telemetry", result)
                self.assertEqual(result["comms"], {"available": False, "items": []})
            finally:
                collector.close()

    def test_busy_source_has_one_future_and_does_not_block_frame(self):
        collector = status.Collector(["agent"])
        future = Future()
        with patch.object(collector.pool, "submit", return_value=future) as submit:
            for _ in range(10):
                self.assertEqual(collector.read()["pending"], ["agent"])
            submit.assert_called_once()
            future.set_result([])
            self.assertEqual(collector.read()["agent"], [])
            collector.read()
            submit.assert_called_once()
        collector.close()


class ActionTests(unittest.TestCase):
    def test_rejects_shell_text_and_unexpected_arguments(self):
        for name, value in (("volume", "1;echo bad"), ("brightness", "$(bad)"), ("volume", "101"),
                            ("panel", "other"), ("dnd", "off"), ("lock", "extra")):
            with self.subTest(name=name, value=value), self.assertRaises(Error):
                actions.plan(name, value)

    def test_absolute_volume_uses_native_dsp_resolution_and_osd(self):
        with patch.object(status, "volume", return_value={"percent": 30, "muted": False}):
            self.assertEqual(actions.plan("volume", "70"), ["omarchy-audio-output-volume", "+40"])
        self.assertEqual(actions.plan("brightness", "-5"), ["omarchy-brightness-display", "5%-"])
        self.assertEqual(actions.plan("brightness", "40"), ["omarchy-brightness-display", "40%"])
        self.assertEqual(actions.plan("power-menu"), ["omarchy-menu", "toggle", "system"])

    def test_native_rejection_is_not_reported_as_success(self):
        with patch.object(actions, "command", return_value="unhandled"), self.assertRaises(Error):
            actions.run("next")
