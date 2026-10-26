import json
from pathlib import Path

L = json.loads((Path(__file__).parent / 'listen.json').read_text(encoding='utf-8'))
m = L['music']['music_b']
mu = m['music']
print('music keys:', list(mu) if isinstance(mu, dict) else type(mu))
for k, v in (mu.items() if isinstance(mu, dict) else []):
    s = json.dumps(v)
    print(f'--- {k}:', s[:700])
mo = m['loudness']['momentary']
t0, dt, lu = mo['t0'], mo['dt'], mo['lufs']
print('--- loudness per second (momentary LUFS, mean):')
row = []
for sec in range(int(len(lu) * dt) + 1):
    vals = [v for i, v in enumerate(lu) if sec <= t0 + i * dt < sec + 1 and v is not None]
    if vals:
        row.append(f'{sec}:{sum(vals) / len(vals):.1f}')
print(' '.join(row))
print('--- sections:', [(s['start'], s['end'], s.get('label', '')[:40], s.get('lufs')) for s in m['sections']])
