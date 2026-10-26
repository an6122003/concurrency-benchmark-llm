import json
import sys
from pathlib import Path

warm = json.loads((Path(sys.argv[1]) / 'bench_warm.json').read_text(encoding='utf-8'))
for e in warm['lab2_rag']:
    if e.get('event') in ('retrieved', 'answer', 'sources', 'citations'):
        print(e.get('event'), json.dumps({k: v for k, v in e.items() if k not in ('answer',)}, ensure_ascii=False)[:2500])
print(sorted({e.get('event') for e in warm['lab2_rag']}))
