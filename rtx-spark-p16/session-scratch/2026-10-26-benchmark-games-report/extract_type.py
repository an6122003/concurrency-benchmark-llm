import json, sys
path, out = sys.argv[1], sys.argv[2]
seen = set()
chunks = []
def texts(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from texts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from texts(v)
with open(path, encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "dash.onData(fn)" not in line and "data/users/me" not in line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        for t in texts(rec):
            if ("dash.onData(fn)" in t or "data/users/me" in t) and len(t) > 2000:
                key = t[:300]
                if key in seen:
                    continue
                seen.add(key)
                chunks.append(f"===== line {i} len {len(t)}\n{t}\n")
open(out, "w", encoding="utf-8").write("\n".join(chunks))
print(len(chunks), "chunks", sum(len(c) for c in chunks), "chars")
