"""Exit actions stay independent of visual lifetime and preserve native argv/env."""
import json
import os
import time
from unittest.mock import patch
from test_foundations import IsolatedHome, InstallHome
from wuling import Error, actions, jsonc, lifecycle, power, session, theme


class ExitTests(IsolatedHome):
    def execute(self, *, ready=True, reduced=False, off=False, failed_theme=False, preview=False, survives=False):
        clock = time
        start = time.time()
        resolved = theme.resolve('wuling', {'motion':'reduced' if reduced else 'full', 'session.exit':not off})
        request = json.dumps({'id':'system.logout', 'action':'printf "native-action"', 'started':start*1000, 'preview':preview})
        calls = []
        def launched(argv, **kw):
            if argv[0] != "omarchy-shell":
                calls.append((clock.time()-start, argv, kw))
        before = dict(os.environ)
        with patch.object(session.theme, 'resolve', side_effect=Error('fixture') if failed_theme else None, return_value=resolved), \
             patch.object(session.dispatch, 'enabled', return_value=True), patch.object(session, 'mark_url', return_value=('',None)), \
             patch.object(session, 'ipc', return_value='ready' if ready else 'unavailable') as ipc, \
             patch.object(session, 'compositor', return_value=None), patch.object(session, 'alive', return_value=survives), \
             patch.object(session.subprocess, 'Popen', side_effect=launched), patch.object(session.subprocess, 'run'):
            result = session.run(request)
        self.assertEqual(dict(os.environ), before)
        self.assertFalse((self.home/'wuling/exit-osd.json').exists())
        self.assertEqual(list((self.home/'wuling').glob('exit-*')), [])
        return calls, result, ipc

    def test_full_and_reduced_dispatch_exactly_once_at_deadline(self):
        for reduced, delay in ((False,.56),(True,.12)):
            with self.subTest(reduced=reduced):
                calls, result, _ = self.execute(reduced=reduced)
                self.assertEqual(len(calls), 1)
                self.assertAlmostEqual(calls[0][0], delay, delta=.08)
                self.assertEqual(calls[0][1], ['bash','-c','printf "native-action"'])
                self.assertNotIn('env', calls[0][2])
                self.assertTrue(result['ended'])

    def test_visual_failure_and_disabled_motion_never_swallow_action(self):
        for kwargs in ({'ready':False},{'off':True},{'failed_theme':True}):
            with self.subTest(kwargs=kwargs):
                calls, result, _ = self.execute(**kwargs)
                self.assertEqual(len(calls), 1)
                self.assertLess(calls[0][0], .15)
                self.assertFalse(result['overlay'])

    def test_preview_runs_nothing_and_surviving_session_gets_one_notice(self):
        calls, result, _ = self.execute(preview=True)
        self.assertEqual(calls, [])
        self.assertTrue(result['preview'])
        calls, result, ipc = self.execute(survives=True)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][1][0], 'notify-send')
        self.assertAlmostEqual(calls[1][0]-calls[0][0], 10, delta=.101)
        self.assertEqual(sum(c.args[0]=='finish' for c in ipc.call_args_list), 1)
        self.assertFalse(result['ended'])

    def test_slow_visual_ipc_does_not_postpone_reduced_action(self):
        started=time.time();sent=[]
        with patch.object(session.subprocess, "Popen", side_effect=lambda *a,**k:sent.append(time.time())):
            deadline=session.ActionDeadline("true",started+.12)
            time.sleep(.3)  # The independent visual handshake is still blocked.
            self.assertEqual(len(sent),1)
            self.assertLess(sent[0]-started,.22)
            deadline.expedite();deadline.join()
            self.assertEqual(len(sent),1)

    def test_stale_lease_cleanup_never_removes_newer_exit(self):
        directory=session.runtime();lease=directory/'exit-osd.json'
        lease.write_text('{"token":"new"}')
        session.clear_lease(directory,'old')
        self.assertTrue(lease.exists())
        session.clear_lease(directory,'new')
        self.assertFalse(lease.exists())


class RouteTests(IsolatedHome):
    def test_exit_zero_unknown_is_a_panel_error(self):
        with patch.object(actions,'command',return_value='unknown'):
            for function in (lambda:actions.terminal('open'),lambda:actions.run('panel','tailscale'),lambda:actions.route('open','wuling.dispatch')):
                with self.assertRaises(actions.PanelUnavailable): function()
        with patch.object(actions,'command',return_value='ok'):
            self.assertTrue(actions.terminal('open')['ok'])
            self.assertTrue(actions.run('panel','wifi')['ok'])

    def test_void_router_checks_live_enabled_target(self):
        for action in ('toggle','close'):
            with patch.object(actions,'command',return_value='[]'),self.assertRaises(actions.PanelUnavailable):
                actions.route(action,'wuling.dispatch')
            with patch.object(actions,'command',side_effect=['[{"id":"wuling.dispatch","enabled":true}]','{"opened":false}','']) as native:
                actions.route(action,'wuling.dispatch')
                self.assertEqual(native.call_count,3)


class MenuTests(InstallHome):
    def test_owned_system_route_restores_exact_original_with_unrelated_edit(self):
        path=power.extension_path();path.parent.mkdir(parents=True,exist_ok=True)
        original='// user settings\n{ "system": {"label":"Custom system"}, "personal": {"action":"true"}, }\n'
        path.write_text(original)
        lifecycle.install(True)
        self.assertEqual(jsonc.loads(path.read_text())['system']['action'],'wuling power toggle')
        path.write_text(path.read_text().replace('"action":"true"','"action":"false"'))
        lifecycle.uninstall(True)
        self.assertEqual(path.read_text(),original.replace('"action":"true"','"action":"false"'))

    def test_existing_user_system_action_is_refused_before_mutation(self):
        path=power.extension_path();path.parent.mkdir(parents=True,exist_ok=True)
        original='{"system":{"action":"my-power-menu"}}\n';path.write_text(original)
        with self.assertRaises(Error): lifecycle.install(True)
        self.assertEqual(path.read_text(),original)
        self.assertIsNone(lifecycle.manifest())

    def test_new_user_system_action_survives_removal(self):
        lifecycle.install(True);path=power.extension_path()
        current=path.read_text().replace('wuling power toggle','my-power-menu');path.write_text(current)
        lifecycle.uninstall(True)
        self.assertEqual(path.read_text(),current)
