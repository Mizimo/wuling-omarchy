#!/usr/bin/env python3
"""Stream read-only process observations; explicit IPC exercise is a separate mode.

Run over SSH from stdin, redirecting stdout to a private local JSONL file.
No remote files are written. Raw inventory must not be committed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

SHELL_PATH = '/usr/share/omarchy/shell'
parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['inventory', 'idle', 'exercise'])
parser.add_argument('--shell-pid', type=int, required=True)
parser.add_argument('--compositor-pid', type=int, required=True)
args = parser.parse_args()
pids = {'shell': args.shell_pid, 'compositor': args.compositor_pid}
env = dict(x.split('=', 1) for x in Path(f'/proc/{args.shell_pid}/environ').read_bytes().decode().strip('\0').split('\0') if '=' in x)
hz = os.sysconf('SC_CLK_TCK')

def emit(kind, **data):
    print(json.dumps(dict(kind=kind, time=time.time(), **data)), flush=True)

def run(argv, strict=True):
    p = subprocess.run(argv, env=env, text=True, capture_output=True, timeout=20)
    if strict and p.returncode:
        raise RuntimeError(f'command failed: {argv[:3]}: rc={p.returncode}: {p.stderr}')
    return dict(argv=argv, rc=p.returncode, stdout=p.stdout, stderr=p.stderr)

def ipc(target, method, *params):
    return run(['quickshell', '-p', SHELL_PATH, 'ipc', 'call', target, method, *params])['stdout'].strip()

def stat(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return {'ticks': int(fields[11]) + int(fields[12]), 'start': int(fields[19]), 'threads': int(fields[17])}

starts = {name: stat(pid)['start'] for name, pid in pids.items()}
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()

def guard():
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip() == boot, 'boot changed'
    for name, pid in pids.items():
        assert stat(pid)['start'] == starts[name], f'{name} identity changed'
    idle = json.loads(ipc('idle', 'status'))
    lock = json.loads(ipc('lock', 'status'))
    assert idle['stayAwake'] is True and idle['enabled'] is False, 'original stay-awake changed'
    for key in ['locked', 'requested', 'pending', 'sessionLocked', 'secure', 'authenticating']:
        assert not lock.get(key, False), f'lock condition: {key}'
    assert not any(v for k, v in lock.items() if 'locked' in k.lower() and isinstance(v, bool)), 'lock state'
    return dict(idle=idle, lock=lock)

def settings():
    config = Path.home()/'.config/omarchy/shell.json'
    theme_name = Path.home()/'.local/state/omarchy/current/theme.name'
    return {'shellConfigSha256': hashlib.sha256(config.read_bytes()).hexdigest(),
            'themeName': theme_name.read_text().strip(),
            'themeNameSha256': hashlib.sha256(theme_name.read_bytes()).hexdigest()}

def layers():
    raw = json.loads(run(['hyprctl', 'layers', '-j'])['stdout'])
    return [dict(namespace=x['namespace'], pid=x.get('pid'), w=x['w'], h=x['h'], alpha=x.get('alpha'))
            for monitor in raw.values() for items in monitor['levels'].values() for x in items
            if x.get('pid') == args.shell_pid]

def memory(pid):
    roll = {}
    for line in Path(f'/proc/{pid}/smaps_rollup').read_text().splitlines():
        m = re.match(r'^(\w+):\s+(\d+)\s+kB$', line)
        if m: roll[m[1]] = int(m[2])
    drm = {}
    fds = list(Path(f'/proc/{pid}/fdinfo').iterdir())
    for fd in fds:
        try: content = fd.read_text()
        except FileNotFoundError: continue
        fields = dict(line.split(':', 1) for line in content.splitlines() if ':' in line)
        fields = {k: v.strip() for k, v in fields.items()}
        if 'drm-client-id' not in fields: continue
        key = fields.get('drm-pdev', '') + ':' + fields['drm-client-id']
        metrics = {k: v for k, v in fields.items() if k.startswith(('drm-memory-', 'drm-total-', 'drm-resident-', 'drm-shared-', 'drm-active-', 'drm-purgeable-'))}
        # Duplicate fds can point to one DRM client. Keep one, never sum them.
        drm[key] = dict(driver=fields.get('drm-driver'), metrics=metrics)
    return dict(pssKiB=roll['Pss'], ussKiB=sum(roll.get(k, 0) for k in ['Private_Clean', 'Private_Dirty', 'Private_Hugetlb']),
                rssKiB=roll['Rss'], swapPssKiB=roll.get('SwapPss'), fdCount=len(fds), drm=drm, **stat(pid))

def sample(phase, **extra):
    state = guard()
    emit('sample', phase=phase, monotonic=time.monotonic(), processes={name: memory(pid) for name, pid in pids.items()}, guard=state, **extra)

cmdline = Path(f'/proc/{args.shell_pid}/cmdline').read_bytes().decode().split('\0')
assert '-p' in cmdline and cmdline[cmdline.index('-p') + 1] == SHELL_PATH, 'unexpected shell'
assert Path(f'/proc/{args.compositor_pid}/comm').read_text().strip() == 'Hyprland', 'unexpected compositor'
initial = settings()
emit('start', controllerPid=os.getpid(), mode=args.mode, pids=pids, starts=starts, clockTicksPerSecond=hz, settings=initial, guard=guard(), layers=layers())
if args.mode == 'inventory':
    commands = {
        'packages': ['pacman', '-Q'],
        'kernel': ['uname', '-r'],
        'monitors': ['hyprctl', 'monitors', '-j'],
        'plugins': ['omarchy', 'plugin', 'list'],
        'fonts': ['fc-list', ':', 'family'],
        'audio': ['wpctl', 'status'],
        'pwPlay': ['bash', '-c', 'command -v pw-play'],
        'boot': ['systemd-analyze'],
        'bootBlame': ['systemd-analyze', 'blame', '--no-pager'],
        'bootCriticalChain': ['systemd-analyze', 'critical-chain', '--no-pager'],
        'ipc': ['quickshell', '-p', SHELL_PATH, 'ipc', 'show'],
        'graphics': ['lspci', '-nn'],
    }
    for name, command in commands.items():
        result = run(command, strict=False)
        if name == 'packages':
            result['stdout'] = '\n'.join(line for line in result['stdout'].splitlines() if re.match(r'^(omarchy|hyprland|quickshell|mesa|linux|qt6-base|qt6-declarative)(?:\s|[-])', line))
        if name == 'fonts':
            result['stdout'] = '\n'.join(sorted(set(line for line in result['stdout'].splitlines() if re.search('Geist|Barlow|Noto.*CJK|Material.*Symbols', line, re.I))))
        if name == 'graphics':
            result['stdout'] = '\n'.join(line for line in result['stdout'].splitlines() if re.search(r': (VGA compatible|3D|Display) controller', line))
        emit('inventory', name=name, result=result)
    emit('config', shell=json.loads((Path.home()/'.config/omarchy/shell.json').read_text()), theme=initial['themeName'])
    sample('inventory')
elif args.mode == 'idle':
    # Require only the normal background/bar; never dismiss existing owner UI.
    assert {x['namespace'] for x in layers()} <= {'omarchy-background', 'omarchy-bar'}, 'pre-existing shell popup'
    baseline_layers = layers()
    layer_geometry = lambda rows: sorted((x['namespace'], x['w'], x['h']) for x in rows)
    begin = time.monotonic()
    for i in range(91):
        delay = begin + i * 10 - time.monotonic()
        if delay > 0: time.sleep(delay)
        current_layers = layers()
        if layer_geometry(current_layers) != layer_geometry(baseline_layers):
            emit('abort', reason='shell layer set or geometry changed during idle', layers=current_layers)
            raise RuntimeError('shell layer set or geometry changed during idle')
        sample('idle', index=i, elapsed=time.monotonic()-begin, layers=current_layers)
        if i % 6 == 0: emit('progress', index=i, elapsed=time.monotonic()-begin)
else:
    def interrupted(signum, frame):
        raise SystemExit(f'controller interrupted by signal {signum}')
    for signum in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]:
        signal.signal(signum, interrupted)
    # Only these explicit, reversible popup operations are permitted.
    # A pre-existing popup is never hidden to make room for the test.
    normal = {'omarchy-background', 'omarchy-bar'}
    assert {x['namespace'] for x in layers()} <= normal, 'pre-existing shell popup'
    interface = run(['quickshell', '-p', SHELL_PATH, 'ipc', 'show'])['stdout']
    targets = {}
    target = None
    for line in interface.splitlines():
        if line.startswith('target '):
            target = line.split()[1]
            targets[target] = []
        elif target and 'function ' in line:
            targets[target].append(line.strip().split('function ', 1)[1].split('(', 1)[0])
    assert {'summon', 'hide'} <= set(targets.get('shell', []))
    assert {'open', 'close'} <= set(targets.get('omarchy.clock', []))
    emit('exerciseInterface', targets={k: targets[k] for k in ['shell', 'omarchy.clock']})

    def verify_surface(namespace, present):
        deadline = time.monotonic() + 5
        while True:
            observed = layers()
            names = {x['namespace'] for x in observed}
            assert names <= normal | {namespace, 'omarchy-keyboard-panel-dismiss'}, 'unexpected shell popup'
            matching = [x for x in observed if x['namespace'] == namespace and x['w'] > 0 and x['h'] > 0 and x.get('alpha', 1) > 0]
            if bool(matching) == present:
                return observed
            if time.monotonic() >= deadline:
                raise RuntimeError(f'surface failed to become {present}: {namespace}')
            time.sleep(0.1)

    for component, namespace, opening, closing in [
        ('menu', 'omarchy-menu', ('shell', 'summon', 'omarchy.menu', '{"menu":"root"}'), ('shell', 'hide', 'omarchy.menu')),
        ('clock', 'omarchy-keyboard-panel', ('omarchy.clock', 'open'), ('omarchy.clock', 'close')),
    ]:
        sample('component-before', component=component)
        armed = False
        try:
            for cycle in range(1, 11):
                assert {x['namespace'] for x in layers()} <= normal, 'popup present before cycle'
                sample('cycle-before', component=component, cycle=cycle)
                armed = True
                result = ipc(*opening)
                observed = verify_surface(namespace, True)
                emit('transition', component=component, cycle=cycle, state='open', result=result, layers=observed)
                time.sleep(3)
                observed = verify_surface(namespace, True)
                sample('open', component=component, cycle=cycle, layers=observed)
                result = ipc(*closing)
                observed = verify_surface(namespace, False)
                armed = False
                emit('transition', component=component, cycle=cycle, state='closed', result=result, layers=observed)
                time.sleep(5)
                assert {x['namespace'] for x in layers()} <= normal, 'popup present after close'
                sample('closed', component=component, cycle=cycle)
            # A later point distinguishes immediate fade-out retirement from retention.
            time.sleep(30)
            sample('component-after-30s', component=component)
        finally:
            if armed:
                # Restore only the popup opened by this controller; never unlock,
                # restart a process, or change settings in an error handler.
                result = ipc(*closing)
                observed = verify_surface(namespace, False)
                emit('cleanup', component=component, result=result, layers=observed)

assert settings() == initial, 'settings changed during measurement'
emit('complete', mode=args.mode, settings=initial, guard=guard(), layers=layers())
