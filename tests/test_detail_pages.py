"""Live device identity, accounting, calendar boundaries and scoped collection."""
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
from test_foundations import IsolatedHome
from wuling import Error, ROOT
from wuling import actions, details, devices, status


class DetailPageTests(IsolatedHome):
    def test_performance_deltas_pid_reuse_and_memory_accounting(self):
        proc=self.home/'proc';proc.mkdir()
        (proc/'cpuinfo').write_text('model name : Fixture CPU\ncpu MHz : 2400\n')
        (proc/'uptime').write_text('900 0')
        (proc/'loadavg').write_text('0.5 0.2 0.1 1/10 10')
        (proc/'meminfo').write_text('MemTotal: 1000 kB\nMemAvailable: 400 kB\nCached: 300 kB\nBuffers: 200 kB\nSwapTotal: 100 kB\nSwapFree: 60 kB\n')
        process=proc/'12';process.mkdir()
        def write(user,idle,start,ticks):
            (proc/'stat').write_text(f'cpu {user} 0 0 {idle} 0 0 0 0\ncpu0 {user} 0 0 {idle} 0 0 0 0\n')
            fields=['0']*22;fields[0]='S';fields[11]=str(ticks);fields[19]=str(start);fields[21]='10'
            (process/'stat').write_text('12 (name with ) space) '+' '.join(fields))
        write(10,90,1,10)
        with patch.object(status,'PROC',proc), patch.object(status,'SYS',self.home/'sys'), patch.object(details.time,'monotonic',side_effect=[1,2,3]):
            reader=details.Performance();reader.hz=100
            self.assertIsNone(reader.read()['cpu_percent'])
            write(50,150,1,35);row=reader.read()
            self.assertEqual(row['cpu_percent'],40)
            self.assertEqual(row['threads'][0]['percent'],40)
            self.assertEqual(row['processes'][0]['cpu'],25)
            self.assertEqual(row['processes'][0]['name'],'name with ) space')
            memory=row['memory'];self.assertEqual(memory['used']+memory['cache']+memory['free'],memory['total'])
            self.assertEqual(memory['swap_used'],40*1024)
            write(60,240,2,5)
            self.assertIsNone(reader.read()['processes'][0]['cpu'])

    def test_power_uses_energy_weighting_and_excludes_absent_pack(self):
        prefix='/org/freedesktop/UPower/devices/'
        packs={prefix+'battery_A':dict(Type=2,PowerSupply=True,IsPresent=True,EnergyFull=50,Energy=25,EnergyRate=5,Percentage=50,Capacity=90,State=2),
               prefix+'battery_B':dict(Type=2,PowerSupply=True,IsPresent=True,EnergyFull=10,Energy=10,EnergyRate=1,Percentage=100,Capacity=80,State=2),
               prefix+'battery_C':dict(Type=2,PowerSupply=True,IsPresent=True,EnergyFull=0,Energy=0,Percentage=0)}
        def call(bus,service,path,interface,method,*args):
            return [list(packs)] if method=='EnumerateDevices' else [prefix+'DisplayDevice'] if method=='GetDisplayDevice' else [[[100,50,2],[99990,70,2],[99995,0,0],[99996,80,1]]]
        profiles={'Profiles':[{'Profile':{'type':'s','data':name}} for name in ['power-saver','balanced']], 'ActiveProfile':'balanced'}
        def properties(bus,service,path,interface):
            return profiles if service=='org.freedesktop.UPower.PowerProfiles' else packs.get(path,{'OnBattery':True})
        with patch.object(devices,'call',side_effect=call), patch.object(devices,'properties',side_effect=properties), patch.object(status,'probe',return_value=None), patch.object(details.time,'time',return_value=100000):
            row=details.Power().read()
        self.assertAlmostEqual(row['percent'],100*35/60)
        self.assertEqual(row['watts'],6)
        self.assertEqual(row['profiles'],['power-saver','balanced'])
        self.assertEqual(row['profile'],'balanced')
        self.assertFalse(row['packs'][2]['present'])
        self.assertEqual([r['percent'] for r in row['history']],[70,80])

    def test_audio_volume_curve_and_default_dsp_target(self):
        data=[{'type':'PipeWire:Interface:Metadata','props':{'metadata.name':'default'},'metadata':[{'key':'default.audio.sink','value':{'name':'dsp'}}]}]
        for i,name in enumerate(['dsp','physical','unplugged']):
            data.append({'type':'PipeWire:Interface:Node','id':i,'info':{'props':{'media.class':'Audio/Sink','node.name':name,'object.serial':i+10},'params':{'Props':[{'channelVolumes':[.125,.125],'mute':False}]}}})
        def probe(argv):
            return json.dumps(data) if argv==['pw-dump'] else json.dumps({'unplugged':False}) if argv==['omarchy-audio-sink-availability'] else 'physical'
        with patch.object(status,'probe',side_effect=probe):
            result=details.audio()
        rows=result['outputs'];self.assertTrue(rows[0]['active']);self.assertAlmostEqual(rows[0]['volume'],50)
        self.assertTrue(next(r for r in rows if r['name']=='physical')['volume_target'])
        self.assertFalse(next(r for r in rows if r['name']=='unplugged')['available'])
        with patch.object(details,'audio',return_value=result):
            self.assertEqual(actions.plan('audio-volume','{"id":0,"serial":10,"value":25}'),['wpctl','set-volume','1','0.25'])
            self.assertEqual(actions.plan('audio-default','{"id":1,"serial":11}'),['omarchy-audio-output-set-default','1','physical'])
            for name,payload in [('audio-mute','{"id":0,"serial":99}'),('audio-volume','{"id":0,"serial":10,"value":NaN}'),('audio-default','{"id":2,"serial":12}'),('audio-default','{"id":0,"serial":10,"argv":[]}')]:
                with self.subTest(name=name,payload=payload),self.assertRaises(Error):actions.plan(name,payload)

    def test_native_failed_device_change_is_not_success_and_copy_uses_stdin(self):
        snapshot={'outputs':[{'id':1,'serial':2,'active':False,'available':True,'name':'sink','volume_target':False,'muted':False}],'inputs':[],'streams':[]}
        with patch.object(details,'audio',return_value=snapshot),patch.object(actions,'command',return_value=''),self.assertRaises(Error):
            actions.run('audio-default','{"id":1,"serial":2}')
        with patch.object(details.System,'read',return_value={'host':'Fixture'}),patch.object(actions.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
            actions.run('system-copy')
            self.assertEqual(run.call_args.args[0],['wl-copy'])
            self.assertEqual(json.loads(run.call_args.kwargs['input']),{'host':'Fixture'})
            self.assertEqual(run.call_args.kwargs['stdout'],subprocess.DEVNULL)
            self.assertEqual(run.call_args.kwargs['stderr'],subprocess.DEVNULL)

    def test_detail_collectors_are_opt_in_and_stop(self):
        with patch.object(details.Performance,'read',return_value={'cpu_percent':20}) as performance,patch.object(details,'audio') as audio:
            collector=status.Collector(['performance'])
            try:
                self.assertEqual(collector.read(wait=True)['performance']['cpu_percent'],20)
                performance.assert_called_once();audio.assert_not_called()
                self.assertEqual(collector.sections,{'performance'})
            finally:collector.close()
        with patch.object(details,'Performance') as performance,patch.object(details,'Power') as power,patch.object(details,'System') as system:
            collector=status.Collector()
            self.assertEqual(collector.sections,set(status.OVERVIEW_SECTIONS)|{'batteries'})
            collector.close();performance.assert_not_called();power.assert_not_called();system.assert_not_called()

    def test_system_identity_arrives_before_slow_native_versions(self):
        release=threading.Event()
        def slow():
            release.wait(2)
            return {'host':'Fixture','quickshell':'Quickshell fixture'}
        with patch.object(details.System,'read',side_effect=slow),patch.object(status,'text',side_effect=lambda path,*args:'Fixture' if str(path)=='/etc/hostname' else ''):
            collector=status.Collector(['system'])
            try:
                early=collector.read()
                self.assertEqual(early['system']['host'],'Fixture')
                self.assertEqual(early['pending'],['system'])
                self.assertNotIn('quickshell',early['system'])
                release.set()
                self.assertEqual(collector.read(wait=True)['system']['quickshell'],'Quickshell fixture')
            finally:
                release.set();collector.close()

    def test_parallel_page_close_cancels_every_probe_and_pending_work(self):
        status._stopping.clear()
        ready=self.home/'ready';ready.mkdir()
        code="import pathlib,os,time;pathlib.Path("+repr(str(ready))+",str(os.getpid())).touch();time.sleep(30)"
        worker=threading.Thread(target=details.parallel,args=({str(i):lambda:status.probe([sys.executable,'-c',code],timeout=30) for i in range(8)},))
        worker.start()
        try:
            deadline=time.monotonic()+3
            while len(list(ready.iterdir()))<4 and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(len(list(ready.iterdir())),4)
            status.stop_probes();worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(list(ready.iterdir())),4)
        finally:
            status.stop_probes();worker.join(2);status._stopping.clear()

    def test_calendar_leap_day_iso_year_and_dst_do_not_shift_grid(self):
        source=(ROOT/'plugins/terminal/Detail.js').read_text().replace('.pragma library','')
        assertions='''
const assert=require('assert');
assert.equal(isoWeek(new Date(2021,0,1,12)),53);
assert.equal(isoWeek(new Date(2024,11,30,12)),1);
const feb=month(2024,2);assert.equal(feb.length,42);assert.equal(feb.filter(d=>d.month===2).length,29);
assert.deepEqual(feb[0],{year:2024,month:1,day:29,week:5});
const march=month(2026,3);assert.equal(march.filter(d=>d.month===3).length,31);
for(let i=1;i<march.length;i++){const a=march[i-1],b=march[i];assert.equal((Date.UTC(b.year,b.month-1,b.day)-Date.UTC(a.year,a.month-1,a.day))/86400000,1);}
'''
        subprocess.run(['node','-e',source+assertions],check=True)


if __name__=='__main__':unittest.main()
