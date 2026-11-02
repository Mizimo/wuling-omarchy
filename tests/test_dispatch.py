"""Desktop launch, private history and calculator input boundaries."""
import json
import os
from pathlib import Path
import subprocess
import time
from unittest.mock import patch
from test_foundations import IsolatedHome, ROOT
from wuling import Error, dispatch, jsonc


class DispatchTests(IsolatedHome):
    def test_hidden_user_entry_masks_system_app_and_terminal_codes_are_argv(self):
        system = self.home / "system"
        user = self.home / ".local/share/applications"
        user.mkdir(parents=True)
        (system / "applications").mkdir(parents=True)
        (system / "applications/masked.desktop").write_text('[Desktop Entry]\nName=System\nExec=system\n')
        (user / "masked.desktop").write_text('[Desktop Entry]\nHidden=true\n')
        (user / "terminal.desktop").write_text('[Desktop Entry]\nType=Application\nName=Name $(do-not-run)\nExec=fixture "two words" %c %k %i %U %%\nIcon=fixture-icon\nTerminal=true\n')
        with patch.dict(os.environ, {"XDG_DATA_DIRS": str(system), "OMARCHY_PATH": str(self.home / "native")}):
            rows = dispatch.applications()
        self.assertEqual([a["id"] for a in rows], ["terminal.desktop"])
        self.assertEqual(dispatch.terminal_argv(rows[0]), ['omarchy-launch-tui', 'fixture', 'two words', 'Name $(do-not-run)', str(user / 'terminal.desktop'), '--icon', 'fixture-icon', '%'])

    def test_nonterminal_launch_keeps_desktop_suffix_and_does_not_shell_metadata(self):
        row = {"id":"org.fixture.desktop.desktop", "terminal":False, "cwd":""}
        with patch.object(dispatch, "applications", return_value=[row]), patch.object(dispatch, "detached") as launch, patch.object(dispatch, "remember"):
            dispatch.activate("apps", row["id"])
        launch.assert_called_once_with(["uwsm-app", "--", "gtk-launch", row["id"]], None)

    def test_private_bounded_history_survives_invalid_selection_and_symlinks(self):
        for i in range(35):
            dispatch.remember("ask", "Question " + str(i))
        data = dispatch.history()
        self.assertEqual(len(data["ask"]), 30)
        self.assertEqual(data["ask"][0], "Question 34")
        self.assertEqual(dispatch.state_path().stat().st_mode & 0o777, 0o600)
        self.assertEqual(dispatch.state_path().parent.stat().st_mode & 0o777, 0o700)
        before = dispatch.state_path().read_bytes()
        with self.assertRaises(Error):
            dispatch.activate("run", "\0")
        self.assertEqual(dispatch.state_path().read_bytes(), before)
        dispatch.state_path().unlink()
        target = self.home / "unrelated"; target.write_text("keep")
        dispatch.state_path().symlink_to(target)
        with self.assertRaises(Error):
            dispatch.remember("run", "fixture")
        dispatch.cleanup()
        self.assertEqual(target.read_text(), "keep")

    def test_clipboard_is_hidden_when_native_provider_is_off(self):
        path = self.home / ".config/omarchy/shell.json";path.parent.mkdir(parents=True)
        path.write_text('{"disabledPlugins":["omarchy.clipboard"]}')
        self.assertEqual(dispatch.clipboard(), [])
        with self.assertRaises(Error), patch.object(dispatch, "detached") as launch:
            dispatch.activate("clip", "0")
        launch.assert_not_called()

    def test_copy_returns_when_helper_leaves_a_background_process(self):
        # A child retaining stdout was sufficient to stall CALC and every
        # following mode. Verify the process boundary, not a mock of it.
        start = time.monotonic()
        self.assertTrue(dispatch.native_launch(["bash", "-c", "sleep 0.5 &"]))
        self.assertLess(time.monotonic()-start, .35)

    def test_missing_agent_preserves_history_and_reports_native_failure(self):
        with patch.object(dispatch, "native_launch", return_value=False) as launch:
            with self.assertRaises(dispatch.AgentUnavailable):
                dispatch.activate("ask", "Synthetic question")
        launch.assert_called_once_with(["omarchy", "agent", "prompt", "Synthetic question"])
        self.assertEqual(dispatch.history()["ask"], [])

    def test_jsonc_never_rewrites_comma_or_comment_syntax_inside_a_string(self):
        source = '{/* note */ "system": {"action":' + json.dumps('printf ",}" // literal') + '}, // keep\n "array":[1,2,],}'
        self.assertEqual(jsonc.loads(source)["system"]["action"], 'printf ",}" // literal')
        updated, record = jsonc.set_member(source, "system", {"action":"fixture"})
        self.assertIn('// keep', updated)
        self.assertEqual(jsonc.remove_member(updated, record), source)

    def test_calculator_grammar_and_fuzzy_labels(self):
        code = (ROOT / "plugins/dispatch/Model.js").read_text().replace('.pragma library', '')
        assertions = r'''
const assert=require('assert');
for(const [input,expected] of [['1366*768','1049088'],['2^3^2','512'],['-2^2','-4'],['2^-2','0.25'],['(.2+.1)*10','3'],['10%3','1'],['4×(2+3)÷2','10']]) assert.equal(calculate(input),expected,input);
for(const input of ['','1/0','2+','process.exit()','2;3','Math.PI','1e999','('.repeat(50)+'1'+')'.repeat(50)]) assert.equal(calculate(input),null,input);
assert(score('Chromium','chrm')>0);assert.equal(score('Chromium','zxx'),0);
assert(!highlight('<b>unsafe</b>','unsafe','#fff').includes('<b>'));
'''
        subprocess.run(["node", "-e", code + assertions], check=True)
