"""Voiceover in the creator's own (cloned) voice for Bali Diary 01.

XTTS-v2 speaks each sentence a few times; Whisper picks the take whose words
best match the script, and the best takes are joined into one file per line.

usage: COQUI_TOS_AGREED=1 python3 clone_vo_bali01.py <workdir>
<workdir>/myvoice/ref_clean.wav must hold the creator's denoised voice sample.
Note: XTTS-v2 weights are under the Coqui Public Model License (non-commercial).
"""
import difflib, re, subprocess, sys
import numpy as np, soundfile as sf, torch
from faster_whisper import WhisperModel
from TTS.api import TTS

BASE = sys.argv[1]
TAKES = 3
LINES = [
    ["मुंबई से बाली... वाया क्वालालंपुर, मलेशिया एयरलाइंस पे.", "चलो, दिखाती हूँ एक्सपीरियंस कैसा रहा!"],
    ["रात के बारह बजे बोर्डिंग.", "फ्लाइट फुल थी, रेड पर्पल सीट्स...", "और क्रू की बाटिक केबाया यूनिफॉर्म,", "सच में, मलेशिया वाली फील आ गई."],
    ["रात एक बजे डिनर.", "मैंने वेज लिया, हस्बैंड ने नॉन वेज.", "पराठा, राइस करी, सलाद, अमूल दही...", "वेज मील बस ठीक ठाक था."],
    ["और स्क्रीन्स?", "हमने काफी एक्सपेक्ट किया था...", "बट ऑनेस्टली, लेटडाउन था."],
    ["लेकिन फिर सुबह... ये व्यू मिला."],
    ["के एल में छोटा सा लेओवर,", "और दूसरी फ्लाइट बाली के लिए, एकदम अपग्रेड!", "नया प्लेन, बड़े स्क्रीन्स, फ्रेश केबिन."],
    ["नेक्स्ट स्टॉप... बाली!", "बाकी ट्रिप के लिए फॉलो करते रहो."],
]
SR = 24000


def norm(s):
    return re.sub(r"[\s\.,!?।…'\"-]", "", s)


def trim(a, thr=0.012, pad=0.04):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    p = int(pad * SR)
    return a[max(0, idx[0] - p): idx[-1] + p]


def to16k(a):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-f", "f32le", "-ar", "16000", "-"], input=a.astype(np.float32).tobytes(), capture_output=True)
    return np.frombuffer(p.stdout, np.float32).copy()


tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
asr = WhisperModel("small", device="cpu", compute_type="int8")
ref = f"{BASE}/myvoice/ref_clean.wav"
for li, chunks in enumerate(LINES, 1):
    parts = []
    for ci, text in enumerate(chunks):
        best = None
        for k in range(TAKES):
            torch.manual_seed(1000 * li + 10 * ci + k)
            a = trim(np.array(tts.tts(text=text, speaker_wav=ref, language="hi", speed=1.08,
                                      temperature=0.55, repetition_penalty=8.0), dtype=np.float32))
            heard = " ".join(s.text for s in asr.transcribe(to16k(a), language="hi")[0])
            score = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
            score -= 0.02 * max(0.0, len(a) / SR - 0.11 * len(norm(text)))  # penalise rambling takes
            if best is None or score > best[0]:
                best = (score, a, heard)
        print(f"line {li}.{ci + 1} score {best[0]:.2f} {len(best[1]) / SR:.1f}s | {best[2]}", flush=True)
        parts += [best[1], np.zeros(int(0.12 * SR), np.float32)]
    sf.write(f"{BASE}/myvoice/clone_{li}.wav", np.concatenate(parts[:-1]), SR)
print("done", flush=True)
