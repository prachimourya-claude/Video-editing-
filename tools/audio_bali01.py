"""Build the low ambient cabin-sound bed for Bali Diary 01, timed to render_bali01.py.

usage: python3 audio_bali01.py <workdir> <out.wav>
"""
import subprocess, sys

BASE, OUT = sys.argv[1], sys.argv[2]
CLIP = {
    "A": "drive/DJI_20261006234428_0017_D~2.mp4",
    "B": "drive/DJI_20261007012656_0018_D~2.mp4",
    "C": "drive/DJI_20261007044857_0019_D.MP4",
    "D": "drive/DJI_20261007044927_0020_D.MP4",
    "E": "drive/DJI_20261007073147_0039_D.MP4",
}
TOTAL = 52.0
# (timeline start, timeline duration, clip, source start, speed, volume)
PARTS = [
    (0.0, 6.3, "D", 14.0, 1, 0.22),
    (6.0, 5.3, "A", 0.0, 1.5, 0.35),
    (11.0, 4.4, "A", 9.0, 1, 0.35),
    (15.0, 2.0, "B", 0.0, 1, 0.25),
    (17.0, 2.5, "B", 4.5, 0.625, 0.25),
    (19.5, 2.4, "B", 8.6, 1, 0.25),
    (21.9, 2.0, "B", 13.1, 1, 0.25),
    (23.9, 2.5, "B", 48.5, 1, 0.25),
    (26.0, 4.8, "C", 6.5, 1, 0.3),
    (30.0, 7.5, "D", 3.5, 1, 0.3),
    (37.0, 3.5, "D", 14.0, 1, 0.22),
    (40.0, 4.2, "E", 7.5, 1, 0.6),
    (44.0, 4.4, "E", 14.0, 1, 0.6),
    (47.0, 5.0, "D", 18.0, 1, 0.22),
]

inputs, chains = [], []
for i, (st, dur, c, ss, sp, vol) in enumerate(PARTS):
    inputs += ["-i", f"{BASE}/{CLIP[c]}"]
    src = dur * sp
    tempo = f"atempo={sp}," if sp != 1 else ""
    chains.append(
        f"[{i}:a:0]atrim=start={ss}:duration={src},asetpts=PTS-STARTPTS,{tempo}"
        f"aformat=sample_rates=48000:channel_layouts=stereo,volume={vol},"
        f"afade=t=in:d=0.2,afade=t=out:st={dur - 0.25}:d=0.25,adelay={int(st * 1000)}:all=1[a{i}]"
    )
mix = "".join(f"[a{i}]" for i in range(len(PARTS)))
fc = ";".join(chains) + f";{mix}amix=inputs={len(PARTS)}:normalize=0,volume=0.5,atrim=duration={TOTAL},afade=t=out:st={TOTAL - 1.2}:d=1.2[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", OUT], check=True)
