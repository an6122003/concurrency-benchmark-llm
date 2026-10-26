"""Master the arcade cut's score (out/arcade-raw.wav, the game's own synth) for delivery: -14 LUFS integrated, true
peak at most -1.5 dBTP, cut to the film's length with a short fade. Writes out/soundtrack-arcade.wav (48 kHz, 24-bit).

    ..\\earshot\\.venv\\Scripts\\python.exe audio\\master_arcade.py <seconds>
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mix import LUFS, CEIL, limit, ramp  # noqa: E402  the film's own master settings and limiter
from earshot import features  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    dur = float(sys.argv[1])
    y, sr = sf.read(str(ROOT / 'out' / 'arcade-raw.wav'), always_2d=True)
    raw_peak = 20 * np.log10(np.abs(y).max())   # the render's 16-bit file clips at 0 dBFS
    n = int(round(dur * sr))
    y = np.pad(y, ((0, max(0, n - len(y))), (0, 0)))[:n].astype(np.float64)
    fo = int(0.25 * sr)
    y[-fo:] *= ramp(fo, up=False)[:, None]
    # the game's kicks and booms peak far above its loudness, so gain and limiting alternate until both hold
    tp0 = None
    for _ in range(10):
        y *= 10 ** ((LUFS - features.integrated_lufs(y)) / 20)
        tp0 = tp0 if tp0 is not None else features.true_peak_dbtp(y)
        ceiling, tp = CEIL, features.true_peak_dbtp(y)
        while tp > CEIL:
            y = limit(y, ceiling)
            tp = features.true_peak_dbtp(y)
            ceiling -= 0.2
        if abs(features.integrated_lufs(y) - LUFS) < 0.25:
            break
    out = ROOT / 'out' / 'soundtrack-arcade.wav'
    sf.write(str(out), y.astype(np.float32), sr, subtype='PCM_24')
    mid, side = (y[:, 0] + y[:, 1]) / 2, (y[:, 0] - y[:, 1]) / 2
    width = 10 * np.log10(np.sum(side ** 2) / max(np.sum(mid ** 2), 1e-12) + 1e-12)
    print(f'{out}: {dur:.2f} s, {features.integrated_lufs(y):.2f} LUFS, true peak {tp:.2f} dBTP (before limiting {tp0:.2f}); '
          f'raw peak {raw_peak:.2f} dBFS; stereo width (side vs mid) {width:.1f} dB')


if __name__ == '__main__':
    main()
