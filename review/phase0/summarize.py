#!/usr/bin/env python3
"""Aggregate a private W-0 JSONL capture without copying raw desktop inventory."""
import argparse
import json
from pathlib import Path
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()

def read(name):
    return [json.loads(line) for line in (args.directory/name).read_text().splitlines() if line.strip()]

def percentile(values, p):
    v = sorted(values)
    point = (len(v)-1)*p
    lo = int(point)
    hi = min(lo+1, len(v)-1)
    return v[lo] + (v[hi]-v[lo])*(point-lo)

def stats(values):
    return {'min': min(values), 'median': statistics.median(values), 'max': max(values),
            'mean': statistics.mean(values), 'p95': percentile(values, 0.95),
            'first': values[0], 'last': values[-1], 'lastMinusFirst': values[-1]-values[0]}

def kib(value):
    fields = value.split()
    if len(fields) == 1:
        assert float(fields[0]) == 0, 'unknown nonzero unit'
        return 0
    return float(fields[0])*{'KiB': 1, 'MiB': 1024, 'GiB': 1024**2, 'B': 1/1024}[fields[1]]

def metrics(process):
    result = {name: process[name+'KiB']/1024 for name in ['pss', 'uss', 'rss', 'swapPss']}
    result.update(fdCount=process['fdCount'], threads=process['threads'], drmClients=len(process['drm']))
    # Each region and accounting category stays separate. Cross-process shared
    # buffers are not deduplicated: do not add these metrics across processes.
    for client in process['drm'].values():
        for name, value in client['metrics'].items():
            result[name] = result.get(name, 0) + kib(value)/1024
    return result

rows = read('idle.jsonl')
assert rows[-1]['kind'] == 'complete', 'idle capture incomplete'
samples = [row for row in rows if row['kind'] == 'sample']
assert [row['index'] for row in samples] == list(range(91))
assert samples[-1]['elapsed']-samples[0]['elapsed'] >= 899.5
hz = rows[0]['clockTicksPerSecond']
report = {'idle': {'sampleCount': len(samples), 'durationSeconds': samples[-1]['monotonic']-samples[0]['monotonic'],
                   'startEpoch': samples[0]['time'], 'endEpoch': samples[-1]['time'], 'processes': {}}}
for role in ['shell', 'compositor']:
    series = [metrics(row['processes'][role]) for row in samples]
    keys = set(series[0])
    assert all(set(row) == keys for row in series), 'GPU metrics changed during capture'
    summary = {key: stats([row[key] for row in series]) for key in sorted(keys)}
    cpu = [100*(b['processes'][role]['ticks']-a['processes'][role]['ticks'])/hz/(b['monotonic']-a['monotonic'])
           for a, b in zip(samples, samples[1:])]
    summary['cpuPercentOneCore'] = stats(cpu)
    summary['cpuPercentOneCore']['weightedMean'] = 100*(samples[-1]['processes'][role]['ticks']-samples[0]['processes'][role]['ticks'])/hz/report['idle']['durationSeconds']
    report['idle']['processes'][role] = summary

if (args.directory/'exercise.jsonl').exists():
    rows = read('exercise.jsonl')
    assert rows[-1]['kind'] == 'complete', 'exercise capture incomplete'
    transitions = [row for row in rows if row['kind'] == 'transition']
    report['exercise'] = {}
    for component in ['menu', 'clock']:
        events = [row for row in transitions if row['component'] == component]
        assert [(row['cycle'], row['state']) for row in events] == [(i, state) for i in range(1, 11) for state in ['open', 'closed']]
        points = [row for row in rows if row['kind'] == 'sample' and row.get('component') == component]
        before = next(row for row in points if row['phase'] == 'component-before')
        after = next(row for row in points if row['phase'] == 'component-after-30s')
        result = {'verifiedOpens': 10, 'verifiedCloses': 10, 'processes': {}}
        for role in ['shell', 'compositor']:
            baseline = metrics(before['processes'][role]); final = metrics(after['processes'][role])
            cycles = []
            for cycle in range(1, 11):
                phase = {row['phase']: metrics(row['processes'][role]) for row in points if row.get('cycle') == cycle}
                cycles.append({'cycle': cycle, 'before': phase['cycle-before'], 'open': phase['open'], 'closed': phase['closed'],
                               'openDelta': {k: phase['open'][k]-phase['cycle-before'][k] for k in baseline},
                               'closedDelta': {k: phase['closed'][k]-phase['cycle-before'][k] for k in baseline}})
            result['processes'][role] = {'before': baseline, 'after30s': final,
                'after30sDelta': {k: final[k]-baseline[k] for k in baseline}, 'cycles': cycles,
                'warmOpenDelta': {k: stats([c['openDelta'][k] for c in cycles[1:]]) for k in baseline},
                'warmClosedDelta': {k: stats([c['closedDelta'][k] for c in cycles[1:]]) for k in baseline}}
        report['exercise'][component] = result
print(json.dumps(report, indent=2, sort_keys=True))
