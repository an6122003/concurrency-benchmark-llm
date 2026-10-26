import json
import sys
from pathlib import Path

lj = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
m = lj['music']['music_b']
print('duration', m.get('duration'), m.get('file_duration'))
for s in m.get('sections') or []:
    print('section', json.dumps({k: v for k, v in s.items() if not isinstance(v, (list, dict))})[:300])
loud = m.get('loudness') or {}
print('loudness keys', list(loud.keys()))
print('silences', loud.get('silences'))
st = loud.get('short_term') or {}
if st:
    t0, dt, L = st['t0'], st['dt'], st['lufs']
    print('short-term LUFS (3 s windows) every 1 s:', [(round(t0 + i * dt, 1), L[i]) for i in range(0, len(L), 2)])
mo = loud.get('momentary') or {}
if mo:
    t0, dt, L = mo['t0'], mo['dt'], mo['lufs']
    for a, b in ((27.5, 33.5), (59.5, 66.0), (5.0, 9.0), (70.0, 76.0)):
        seg = [(round(t0 + i * dt, 1), L[i]) for i in range(len(L)) if a <= t0 + i * dt <= b]
        print(f'momentary {a}-{b}:', seg[::2])
print('summary:', (m.get('summary') or '')[:1500])
