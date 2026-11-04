"""Public radio identity, secret transport and truthful native failures."""
import io
import json
import os
import signal
import subprocess
import sys
import time
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, ROOT
from wuling import actions, devices, radios, status


class RadioTests(IsolatedHome):
    def test_wifi_reads_cached_access_points_and_public_settings(self):
        base=radios.NM_PATH;service=radios.NM
        ap=base+'/AccessPoint/7';device=base+'/Devices/2';profile=base+'/Settings/4'
        props={(base,service):{'Devices':[device],'WirelessEnabled':True,'WirelessHardwareEnabled':True},
               (device,service+'.Device'):{'DeviceType':2,'Managed':True,'Interface':'wlan-test','State':30},
               (device,service+'.Device.Wireless'):{'AccessPoints':[ap],'LastScan':2000},
               (ap,service+'.AccessPoint'):{'Ssid':list(b'field-net'),'HwAddress':'AA:BB:CC:DD:EE:FF','Frequency':5200,'Strength':78,'RsnFlags':256}}
        settings={'connection':{'type':'802-11-wireless','uuid':'fixture-profile'},'802-11-wireless':{'ssid':list(b'field-net')},'802-11-wireless-security':{'key-mgmt':'wpa-psk'}}
        def call(path,interface,method):
            self.assertIn(method,('ListConnections','GetSettings'))
            return [profile] if method=='ListConnections' else settings
        with patch.object(radios,'nmprops',side_effect=lambda path,interface:props.get((path,interface),{})),patch.object(radios,'nmcall',side_effect=call),patch.object(radios.time,'clock_gettime',return_value=5):
            snapshot=radios.Wifi().read()
        row=snapshot['networks'][0]
        self.assertEqual((row['security'],row['uuid'],row['band'],snapshot['age']),('psk','fixture-profile','5G',3))
        for address,expected in (([170,187,204,221,238,255],'fixture-profile'),([170,187,204,221,238,254],'')):
            settings['802-11-wireless']['bssid']=address
            with patch.object(radios,'nmprops',side_effect=lambda path,interface:props.get((path,interface),{})),patch.object(radios,'nmcall',side_effect=call):
                self.assertEqual(radios.Wifi().read()['networks'][0]['uuid'],expected)

    def test_wifi_credential_is_only_stdin_and_stale_target_rejected(self):
        row={'id':'ap','name':'field-net','address':'AA:BB:CC:DD:EE:FF','connected':False,'security':'psk','uuid':''}
        snapshot={'interface':'wlan-test','networks':[row],'linked':None}
        request=json.dumps({'id':'ap','interface':'wlan-test','credentials':True})
        with patch.object(radios.Wifi,'__init__',return_value=None),patch.object(radios.Wifi,'read',side_effect=[snapshot,{'linked':row}]),patch.object(radios,'nmprops',return_value={'Ssid':list(b'field-net')}),patch.object(radios.sys,'stdin',io.StringIO('fixture-passphrase\n')),patch.object(radios,'execute') as execute:
            actions.run('wifi-connect',request)
            calls=execute.call_args_list
            self.assertNotIn('fixture-passphrase',json.dumps([call.args for call in calls]))
            self.assertEqual(calls[1].kwargs['secret'],'802-11-wireless-security.psk:fixture-passphrase\n')
            self.assertEqual(calls[1].args[0][-2:],['passwd-file','/dev/stdin'])
            self.assertIn('AddConnection',calls[0].args[0])
        with patch.object(radios.Wifi,'__init__',return_value=None),patch.object(radios.Wifi,'read',return_value=snapshot),patch.object(radios,'execute') as execute:
            for value in ({'id':'removed','interface':'wlan-test'},{'id':'ap','interface':'removed'}):
                with self.assertRaises(Error):actions.run('wifi-connect',json.dumps(value))
            execute.assert_not_called()
        with patch.object(radios.Wifi,'__init__',return_value=None),patch.object(radios.Wifi,'read',return_value=snapshot),patch.object(radios.sys,'stdin',io.StringIO('invalid\0pass\n')),patch.object(radios,'execute') as execute:
            with self.assertRaises(Error):actions.run('wifi-connect',request)
            execute.assert_not_called()

    def test_enterprise_hands_off_without_reading_a_secret(self):
        snapshot={'interface':'wlan-test','networks':[{'id':'ap','security':'enterprise'}],'linked':None}
        with patch.object(radios.Wifi,'__init__',return_value=None),patch.object(radios.Wifi,'read',return_value=snapshot),patch.object(actions,'route') as route,patch.object(radios.sys,'stdin') as stdin:
            actions.run('wifi-connect',json.dumps({'id':'ap','interface':'wlan-test'}))
            route.assert_called_once_with('open','omarchy.network');stdin.readline.assert_not_called()

    def test_retry_replaces_saved_secret_through_stdin_without_readline_prefill(self):
        row={'id':'ap','address':'AA:BB:CC:DD:EE:FF','connected':False,'security':'psk','uuid':'fixture-profile'}
        snapshot={'interface':'wlan-test','networks':[row],'linked':None}
        secret=' leading and trailing \\ : " value \n'
        with patch.object(radios.Wifi,'__init__',return_value=None),patch.object(radios.Wifi,'read',side_effect=[snapshot,{'linked':row}]),patch.object(radios.sys,'stdin',io.StringIO(secret)),patch.object(radios,'execute') as execute:
            actions.run('wifi-connect',json.dumps({'id':'ap','interface':'wlan-test','credentials':True}))
        calls=execute.call_args_list
        self.assertEqual(calls[0].args[0][-2:],['802-11-wireless-security.psk',''])
        self.assertEqual(calls[1].args[0][-2:],['passwd-file','/dev/stdin'])
        self.assertEqual(calls[1].kwargs['secret'],'802-11-wireless-security.psk:'+secret)
        self.assertNotIn(secret,json.dumps([call.args for call in calls]))

    def test_rfkill_only_adapter_remains_visible(self):
        root=self.home/'sys';radio=root/'class/rfkill/rfkill0';radio.mkdir(parents=True)
        (radio/'type').write_text('bluetooth\n');(radio/'soft').write_text('1\n')
        with patch.object(status,'SYS',root),patch.object(devices,'call',return_value=[]),patch.object(status,'probe',return_value=None):
            self.assertTrue(radios.bluetooth_present())
            result=radios.bluetooth();self.assertTrue(result['present']);self.assertFalse(result['enabled'])

    def test_bluez_nested_variants_and_default_adapter(self):
        def variant(value):return {'type':'s','data':value}
        objects={'/a':{'org.bluez.Adapter1':{'Address':variant('AA:BB:CC:DD:EE:01'),'Powered':variant(True)}},
                 '/b':{'org.bluez.Adapter1':{'Address':variant('AA:BB:CC:DD:EE:02'),'Powered':variant(True)}},
                 '/b/device':{'org.bluez.Device1':{'Adapter':variant('/b'),'Alias':variant('Field Sensor'),'Address':variant('AA:BB:CC:DD:EE:03'),'Paired':variant(True)},'org.bluez.Battery1':{'Percentage':variant(73)}}}
        with patch.object(devices,'call',return_value=[objects]),patch.object(status,'probe',return_value='Controller AA:BB:CC:DD:EE:02 Field [default]'):
            row=radios.bluetooth()
        self.assertEqual(row['adapter'],'/b');self.assertEqual(row['devices'][0]['battery'],73)
        snapshot={'adapter':'/b','devices':[{'id':'/b/device','address':'AA:BB:CC:DD:EE:03','connected':False}]}
        with patch.object(radios,'bluetooth',return_value=snapshot),patch.object(radios,'execute'):
            with self.assertRaises(Error):actions.run('bluetooth-connect',json.dumps({'id':'/b/device','adapter':'/b'}))

    def test_native_failure_output_is_never_forwarded(self):
        with self.assertRaises(Error) as caught:
            radios.execute([sys.executable,'-c','import sys;print("private-service-answer",file=sys.stderr);sys.exit(1)'])
        self.assertNotIn('private-service-answer',str(caught.exception))

    def test_cancel_radio_action_reaps_its_process_group(self):
        child_pid=self.home/'child-pid'
        script='import os,time;open('+repr(str(child_pid))+',"w").write(str(os.getpid()));time.sleep(60)'
        code='from wuling.radios import execute;execute('+repr([sys.executable,'-c',script])+',timeout=60)'
        env={**os.environ,'PYTHONPATH':str(ROOT/'bin/lib'),'PYTHONDONTWRITEBYTECODE':'1'}
        parent=subprocess.Popen([sys.executable,'-c',code],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            until=time.monotonic()+3
            while not child_pid.exists() and time.monotonic()<until:time.sleep(.02)
            self.assertTrue(child_pid.exists());pid=int(child_pid.read_text())
            parent.send_signal(signal.SIGTERM);parent.wait(timeout=3)
            with self.assertRaises(ProcessLookupError):os.kill(pid,0)
        finally:
            if parent.poll() is None:parent.kill();parent.wait()

    def test_tailnet_login_is_not_projected_and_failures_stay_failed(self):
        data={'BackendState':'NeedsLogin','AuthURL':'https://login.example.test/auth','Self':{},'Peer':{}}
        with patch.object(radios.shutil,'which',return_value='/fixture/tailscale'),patch.object(status,'probe_json',return_value=data):
            self.assertNotIn('AuthURL',radios.tailnet())
            from wuling import dispatch
            with patch.object(dispatch,'native_launch',return_value=True) as launch:
                radios.tailnet_action('start');self.assertEqual(launch.call_args.args[0][0],'omarchy-launch-browser')
        with patch.object(radios.shutil,'which',return_value='/fixture/tailscale'),patch.object(status,'probe_json',return_value={'BackendState':'Stopped'}),patch.object(radios,'execute'):
            with self.assertRaises(Error):radios.tailnet_action('start')
