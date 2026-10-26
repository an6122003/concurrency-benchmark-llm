"""Sum GGUF tensor sizes by name pattern (reads headers only).

Usage: gguf_tensors.py <shard.gguf> [<shard.gguf> ...]
Sizes come from the gaps between consecutive tensor offsets, so no type table is needed.
"""
import collections
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gguf_info import read_str, read_val  # noqa: E402


def tensors(path):
    with open(path, "rb") as f:
        assert f.read(4) == b"GGUF"
        version, n_tensors, n_kv = struct.unpack("<IQQ", f.read(20))
        align = 32
        for _ in range(n_kv):
            key = read_str(f)
            (t,) = struct.unpack("<I", f.read(4))
            val = read_val(f, t)
            if key == "general.alignment":
                align = val
        infos = []
        for _ in range(n_tensors):
            name = read_str(f)
            (nd,) = struct.unpack("<I", f.read(4))
            f.read(8 * nd)
            (ttype,) = struct.unpack("<I", f.read(4))
            (offset,) = struct.unpack("<Q", f.read(8))
            infos.append((offset, name, ttype))
        data_start = (f.tell() + align - 1) // align * align
    size = os.path.getsize(path)
    infos.sort()
    for i, (offset, name, ttype) in enumerate(infos):
        end = infos[i + 1][0] if i + 1 < len(infos) else size - data_start
        yield name, ttype, end - offset


if __name__ == "__main__":
    groups = collections.Counter()
    biggest = []
    for path in sys.argv[1:]:
        for name, ttype, nbytes in tensors(path):
            key = re.sub(r"\.\d+\.", ".N.", name)
            key = re.sub(r"^blk\.N\.", "blk.", key)
            groups[key] += nbytes
            biggest.append((nbytes, name, ttype))
    total = sum(groups.values())
    print(f"total {total / 2**30:.2f} GiB")
    for key, nbytes in groups.most_common(12):
        print(f"{nbytes / 2**30:8.2f} GiB  {key}")
    print("largest single tensors:")
    for nbytes, name, ttype in sorted(biggest, reverse=True)[:6]:
        print(f"{nbytes / 2**30:8.2f} GiB  {name} (type {ttype})")
