#!/usr/bin/env python3
"""Read-only 24-hour observer; private JSONL goes to stdout, never the repo.

No QML instrumentation, setting changes, session control or notification text.
All CPU percentages mean one core. Explicit PIDs prevent silently joining runs.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time


def process(pid):
    base=Path('/proc')/str(pid)
    stat=base.joinpath('stat').read_text().rsplit(')',1)[1].split()
    memory={}
    for line in base.joinpath('smaps_rollup').read_text().splitlines():
        m=re.fullmatch(r'(\w+):\s+(\d+) kB',line)
        if m:memory[m[1]]=int(m[2])
    fds=list(base.joinpath('fdinfo').iterdir());drm={}
    for fd in fds:
        try:fields=dict(line.split(':',1) for line in fd.read_text().splitlines() if ':' in line)
        except FileNotFoundError:continue
        fields={k:v.strip() for k,v in fields.items()}
        if 'drm-client-id' in fields:
            key=fields.get('drm-pdev','')+':'+fields['drm-client-id']
            drm[key]={k:v for k,v in fields.items() if k.startswith(('drm-total-','drm-resident-','drm-memory-','drm-shared-','drm-active-','drm-purgeable-'))}
    return dict(pid=pid,start=int(stat[19]),ticks=int(stat[11])+int(stat[12]),threads=int(stat[17]),
                pss_kib=memory['Pss'],uss_kib=sum(memory.get(k,0) for k in ('Private_Clean','Private_Dirty','Private_Hugetlb')),
                swap_pss_kib=memory.get('SwapPss'),fds=len(fds),maps=sum(1 for _ in base.joinpath('maps').open()),drm=drm)


def ipc(*argv):
    try:
        p=subprocess.run(['omarchy-shell',*argv],text=True,capture_output=True,timeout=3,
                         env={**os.environ,'OMARCHY_SHELL_IPC_TIMEOUT':'2s'})
        if p.returncode:return {'ipc_error':p.returncode}
        try:return json.loads(p.stdout)
        except ValueError:return {'ipc_error':'invalid-json'}
    except (OSError,subprocess.TimeoutExpired):return {'ipc_error':'unavailable'}


def writer_events(since, shell_pid):
    # Read only journal lines from this process; retain only our numeric exit
    # diagnostics. Qt warnings can contain private paths, so never copy raw text.
    p=subprocess.run(['journalctl','--user','--since','@'+str(since),'--no-pager','-o','json',
                      '_PID='+str(shell_pid),
                      '--grep','WULING notification writer (started|exited):'],text=True,capture_output=True,timeout=5)
    result=[]
    for line in p.stdout.splitlines():
        try:
            row=json.loads(line);message=row.get('MESSAGE','')
            # journald encodes messages containing control bytes (including
            # Qt's coloured console prefix) as a JSON byte array.
            if isinstance(message,list) and all(type(b) is int and 0<=b<=255 for b in message):
                message=bytes(message).decode('utf-8','replace')
            if not isinstance(message,str):continue
            start=re.search(r'WULING notification writer started: (\d+)',message)
            end=re.search(r'WULING notification writer exited: (-?\d+)(?: pid=(\d+))?',message)
            if start or end:result.append({'time_us':row.get('__REALTIME_TIMESTAMP'),'shell_pid':row.get('_PID'),
                'event':'start' if start else 'exit','writer_pid':int(start[1]) if start else int(end[2]) if end[2] else None,
                'exit_code':None if start else int(end[1])})
        except ValueError:continue
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shell-pid',type=int,required=True)
    parser.add_argument('--compositor-pid',type=int,required=True)
    parser.add_argument('--seconds',type=float,default=86400)
    parser.add_argument('--interval',type=float,default=10)
    args=parser.parse_args()
    if args.seconds<0 or args.interval<1:parser.error('seconds >= 0 and interval >= 1 required')
    def emit(kind,**values):print(json.dumps(dict(kind=kind,time=time.time(),**values)),flush=True)
    shell=Path('/proc')/str(args.shell_pid);words=shell.joinpath('cmdline').read_bytes().split(b'\0')
    if b'/usr/share/omarchy/shell' not in words:raise SystemExit('PID is not the installed Omarchy shell')
    if Path('/proc',str(args.compositor_pid),'comm').read_text().strip()!='Hyprland':raise SystemExit('PID is not Hyprland')
    starts={name:process(pid)['start'] for name,pid in [('shell',args.shell_pid),('compositor',args.compositor_pid)]}
    begin=time.monotonic();hz=os.sysconf('SC_CLK_TCK');previous={};journal_at=time.time();seen=set();events=0;unhealthy=0
    emit('start',seconds=args.seconds,interval=args.interval,hz=hz,starts=starts)
    index=0
    while True:
        due=min(args.seconds,index*args.interval);time.sleep(max(0,begin+due-time.monotonic()))
        now=time.monotonic();samples={}
        try:
            for name,pid in [('shell',args.shell_pid),('compositor',args.compositor_pid)]:
                value=process(pid)
                if value['start']!=starts[name]:raise RuntimeError(name+' identity changed')
                old=previous.get(name);value['cpu_percent']=None if old is None else (value['ticks']-old['ticks'])/hz/(now-old['at'])*100
                previous[name]={'ticks':value['ticks'],'at':now};samples[name]=value
        except (OSError,RuntimeError) as exc:
            emit('abort',reason=type(exc).__name__,elapsed=now-begin);raise SystemExit(2)
        writer=ipc('wuling.notifications','writer')
        if writer.get('status')!='running':unhealthy+=1
        observed=writer_events(journal_at,args.shell_pid);journal_at=time.time()-1
        for event in observed:
            key=(event['time_us'],event['shell_pid'],event['event'],event['exit_code'])
            if key in seen:continue
            seen.add(key);events+=event['event']=='exit';emit('writer-event',**event)
        # Bound de-duplication to the overlapping one-second journal window.
        seen={key for key in seen if int(key[0] or 0)>=int((journal_at-2)*1000000)}
        emit('sample',index=index,elapsed=now-begin,processes=samples,writer=writer)
        if due==args.seconds:break
        index+=1
    emit('complete',elapsed=time.monotonic()-begin,writer_exit_events=events,unhealthy_samples=unhealthy)


if __name__=='__main__':main()
