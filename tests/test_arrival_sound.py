"""Startup gates and bounded factual payloads do not invent state."""
from pathlib import Path
import hashlib
import json
import subprocess
import wave
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import ROOT, arrival, settings


class ArrivalSoundTests(IsolatedHome):
    def test_late_or_unknown_compositor_never_counts_as_a_login(self):
        signature='a'*40+'_1700000000_123'
        cases=[(signature,1700000000000,True),(signature,1700000029999,True),
               (signature,1700000030000,False),(signature,1699999999999,False),
               ('unknown',1700000000000,False),('a_1700000000_123',1700000000000,False)]
        code=(ROOT/'kit/SessionIdentity.js').read_text().replace('.pragma library','')
        result=subprocess.check_output(['node','-e',code+'\nconsole.log(JSON.stringify('+json.dumps(cases)+'.map(x=>fresh(x[0],x[1]))));'],text=True)
        self.assertEqual(json.loads(result),[x[2] for x in cases])

    def test_early_gate_agrees_with_canonical_settings(self):
        documents = [
            '', '"session.arrival" = false', 'session.arrival=false # off',
            '[session]\narrival=false\nexit=true', "['session']\n'arrival'=false",
            'session = { arrival = false, exit = true }',
            'login_music = "session.arrival=false"',
            "login_music = '''session.arrival=false'''\n",
            '"session\\u002earrival"=false',
            'terminal.sections=["clock",\n"agent",]\n[session]\narrival=true',
            'schema_version=1\n[session]\narrival=false',
            'login_music = "/example/1.0.wav"\n"session.arrival"=false',
        ]
        expected = [settings.load(text).get('session.arrival', True) for text in documents]
        code = (ROOT / 'plugins/session/Gate.js').read_text().replace('.pragma library', '')
        output = subprocess.check_output(['node', '-e', code + '\nconsole.log(JSON.stringify(' + json.dumps(documents) + '.map(arrivalEnabled)));'], text=True)
        self.assertEqual(json.loads(output), expected)
        invalid = ['[session\narrival=true', 'session.arrival = "false"', 'x' * 65537, '"session.arrival"=false\n"session.arrival"=true']
        output = subprocess.check_output(['node', '-e', code + '\nconsole.log(JSON.stringify(' + json.dumps(invalid) + '.map(arrivalEnabled)));'], text=True)
        self.assertEqual(json.loads(output), [False]*len(invalid))

    def test_arrival_unavailable_readings_are_explicit_not_fake_versions(self):
        with patch.object(arrival, 'probe', return_value=None), patch.object(arrival.socket, 'gethostname', return_value='fixture'), patch.object(arrival.getpass, 'getuser', return_value='operator'):
            result = arrival.prepare()
        by_key={row['key']:row for row in result['rows']}
        for key in ('compositor','shell','link'):
            self.assertEqual(by_key[key]['value'],'—')
            self.assertFalse(by_key[key]['ok'])
        self.assertEqual(result['host'],'FIXTURE')
        self.assertEqual(result['screens'],[])

    def test_sound_manifest_is_original_bounded_pcm(self):
        manifest=json.loads((ROOT/'sounds/manifest.json').read_text())
        cues=set(settings.tokens()['sound']['cues']) | {f'tick-{i}' for i in range(1,8)}
        self.assertEqual(set(manifest['files']),{name+'.wav' for name in cues})
        for name,digest in manifest['files'].items():
            path=ROOT/'sounds'/name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
            with wave.open(str(path)) as stream:
                self.assertEqual((stream.getnchannels(),stream.getsampwidth(),stream.getframerate()),(1,2,48000))
                self.assertLessEqual(stream.getnframes()/stream.getframerate(),2)
