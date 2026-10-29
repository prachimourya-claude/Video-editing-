"""Chat sound effects for the can-opener reel: a soft "pop" when you send a bubble, a two-note ding when a friend's
bubble arrives, and light keyboard clicks while the "typing…" dots show. Timed from render_opener01.BUBBLES.

usage: cd tools && python3 sfx_opener01.py <workdir> <out.wav>
"""
import subprocess, sys
import numpy as np

import render_opener01 as P

SR = 48000
TOTAL = P.SEGMENTS[-1][2]
rng = np.random.default_rng(3)


def env(n, attack=0.004, decay=0.06):
    t = np.arange(n) / SR
    return np.minimum(t / attack, 1) * np.exp(-t / decay)


def tone(f0, f1, dur, decay, amp):
    n = int(dur * SR)
    f = np.linspace(f0, f1, n)
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, decay=decay)


def send():   # quick rising "pop" with a short bright tail
    out = tone(520, 1150, 0.12, 0.035, 0.55)
    tail = tone(1150, 1150, 0.09, 0.03, 0.15)
    out[:len(tail)] += tail
    return out


def receive():  # two-note ding
    a = tone(1320, 1320, 0.16, 0.05, 0.4)
    b = tone(1760, 1760, 0.22, 0.07, 0.35)
    out = np.zeros(int(0.32 * SR))
    out[:len(a)] += a
    out[int(0.09 * SR):int(0.09 * SR) + len(b)] += b
    return out


def click():
    n = int(0.018 * SR)
    noise = rng.normal(0, 1, n)
    noise = np.convolve(noise, np.ones(6) / 6, "same")  # soften
    return 0.18 * noise * env(n, attack=0.001, decay=0.004)


def build():
    out = np.zeros(int(TOTAL * SR) + SR)

    def put(sig, t):
        i = int(t * SR)
        out[i:i + len(sig)] += sig[:max(0, len(out) - i)]

    for at, _, right, *_ in P.BUBBLES:
        if right:
            put(send(), at)
        else:
            t = max(0.05, at - 0.7)  # typing clicks under the "typing…" dots
            while t < at - 0.08:
                put(click() * rng.uniform(0.6, 1.0), t)
                t += rng.uniform(0.07, 0.14)
            put(receive(), at)
    out = out[:int(TOTAL * SR)]
    return np.clip(out / max(1e-6, np.abs(out).max()) * 0.6, -1, 1).astype(np.float32)


if __name__ == "__main__":
    a = build()
    stereo = np.repeat(a[:, None], 2, 1).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", P.OUT],
                   input=stereo, check=True)
    print("wrote", P.OUT)
