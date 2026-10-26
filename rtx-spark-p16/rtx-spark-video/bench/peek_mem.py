import json
from pathlib import Path

b = json.loads((Path(__file__).parent / 'bench.json').read_text(encoding='utf-8'))
rows = [g for g in b['gpu'] if g.get('mem_mb') is not None]
for p in b['phases']:
    seg = [g['mem_mb'] / 1024 for g in rows if p['start'] <= g['t'] <= p['end']]
    if seg:
        print(f"{p['name']:14s} mem GB min {min(seg):5.1f}  median {sorted(seg)[len(seg)//2]:5.1f}  max {max(seg):5.1f}")
batch = Path.home() / 'ai-workshop' / '.run' / 'models' / 'batch'
for f in batch.glob('*.gguf'):
    print(f.name, round(f.stat().st_size / 1e9, 1), 'GB')
