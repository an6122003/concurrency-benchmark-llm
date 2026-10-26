"""earshot's reading of the ElevenLabs takes: the two scores (sections, beat grid, loudness) and, for each effect,
which of its two takes matches its description best and its cleanest trim. Writes audio/listen.json."""
import json
import sys
from pathlib import Path

from earshot import api

HERE = Path(__file__).resolve().parent
EL = HERE / 'eleven'
ROLES = {   # query, realistic confusions
    'whoosh': ('a fast clean air whoosh passing by', ['a gust of wind', 'a car passing by', 'a sword swish']),
    'impact': ('a deep soft sub boom impact', ['a door slam', 'a bass drum hit', 'thunder']),
    'pop': ('a soft rounded pop, like a small bubble', ['a mouse click', 'a cork pop', 'a water drop']),
    'tick': ('a tiny crisp digital tick', ['a clock ticking', 'a mouse click', 'a typewriter key']),
    'typing': ('fast typing on a quiet laptop keyboard', ['a mechanical keyboard', 'a typewriter', 'rain on a window']),
    'chime': ('a short bright two-note chime, glassy bell tones', ['a doorbell', 'a piano chord', 'a phone ringtone']),
    'blip': ('a quick soft digital chirp, a glassy data blip', ['a bird chirp', 'a phone notification', 'a laser zap']),
    'riser': ('an airy synth riser building up', ['a jet engine', 'wind howling', 'a siren']),
    'note': ('a single soft felt piano note with a long natural decay', ['a guitar note', 'a bell', 'an organ chord']),
    'click': ('a single crisp mouse click', ['a keyboard key', 'a pen click', 'a light switch']),
}


def main():
    out = {'music': {}, 'sfx': {}}
    for k in ('music_a', 'music_b'):
        p = str(EL / f'{k}.mp3')
        tl = api.timeline(p, detail='normal')
        out['music'][k] = tl
        print(f'== {k}\n', (tl.get('summary') or '')[:1500], flush=True)
    for role, (q, alts) in ROLES.items():
        res = {}
        for take in ('a', 'b'):
            p = str(EL / f'{role}_{take}.mp3')
            m = api.match(p, q, alts=alts)
            f = api.find(p, q, top=1)
            res[take] = {'match': m, 'find': f}
            z = m.get('z') if isinstance(m, dict) else None
            print(f'{role}_{take}: z={z} summary={(m.get("summary") if isinstance(m, dict) else "")!s:.200}', flush=True)
        out['sfx'][role] = res
    (HERE / 'listen.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print('wrote', HERE / 'listen.json')


if __name__ == '__main__':
    sys.exit(main())
