import json
import sys
from pathlib import Path

bench = Path(sys.argv[1])
labs = json.loads((bench / 'bench_labs.json').read_text(encoding='utf-8'))
warm = json.loads((bench / 'bench_warm.json').read_text(encoding='utf-8'))
cmp_ = {'base': '', 'tuned': ''}
for e in labs['lab1_compare']:
    if e.get('side') in cmp_:
        cmp_[e['side']] += e.get('text', '')
print('BASE:', repr(cmp_['base']))
print('TUNED:', repr(cmp_['tuned']))
plain = ''.join(e.get('text', '') for e in warm['lab2_plain'] if e.get('event') != '_stream')
print('PLAIN:', repr(plain))
rag = next((e for e in warm['lab2_rag'] if e.get('event') == 'answer'), {})
print('RAG:', repr(rag.get('answer')))
