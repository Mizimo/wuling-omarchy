"""Installation metadata and Config failure boundaries without a desktop."""
from pathlib import Path
import json
import os
import subprocess
import shutil
import unittest
import wave
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, configuration, lifecycle, paths, settings, theme


class ConfigurationTests(IsolatedHome):
    def test_music_rejects_missing_non_audio_and_fifo_without_changing_old_value(self):
        audio = self.home / "fixture.wav"
        with wave.open(str(audio), "wb") as stream:
            stream.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            stream.writeframes(b"\0\0" * 80)
        lifecycle.set_config("login_music", str(audio))
        path = paths()["config"] / "overrides.toml"
        before = path.read_bytes()
        ordinary = self.home / "text.wav"
        ordinary.write_text("Not audio")
        fifo = self.home / "pipe.wav"
        os.mkfifo(fifo)
        for invalid in (self.home / "missing", ordinary, fifo, self.home, Path("relative.wav")):
            with self.subTest(path=invalid), self.assertRaises(settings.InvalidMusic):
                lifecycle.set_config("login_music", str(invalid))
            self.assertEqual(path.read_bytes(), before)
        audio.unlink()
        # Runtime reads and unrelated edits survive an old file disappearing.
        self.assertEqual(theme.resolve()["settings"]["login_music"]["value"], str(audio))
        lifecycle.set_config("labels", "false")
        lifecycle.set_config("login_music", "")
        self.assertEqual(settings.load()["login_music"], "")

    def test_native_entry_uses_menu_content_and_never_a_supplied_command(self):
        source = self.home / "native/default/omarchy"
        source.mkdir(parents=True)
        menu = source / "omarchy-menu.jsonc"
        with patch.dict(os.environ, {"OMARCHY_PATH": str(self.home / "native")}):
            for prefix in ("style", "appearance"):
                menu.write_text(json.dumps({prefix+".font": {"provider": "fonts"}}))
                self.assertEqual(configuration.native("font"), ["omarchy-menu", "summon", prefix+".font"])
            with self.assertRaises(Error):
                configuration.native("theme")
            with self.assertRaises(Error):
                configuration.native("font; arbitrary-command")
        with self.assertRaises(Error):
            configuration.native("input")
        input_file = self.home / ".config/hypr/input.lua"
        input_file.parent.mkdir(parents=True)
        input_file.write_text("-- fixture\n")
        self.assertEqual(configuration.native("input"), ["omarchy-launch-config-editor", str(input_file)])

    def test_payload_records_git_archive_and_unversioned_sources(self):
        source = self.home / "checkout"
        source.mkdir()
        (source / "LICENSE").write_text("Fixture license\n")
        def payload(name):
            destination = self.home / name
            with patch.object(lifecycle, "ROOT", source), patch.object(lifecycle, "PAYLOAD", ()):
                lifecycle.prepare_payload(destination)
            return json.loads((destination / "release.json").read_text())
        self.assertEqual(payload("plain"), {"version": "unreleased", "commit": "", "date": ""})
        release = {"version": "fixture", "commit": "a"*40, "date": "2026-01-01"}
        (source / "release.json").write_text(json.dumps(release))
        self.assertEqual(payload("archive"), release)
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "add", "LICENSE"], check=True)
        subprocess.run(["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "Fixture"], check=True)
        commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        data = payload("git")
        self.assertEqual(data["commit"], commit)
        self.assertEqual(data["version"], "unreleased")
        self.assertRegex(data["date"], r"^\d{4}-\d{2}-\d{2}$")
        subprocess.run(["git", "-C", str(source), "tag", "fixture-tag"], check=True)
        self.assertEqual(payload("tagged")["version"], "fixture-tag")
        (source / "release.json").write_text('{"version": null, "commit": {}}')
        # Invalid field types cannot become visible strings such as "None".
        shutil.rmtree(source / ".git")
        self.assertEqual(payload("malformed-fields"), {"version": "unreleased", "commit": "", "date": ""})


if __name__ == "__main__":
    unittest.main()
