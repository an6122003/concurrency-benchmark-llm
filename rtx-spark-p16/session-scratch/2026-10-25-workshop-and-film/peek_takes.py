import sys

sys.path.insert(0, sys.argv[1])
import mix  # noqa: E402

np = mix.np
for name in sys.argv[2].split(','):
    raw = mix.audio.load(str(mix.EL / f'{name}.mp3'))
    t = mix.eleven_take(name, 5.0)
    m = raw.mean(axis=1)
    w = int(0.02 * mix.SR)
    env = [20 * np.log10(np.sqrt((m[i:i + w] ** 2).mean()) + 1e-9) for i in range(0, min(len(m), int(0.6 * mix.SR)), w)]
    print(f"{name:10s} raw {len(raw) / mix.SR:5.2f} s peak {20 * np.log10(abs(raw).max() + 1e-12):6.1f} dBFS | "
          f"onset {t['onset_s']:.3f} peak_s {t['peak_s']:.3f} end {t['end_s']:.3f} l50 {t['l50_lufs']:6.1f}")
    print('   20 ms RMS dB:', ' '.join(f'{v:.0f}' for v in env))
