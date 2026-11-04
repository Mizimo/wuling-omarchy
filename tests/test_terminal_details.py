"""View lifecycle, history safety and multiple battery packs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, ROOT, paths
from wuling import actions, devices, notifications, spectrum, status


class DetailDataTests(IsolatedHome):
    def test_media_times_require_a_unique_complete_native_match(self):
        native = {"hasPlayer": True, "playing": True, "identity": "Example", "desktopEntry": "example",
                  "title": "Track", "artist": "Artist", "album": "Album", "artUrl": ""}
        root = {"Identity": "Example", "DesktopEntry": "example"}
        player = {"PlaybackStatus": "Playing", "Position": 12000000, "Metadata": {
            key: {"data": value} for key, value in {"xesam:title": "Track", "xesam:artist": ["Artist"],
                "xesam:album": "Album", "mpris:length": 180000000}.items()}}
        names = ["org.mpris.MediaPlayer2.one", "org.mpris.MediaPlayer2.two"]
        roots = {names[0]: root, names[1]: {"Identity": "Other"}}
        def properties(bus, name, path, interface):
            return roots[name] if interface == "org.mpris.MediaPlayer2" else player
        with patch.object(devices, "call", return_value=[names]), patch.object(devices, "properties", side_effect=properties):
            self.assertEqual(devices.media_times(native), {"length": 180, "position": 12})
            roots[names[1]] = root
            self.assertEqual(devices.media_times(native), {"length": None, "position": None})
            roots[names[1]] = {}
            self.assertEqual(devices.media_times(native), {"length": None, "position": None})
            roots[names[1]] = {"Identity": "Other"}
            self.assertEqual(devices.media_times({**native, "title": "Next track"}), {"length": None, "position": None})
            player["Position"] = -1
            self.assertIsNone(devices.media_times(native)["position"])
        with patch.object(devices, "call") as call:
            self.assertEqual(devices.media_times({**native, "playing": False}), {"length": None, "position": None})
            self.assertEqual(devices.media_times({}), {"length": None, "position": None})
            call.assert_not_called()

    def test_packs_are_independent_and_empty_capacity_is_not_zero_percent(self):
        prefix = "/org/freedesktop/UPower/devices/"
        data = {
            prefix + "battery_BAT0": {"Type": 2, "PowerSupply": True, "IsPresent": True, "EnergyFull": 50, "Percentage": 78, "State": 1, "NativePath": "/sys/BAT0"},
            prefix + "battery_BAT1": {"Type": 2, "PowerSupply": True, "IsPresent": True, "EnergyFull": 0, "Percentage": 0, "State": 2},
            prefix + "battery_BAT2": {"Type": 2, "PowerSupply": True, "IsPresent": True, "EnergyFull": 20, "Percentage": 8, "State": 2},
            prefix + "mouse": {"Type": 2, "PowerSupply": False, "EnergyFull": 1},
        }
        with patch.object(devices, "call", return_value=[list(data)+[None, "invalid"]]), patch.object(devices, "properties", side_effect=lambda bus, service, path, interface: data[path]):
            rows = devices.battery_rows()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["name"], "BAT0")
        self.assertEqual(rows[0]["state"], "charging")
        self.assertEqual(rows[1]["state"], "absent")
        self.assertIsNone(rows[1]["percent"])
        self.assertEqual(rows[2]["percent"], 8)
        with patch.object(devices, "call", return_value=[]):
            self.assertEqual(devices.battery_rows(), [])

    def test_comms_projects_retained_plain_body_and_contract_actions(self):
        now = time.time()
        rows = [{"key":"first", "app":"Example", "summary":"<b>Earlier</b>", "body":"First<br>Second &amp; third",
                 "ts":now-2,"closed_ts":now,"execArgv":'["true"]',"execActions":'[{"label":"View","argv":["true"]}]'},
                {"key":"second", "app":"Example", "summary":"Latest", "body":"Details", "ts":now-1,"closed_ts":now}]
        notifications.write({"schema_version":1,"dnd":False,"live":[],"history":rows})
        for contract, count in (("4.0.6",1),("4.5.0-rc2",2)):
            with patch.object(status, "probe_json", return_value={"provider":"wuling.notifications","contract":contract}):
                result = status.comms()["items"]
            self.assertEqual([row["key"] for row in result], ["second","first"])
            self.assertEqual(result[1]["body"], "First\nSecond & third")
            self.assertEqual(result[1]["summary"], "Earlier")
            self.assertEqual(len(result[1]["actions"]), count)
            self.assertNotIn("argv", json.dumps(result))

    def test_history_action_never_accepts_argv_or_an_arbitrary_key(self):
        self.assertEqual(actions.plan("comms-action",'{"key":"fixture-1","index":-1}'),
                         ["omarchy-shell","wuling.notifications","historyDeed","fixture-1","-1"])
        for payload in ('[]','null','{"key":"x;bad","index":0}','{"key":"x","index":true}',
                        '{"key":"x","index":3}','{"key":"x","argv":["bad"]}'):
            with self.subTest(payload=payload), self.assertRaises(Error):
                actions.plan("comms-action", payload)
        with patch.object(actions,"command",return_value="none"), self.assertRaises(Error):
            actions.run("comms-action",'{"key":"expired","index":-1}')

    def test_page_open_targets_focused_output_and_rejects_disabled_page(self):
        with patch.object(actions,"command",side_effect=['[{"name":"Virtual-1","focused":true}]',"ok"]) as command:
            self.assertTrue(actions.terminal("open","comms")["ok"])
            self.assertEqual(command.call_args.args[0], ["omarchy-shell","wuling.terminal.Virtual-1","page","comms"])
        with self.assertRaises(Error):
            actions.terminal("toggle","comms")
        with patch.object(actions,"command",side_effect=['[{"name":"Virtual-1","focused":true}]',"off"]), self.assertRaises(actions.PanelUnavailable):
            actions.terminal("open","comms")

    def test_stopping_collector_kills_pending_probe_and_prevents_followups(self):
        status._stopping.clear()
        with tempfile.TemporaryDirectory() as folder:
            ready = Path(folder)/"ready"
            source = "import pathlib,time;pathlib.Path("+repr(str(ready))+").touch();time.sleep(30)"
            worker = threading.Thread(target=status.probe,args=([sys.executable,"-c",source],),kwargs={"timeout":30})
            worker.start()
            try:
                deadline = time.monotonic()+3
                while not ready.exists() and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertTrue(ready.exists())
                status.stop_probes()
                worker.join(1)
                self.assertFalse(worker.is_alive())
                self.assertIsNone(status.probe([sys.executable,"-c","print('late')"]))
            finally:
                status.stop_probes()
                worker.join(1)
                status._stopping.clear()

    def test_spectrum_rejects_partial_frames_and_clamps_values(self):
        self.assertIsNone(spectrum.bars("1;2;"))
        self.assertIsNone(spectrum.bars("bad;"*20))
        self.assertEqual(spectrum.bars("-1;2000;"+"500;"*18),[0,1]+[.5]*18)

    def test_spectrum_termination_reaps_child_and_private_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pidfile = root / "child"
            fake = root / "cava"
            fake.write_text("#!"+sys.executable+"\nimport os,pathlib,time\npathlib.Path("+repr(str(pidfile))+").write_text(str(os.getpid()))\nprint('500;'*20,flush=True)\ntime.sleep(30)\n")
            fake.chmod(0o700)
            env = {**os.environ,"PATH":folder+os.pathsep+os.environ["PATH"],"XDG_RUNTIME_DIR":folder}
            child = subprocess.Popen([sys.executable,str(ROOT/"bin/wuling"),"status","--spectrum"], env=env,
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+5
                while not pidfile.exists() and child.poll() is None and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertTrue(pidfile.exists())
                analyzer=int(pidfile.read_text())
                self.assertEqual(os.getpriority(os.PRIO_PROCESS,analyzer),19)
                child.terminate()
                out,err=child.communicate(timeout=2)
                self.assertEqual(child.returncode,0,err)
                self.assertEqual(json.loads(out.splitlines()[0])["bars"],[.5]*20)
                with self.assertRaises(ProcessLookupError):
                    os.kill(analyzer,0)
                self.assertEqual(list(root.glob("wuling-spectrum-*")),[])
            finally:
                if child.poll() is None:
                    child.kill()
                child.communicate()


if __name__ == "__main__":
    unittest.main()
