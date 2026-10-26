"""bench.json (+ bench_labs.json, + audio/listen.json) -> comp/data.js: every number the film shows.

bench.json is the full run (models, labs, three Enterprise batches, GPU sampled twice a second); bench_labs.json,
when present, is a second run of the models and labs with the machine otherwise idle, and its lab numbers win.
The music grid comes from earshot's beat tracking of the chosen score, shifted by where the film starts in it.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MUSIC_TAKE, MUSIC_START = 'music_b', 4.0   # the score earshot preferred, entered 4 s in so its drop lands at 4.0


def load(name):
    p = HERE / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


full, labs, warm = load('bench.json'), load('bench_labs.json'), load('bench_warm.json')
L = labs or full
LW = warm or L   # Labs 2 and 3 with every model already loaded, as in a live session


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def gpu_rows(b):  # the GPU's rows (the NPU's have no memory reading)
    return [g for g in b['gpu'] if g.get('mem_mb') is not None]


def phase(b, name):
    return next((p for p in b['phases'] if p['name'] == name), None)


def clean(text, words=34):
    t = re.sub(r'\*\*|__|`|#+ ', '', text or '')
    t = re.sub(r'(^|\n)\s*[-•]\s+', ' ', t).replace('\n', ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    w = t.split(' ')
    return ' '.join(w[:words]) + ('…' if len(w) > words else '')


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean(text, 400)) if s.strip()]


def first_and(text, must, cut=False):  # the first sentence, and the one that carries `must` (up to it, if cut)
    ss = sentences(text)
    hit = next((s for s in ss[1:] if must.lower() in s.lower()), '')
    if hit and cut:
        i = hit.lower().index(must.lower()) + len(must)
        hit = hit[:i] + ('…' if i < len(hit) else '')
    return ' '.join(ss[:1] + ([hit] if hit else []))


D = {}
# ---- models
runs = L['ollama']['runs']
by = lambda m, k: [r for r in runs if r['model'].startswith(m) and r['kind'] == k]
# reading speed only from a cold prompt: a run whose prompt Ollama had cached evaluates a handful of tokens
cold = max((r for b in (full, labs) if b for r in b['ollama']['runs']
            if r['model'].startswith('nemotron') and r['kind'] == 'long_prompt'), key=lambda r: r['prompt_tokens'] or 0)
D['ollama'] = {
    'nemotron': {'gen': round(mean(r['gen_tps'] for r in by('nemotron', 'short')), 1),
                 'prompt': round(cold['prompt_tps']), 'prompt_tokens': cold['prompt_tokens']},
    'qwen': {'gen': round(mean(r['gen_tps'] for r in by('qwen2.5', 'short')))},
    'aurora': {'gen': round(mean(r['gen_tps'] for r in by('aurora', 'short')))},
    'embed': round(mean(L['ollama']['embed_passages_per_s']), 1),
}
# ---- lab 1: the training run, its loss curve, the GPU's load while it trained
t1 = L['lab1_train']
ev = t1['events']
loss = [[e['step'], round(e['loss'], 4)] for e in ev if e.get('stage') == 'train' and 'loss' in e and 'step' in e]
p1 = phase(L, 'lab1_train')
tr_t = [e.get('_t', 0) for e in ev if e.get('stage') == 'train']
util = []
if tr_t and p1:
    a, b = p1['start'] + min(tr_t), p1['start'] + max(tr_t)
    util = [g['util'] for g in gpu_rows(L) if a <= g['t'] <= b]
info = t1.get('info_after') or {}
cmp_ = {'base': '', 'tuned': ''}
for e in L['lab1_compare']:
    if e.get('side') in cmp_:
        cmp_[e['side']] += e.get('text', '')
util = [u for u in util if u >= 30]   # the seconds the GPU was training, not loading
D['lab1'] = {'steps': info.get('steps', len(loss)), 'train_s': round(info.get('train_seconds') or 0),
             'total_s': round(info.get('total_seconds') or 0), 'loss': loss,
             'util': [round(u) for u in util][::max(1, len(util) // 60)] if util else [],
             'question': 'Who built you, and what are you for?',
             'before': ' '.join(sentences(cmp_['base'])[:1]),
             'after': first_and(cmp_['tuned'], 'RTX Spark')}
# ---- lab 2: without and with the documents
plain = ''.join(e.get('text', '') for e in LW['lab2_plain'] if 'event' not in e or e.get('event') != '_stream')
rag = next((e for e in LW['lab2_rag'] if e.get('event') == 'answer'), {})
ret = next((e for e in LW['lab2_rag'] if e.get('event') == 'retrieved'), {})
gen = next((e for e in LW['lab2_rag'] if e.get('event') == 'step' and e.get('id') == 'generate'), {})
st2 = next((e for e in LW['lab2_rag'] if e.get('event') == '_stream'), {})
stp = next((e for e in LW['lab2_plain'] if e.get('event') == '_stream'), {})
docs = sorted({s['doc'] for s in ret.get('sources', [])} | {f'doc-{i:02d}' for i in range(28)})
hits = []
for i, s in enumerate(ret.get('sources', [])):  # where each passage sits on the library's ring of 82
    m = re.search(r'doc-(\d+)', s.get('doc', ''))
    k = int(m.group(1)) if m else i * 5
    h = min(81, round((k - 1) * 82 / 28) + i % 3)
    while h in hits:
        h = (h + 1) % 82
    hits.append(h)
answer = rag.get('answer', '') or ''
bulletins = sorted(re.findall(r'sb-(\d{4}-\d{2})', ' '.join(s.get('doc', '') for s in ret.get('sources', [])), re.I))
D['lab2'] = {'question': 'How long after opening the DC disconnect must I wait before removing a module cover?',
             'plain': ' '.join(sentences(plain)[:1]),
             'rag': first_and(re.sub(r'\s*\([^)]*\)\s*$', '', answer), 'withdrawn', cut=True),
             'source': f'SB-{bulletins[-1]}' if bulletins else '', 'hits': sorted(hits),   # the newest bulletin it found
             't_embed_ms': round((gen.get('_t') or 0) * 1000), 't_total': round(st2.get('total_s') or 0, 1),
             't_plain': round(stp.get('total_s') or 0, 1)}
# ---- lab 3: the agent's tool calls and its chart
ev3 = LW['lab3']
calls, regions, last_llm = [], [], 0
for e in ev3:
    if e.get('event') == 'llm_done':
        last_llm = e.get('seconds') or 0
    if e.get('event') == 'tool_call':
        a = e.get('args') or {}
        arg = {'create_chart': a.get('chart_type'), 'export_excel_report': 'Excel'}.get(e['name'], a.get('group_by')) or ''
        calls.append({'name': e['name'], 'arg': arg, 'ms': round(last_llm * 1000)})
    if e.get('event') == 'tool_result':
        if calls and calls[-1]['name'] == e.get('name'):
            calls[-1]['ms'] += round((e.get('seconds') or 0) * 1000)
        tab = ((e.get('ui') or {}).get('table') or {})
        if tab.get('rows') and not regions:
            for r in tab['rows']:
                nums = [float(x.split()[0].replace(',', '')) for x in r[1:3]]
                regions.append({'name': r[0], 'a': nums[0], 'b': nums[1]})
st3 = next((e for e in ev3 if e.get('event') == '_stream'), {})
D['lab3'] = {'question': 'Analyse sales by region and tell me which region grew the most.', 'calls': calls[:4],
             'regions': sorted(regions, key=lambda r: -r['b'])[:4], 'total_s': round(st3.get('total_s') or 0, 1)}
# ---- enterprise (the full run)
ent = {}
for k, e in (full.get('ent') or {}).items():
    f = e['final']
    acc = f.get('accuracy') or {}
    head = {'inbox': acc.get('category'), 'invoices': mean(acc.values()), 'calls': acc.get('checklist')}.get(k)
    ent[k] = {'n': f.get('processed'), 'rate': f.get('rate_per_min'), 'acc': round(head or 0, 1),
              'wh': (f.get('totals') or {}).get('wh'), 'asr': acc.get('asr')}
D['ent'] = ent
# ---- the GPU through the full run
rows = gpu_rows(full)
names = {'ollama': 'Models', 'lab1_train': 'Fine-tune', 'lab2_rag': 'RAG', 'lab3_agent': 'Agent',
         'ent_inbox': 'Inbox', 'ent_invoices': 'Invoices', 'ent_calls': 'Calls'}
t_end = rows[-1]['t']
step = max(1, len(rows) // 420)
ent_rows = [g for g in rows if any(p['name'].startswith('ent_') and p['start'] <= g['t'] <= p['end'] for p in full['phases'])]
D['gpu'] = {'series': [[round(g['t'], 1), g['util'], g['power_w']] for g in rows[::step]],
            'phases': [{'start': p['start'], 'label': names[p['name']]} for p in full['phases'] if p['name'] in names],
            'minutes': round(t_end / 60), 'peak_util': max(g['util'] for g in rows),
            'peak_power': round(max(g['power_w'] for g in rows)), 'peak_temp': round(max(g['temp_c'] for g in rows)),
            'idle_power': round(mean(g['power_w'] for g in rows[:12]), 1),
            'ent_power': round(mean(g['power_w'] for g in ent_rows)) if ent_rows else None,
            'peak_mem_gb': round(max(g['mem_mb'] for g in rows) / 1024, 1)}
# ---- what sits in memory: Ollama's models, and the batch engine at its peak
# (nvidia-smi's memory reading on this unified-memory chip does not see the batch engine, so: Ollama's own sizes,
# and the engine's weights on disk; both were loaded together through the Enterprise batches)
PRETTY = {'nemotron-3.5-lightning': 'Nemotron 3.5 Lightning 30B', 'qwen3-embedding': 'qwen3-embedding 4B',
          'qwen2.5': 'Qwen2.5 1.5B', 'aurora-assistant': 'Aurora (fine-tuned)'}
ps = full['ollama_ps'].get('models', [])
models = [{'name': PRETTY.get(m['name'].split(':')[0], m['name']), 'gb': round(m.get('size_vram', 0) / 1e9, 1)} for m in ps]
batch_dir = Path.home() / 'ai-workshop' / '.run' / 'models' / 'batch'
engine_gb = round(sum(f.stat().st_size for f in batch_dir.glob('*.gguf')) / 1e9, 1)
if engine_gb:
    models.append({'name': 'Qwen3.6 35B · batch engine', 'gb': engine_gb})
D['mem'] = {'models': sorted(models, key=lambda m: -m['gb']), 'total_gb': 128}
D['install'] = {'first_min': 35, 'gb': 58, 'update_min': 1.5}
# ---- the music grid, in film time
lj = json.loads((ROOT / 'audio' / 'listen.json').read_text(encoding='utf-8'))
beats = lj['music'][MUSIC_TAKE]['music']['beats']
drop = min(range(len(beats)), key=lambda i: abs(beats[i] - (MUSIC_START + 4.0)))   # the beat nearest the drop
db = [beats[i] - MUSIC_START for i in range(drop % 4, len(beats), 4)]
k0 = db.index(beats[drop] - MUSIC_START)
bars = [round(4.0 + 2.0 * (n - 2), 3) for n in range(0, 2)] + [round(t, 3) for t in db[k0:]]
while len(bars) < 40:
    bars.append(round(bars[-1] + 2.0, 3))
D['music'] = {'take': MUSIC_TAKE, 'start': MUSIC_START, 'bar': 2.0, 'offset': 0.0, 'downbeats': bars[:40]}
# ---- the quick cut (TikTok, 38 s): the score from the bar before its drop to its first break, joined on the
# downbeat to its last break (the same bar of the arrangement), then its peak and its fade
QUICK_END = 38.0
tdb = [beats[i] for i in range(drop % 4, len(beats), 4)]   # the score's own downbeats
k0 = tdb.index(beats[drop]) - 1
ka = min(range(len(tdb)), key=lambda i: abs(tdb[i] - 30.0))
kb = min(range(len(tdb)), key=lambda i: abs(tdb[i] - 62.0))
lead = tdb[ka] - tdb[k0]
D['quick'] = {'take': MUSIC_TAKE, 'end': QUICK_END,
              'segments': [[tdb[k0], tdb[ka]], [tdb[kb], round(tdb[kb] + QUICK_END - lead, 3)]],
              'downbeats': [round(t - tdb[k0], 3) for t in tdb[k0:ka]] + [round(lead + t - tdb[kb], 3) for t in tdb[kb:]]}

out = ROOT / 'comp' / 'data.js'
out.write_text('window.DATA = ' + json.dumps(D, ensure_ascii=False, indent=1) + ';\n', encoding='utf-8')
print(json.dumps({k: (v if k not in ('gpu', 'lab1') else {kk: vv for kk, vv in v.items() if kk not in ('series', 'loss', 'util')}) for k, v in D.items()}, ensure_ascii=False, indent=1)[:4000])
