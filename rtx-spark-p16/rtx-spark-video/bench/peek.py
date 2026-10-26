import json
from pathlib import Path

b = json.loads((Path(__file__).parent / 'bench.json').read_text(encoding='utf-8'))
print('keys:', list(b))
print('phases:', [(p['name'], p['start'], p['end']) for p in b['phases']])
print('gpu samples:', len(b['gpu']), b['gpu'][:2])
o = b['ollama']
print('ollama:', [(r['model'], r['kind'], r['gen_tps'], r['prompt_tps']) for r in o['runs']], 'embed:', o['embed_passages_per_s'])
print('ps:', [(m['name'], round(m.get('size_vram', 0) / 1e9, 1)) for m in b['ollama_ps'].get('models', [])])
ev = b['lab1_train']['events']
print('lab1 events:', len(ev))
print(' first:', ev[:3])
print(' kinds:', sorted({str(e.get('event') or e.get('stage') or list(e)[:3]) for e in ev}))
print(' last:', ev[-3:])
print('info_after:', b['lab1_train']['info_after'])
for k in ('lab1_compare', 'lab2_plain', 'lab2_rag', 'lab3'):
    evs = b.get(k, [])
    print('==', k, len(evs))
    for e in evs[:16]:
        print('  ', json.dumps(e, ensure_ascii=False)[:420])
