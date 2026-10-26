"""The soundtrack: the ElevenLabs score under the film, the effects on its cues, mastered for delivery.

    $env:Path = '..\\tools\\ffmpeg\\bin;' + $env:Path
    ..\\earshot\\.venv\\Scripts\\python.exe audio\\mix.py           ->  out\\soundtrack.wav (48 kHz, 24-bit) + out\\mix.json
    ..\\earshot\\.venv\\Scripts\\python.exe audio\\mix.py quick     ->  out\\soundtrack-quick.wav + out\\mix-quick.json
    ..\\earshot\\.venv\\Scripts\\python.exe audio\\mix.py evo       ->  out\\soundtrack-evo.wav (the NEON SPARK cut)

The film enters the score (music_b) 4.0 s in, so its drop lands on the title. The quick cut plays the score's own cut
of it (the cues file's "score": segments in track seconds, joined on their downbeats with a 30 ms crossfade). Every
effect sits on its cue (out\\cues-h.json or out\\cues-v-quick.json, written by render.ps1) the way earshot's launch
kit places that role: aligned on its onset or its peak, offset against the cut, and bed_db over the music's level in
the second before the cue (earshot.forge.kit.bed_level / gain_db, never over -1 dBFS at its own peak). The music
steps down before the impacts and comes back on them; nothing else ducks. Master: -14 LUFS integrated, true peak at
most -1.5 dBTP, which leaves room for the AAC encode.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

from earshot import audio, features
from earshot.forge import bank, kit

ROOT = Path(__file__).resolve().parent.parent
EL = ROOT / 'audio' / 'eleven'
OUT = ROOT / 'out'
SR = kit.SR
START, DUR = 4.0, 72.0          # where the film enters the score, and its length
LUFS, CEIL = -14.0, -1.5
# each cut: its cues, its outputs, and how its score fades in and out (s)
CUTS = {'film': {'cues': 'cues-h.json', 'out': 'soundtrack.wav', 'report': 'mix.json', 'fade': (0.25, 1.0)},
        'quick': {'cues': 'cues-v-quick.json', 'out': 'soundtrack-quick.wav', 'report': 'mix-quick.json',
                  'fade': (0.03, 0.3)},
        'evo': {'cues': 'cues-v-evo.json', 'out': 'soundtrack-evo.wav', 'report': 'mix-evo.json',
                'fade': (0.03, 1.2)}}
# cue kind -> its role, after earshot's launch kit (align, offset_ms, bed_db, min_gap_ms); max_s trims a take, and
# level_db is the fallback where the score is silent. Two takes alternate where a role comes in runs.
ROLES = {
    'impact': {'takes': ['impact_b'], 'align': 'onset', 'offset_ms': 0, 'bed_db': 7.5, 'max_s': 2.5, 'level_db': -6.0},
    'whoosh': {'takes': ['whoosh_a'], 'align': 'peak', 'offset_ms': 37, 'bed_db': 9.0, 'max_s': 1.2, 'level_db': -6.0},
    'tick': {'kit': 'tick', 'align': 'onset', 'offset_ms': 0, 'bed_db': 3.0, 'min_gap_ms': 66, 'level_db': -12.0},
    'typing': {'takes': ['typing_b'], 'align': 'onset', 'offset_ms': 8, 'bed_db': 6.5, 'max_s': 1.3, 'level_db': -8.0},
    'click': {'takes': ['click_a'], 'cut': 'peak', 'align': 'onset', 'offset_ms': -11, 'bed_db': 6.5, 'max_s': 0.4,
              'level_db': -8.0},
    'pop': {'takes': ['pop_a', 'pop_b'], 'align': 'onset', 'offset_ms': 4, 'bed_db': 8.5, 'max_s': 0.5,
            'min_gap_ms': 114, 'level_db': -8.0},
    'blip': {'takes': ['blip_b', 'blip_a'], 'align': 'onset', 'offset_ms': 0, 'bed_db': 4.0, 'max_s': 0.6,
             'min_gap_ms': 110, 'level_db': -10.0},
    'chime': {'takes': ['chime_b'], 'align': 'onset', 'offset_ms': 0, 'bed_db': 8.5, 'max_s': 1.6, 'level_db': -8.0},
    'note': {'takes': ['note_a'], 'align': 'onset', 'offset_ms': -20, 'bed_db': 7.5, 'max_s': 5.0, 'level_db': -8.0},
}
STOP_DOWN = {'before': ('impact',), 'depth_db': 12.0, 'length_s': 0.4}   # the music steps down, back on the hit


def ramp(n, up=True):
    r = np.sin(np.linspace(0, np.pi / 2, max(n, 1))) ** 2
    return r if up else r[::-1]


def measured(y):
    """the take as a kit lock row: its sync points, sample peak and loudest 50 ms (what place / gain_db read)"""
    row = bank.times(y)
    row['peak_db'] = round(float(20 * np.log10(np.abs(y).max() + 1e-12)), 2)
    row['l50_lufs'] = kit.loud_lufs(y)
    return row


def eleven_take(name, max_s, cut=None):
    """an ElevenLabs take from its first sound to its end (at most max_s), the cut faded out. cut='peak' keeps only
    its loudest moment: click_a is five clicks in half a second, and the Enter key is one of them"""
    y = audio.load(str(EL / f'{name}.mp3'))
    t = bank.times(y)
    if cut == 'peak':
        y = y[max(0, int((t['peak_s'] - 0.02) * SR)):int((t['peak_s'] + 0.06) * SR)].copy()
        a, b = int(0.004 * SR), int(0.03 * SR)
        y[:a] *= ramp(a)[:, None]
        y[-b:] *= ramp(b, up=False)[:, None]
        return {'file': f'{name}.mp3', 'y': y, **measured(y)}
    y = y[max(0, int((t['onset_s'] - 0.01) * SR)):]
    t = bank.times(y)
    n = int(min(t['end_s'] + 0.05, max_s) * SR)
    if n < len(y):
        y = y[:n].copy()
        f = min(n // 4, int(0.15 * SR))
        y[-f:] *= ramp(f, up=False)[:, None]
    return {'file': f'{name}.mp3', 'y': y, **measured(y)}


def kit_takes(role):
    lock = json.loads((ROOT / 'audio' / 'kit' / kit.LOCK).read_text(encoding='utf-8'))['roles'][role]
    return [{'file': f"kit/{t['file']}", 'y': audio.load(str(ROOT / 'audio' / 'kit' / t['file'])), **t}
            for t in lock['takes']]


def limit(x, ceiling_db, look_s=0.0015, release_s=0.08):
    """a true-peak limiter: the gain each sample needs (4x oversampled), held over a look-ahead window and averaged
    over it (so it is down before the peak arrives), then let back up with a release"""
    c = 10 ** (ceiling_db / 20)
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = up[:len(x) * 4].reshape(len(x), 4).max(axis=1)
    w = 2 * max(1, int(look_s * SR)) + 1
    g = uniform_filter1d(minimum_filter1d(np.minimum(1.0, c / np.maximum(pk, 1e-9)), w, mode='nearest'), w,
                         mode='nearest')
    a, cur, out = math.exp(-1.0 / (release_s * SR)), 1.0, np.empty_like(g)
    for i, v in enumerate(g):
        cur = v if v < cur else v + (cur - v) * a
        out[i] = cur
    return x * out[:, None].astype(x.dtype)


def score_bed(score, n):
    """the score as a cut plays it: its segments (track seconds) end to end, each join an equal-power crossfade of
    30 ms centred on the downbeat"""
    x = audio.load(str(EL / f"{score['take']}.mp3")).astype(np.float64)
    segs, h, parts = score['segments'], int(0.015 * SR), []
    for i, (a, b) in enumerate(segs):
        s, e = int(round(a * SR)) + (h if i else 0), int(round(b * SR)) - (h if i < len(segs) - 1 else 0)
        parts.append(x[s:e])
        if i < len(segs) - 1:
            nxt = int(round(segs[i + 1][0] * SR))
            th = np.linspace(0, np.pi / 2, 2 * h)[:, None]
            parts.append(x[e:e + 2 * h] * np.cos(th) + x[nxt - h:nxt + h] * np.sin(th))
    bed = np.concatenate(parts)[:n]
    return np.pad(bed, ((0, n - len(bed)), (0, 0)))


def main():
    cut = CUTS[sys.argv[1] if len(sys.argv) > 1 else 'film']
    cj = json.loads((OUT / cut['cues']).read_text(encoding='utf-8'))
    cues, dur = cj['cues'], float(cj.get('duration') or DUR)
    score = cj.get('score') or {'take': 'music_b', 'segments': [[START, START + dur]]}
    n = int(round(dur * SR))
    bed = score_bed(score, n)
    fi, fo = (int(f * SR) for f in cut['fade'])
    bed[:fi] *= ramp(fi)[:, None]
    bed[-fo:] *= ramp(fo, up=False)[:, None]

    takes = {k: (kit_takes(r['kit']) if 'kit' in r else [eleven_take(t, r['max_s'], r.get('cut')) for t in r['takes']])
             for k, r in ROLES.items()}
    times = {}
    for k in ROLES:   # runs keep their role's spacing
        times[k] = kit.space_run([c['t'] for c in cues if c['kind'] == k], ROLES[k].get('min_gap_ms'))
    rng = np.random.default_rng(7)
    fx = np.zeros((n, 2))
    env = np.ones(n)
    rows = []
    for k, ts in times.items():
        r, tk = ROLES[k], takes[k]
        for i, t in enumerate(ts):
            tkn = tk[i % len(tk)]
            try:
                bl = kit.bed_level(bed, t)
            except kit.KitError:
                bl = None
            jitter = float(rng.uniform(-0.75, 0.75)) if len(ts) > 2 else 0.0   # a run is never one level
            g = min(kit.gain_db(tkn, r, bl) + jitter, -1.0 - tkn['peak_db'])
            s = kit.place(tkn, r, t)
            a, y = int(round(s * SR)), tkn['y'].astype(np.float64) * 10 ** (g / 20)
            if a < 0:
                y, a = y[-a:], 0
            y = y[:max(0, n - a)]
            fx[a:a + len(y)] += y
            rows.append({'t': round(t, 3), 'kind': k, 'file': tkn['file'], 'start': round(s, 3),
                         'bed_lufs': bl, 'gain_db': round(g, 2)})
            if k in STOP_DOWN['before']:   # down over 80 ms, held, back up on the hit
                d, L = 10 ** (-STOP_DOWN['depth_db'] / 20), STOP_DOWN['length_s']
                b0, b1, h = int((t - L) * SR), int((t - L + 0.08) * SR), int(t * SR)
                env[b0:b1] = np.minimum(env[b0:b1], 1 - (1 - d) * ramp(b1 - b0))
                env[b1:h - int(0.015 * SR)] = np.minimum(env[b1:h - int(0.015 * SR)], d)
                e0 = h - int(0.015 * SR)
                env[e0:h] = np.minimum(env[e0:h], d + (1 - d) * ramp(h - e0))
    mix = bed * env[:, None] + fx
    pre = features.integrated_lufs(mix)
    mix *= 10 ** ((LUFS - pre) / 20)
    tp0 = features.true_peak_dbtp(mix)
    ceiling, tp = CEIL, tp0
    for _ in range(4):
        if tp <= CEIL:
            break
        mix = limit(mix, ceiling)
        tp = features.true_peak_dbtp(mix)
        ceiling -= 0.2
    import soundfile as sf
    sf.write(str(OUT / cut['out']), mix.astype(np.float32), SR, subtype='PCM_24')
    rows.sort(key=lambda r: r['t'])
    rep = {'integrated_lufs': round(features.integrated_lufs(mix), 2), 'true_peak_dbtp': round(tp, 2),
           'true_peak_before_limit': round(tp0, 2), 'lra_lu': features.lra(mix), 'effects': len(rows),
           'per_10s': round(len(rows) / dur * 10, 1), 'score': score, 'placed': rows}
    (OUT / cut['report']).write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'placed'}))
    for r_ in rows:
        print(f"{r_['t']:7.3f} {r_['kind']:7s} {r_['file']:16s} start {r_['start']:7.3f}  bed {r_['bed_lufs']}  "
              f"gain {r_['gain_db']:+.1f} dB")


if __name__ == '__main__':
    main()
