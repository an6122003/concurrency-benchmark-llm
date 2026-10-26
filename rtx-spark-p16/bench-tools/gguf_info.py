"""Print the key metadata of GGUF files (stdlib only, reads the header only)."""
import json
import struct
import sys

SCALARS = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}


def read_str(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", errors="replace")


def read_val(f, t):
    if t in SCALARS:
        fmt = SCALARS[t]
        return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]
    if t == 8:
        return read_str(f)
    if t == 9:
        (it,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        if it in SCALARS and n > 64:
            f.seek(struct.calcsize(SCALARS[it]) * n, 1)
            return f"<array of {n}>"
        if it == 8 and n > 64:
            for _ in range(n):
                read_str(f)
            return f"<string array of {n}>"
        return [read_val(f, it) for _ in range(n)]
    raise ValueError(f"unknown type {t}")


def info(path):
    with open(path, "rb") as f:
        assert f.read(4) == b"GGUF", "not a GGUF file"
        version, n_tensors, n_kv = struct.unpack("<IQQ", f.read(20))
        kv = {}
        for _ in range(n_kv):
            key = read_str(f)
            (t,) = struct.unpack("<I", f.read(4))
            kv[key] = read_val(f, t)
    return version, n_tensors, kv


if __name__ == "__main__":
    for path in sys.argv[1:]:
        version, n_tensors, kv = info(path)
        print("=" * 100)
        print(path)
        print(f"gguf v{version}, tensors={n_tensors}")
        tmpl = kv.pop("tokenizer.chat_template", "")
        for key, value in kv.items():
            if key.startswith("tokenizer.ggml.") and key not in ("tokenizer.ggml.model", "tokenizer.ggml.pre"):
                continue
            text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            if len(text) > 200:
                text = text[:200] + "..."
            print(f"  {key} = {text}")
        if tmpl:
            flags = [w for w in ("enable_thinking", "reasoning_effort", "thinking_budget", "<think>", "builtin_tools", "preserve") if w in tmpl]
            print(f"  chat_template: {len(tmpl)} chars, mentions {flags}")
