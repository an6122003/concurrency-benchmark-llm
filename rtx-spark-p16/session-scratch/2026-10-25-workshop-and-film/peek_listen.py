import json
import re
import sys
from pathlib import Path

lj = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
for role, r in lj['sfx'].items():
    for take, v in r.items():
        s = (v.get('match') or {}).get('summary', '')
        m = re.search(r"-> (\w+).*?\(z ([+-][\d.]+)", s)
        like = re.search(r"It sounds most like: (.*?)\.", s)
        print(f"{role:7s} {take}: {m.group(1) if m else '?':10s} z {m.group(2) if m else '?':5s} | {like.group(1)[:110] if like else ''}")
