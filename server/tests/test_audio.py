import os
import threading
import time

import numpy as np
import pytest

from audio.analyzer import Analyzer, CHUNK, SAMPLE_RATE
from audio.sources import SyntheticSource, FifoSource
from audio.engine import AudioEngine


def feed(analyzer, source, seconds, bpm=120.0):
    """Push `seconds` of the synthetic loop through the analyzer with fake timestamps."""
    src = source(lambda m: None, None, bpm=bpm)
    n = int(seconds * SAMPLE_RATE / CHUNK)
    feats = []
    for k in range(n):
        mono = src.render(k * CHUNK / SAMPLE_RATE, CHUNK).astype(np.float32) / 32768.0
        feats.append(analyzer.update(mono, now=k * CHUNK / SAMPLE_RATE))
    return feats


def test_silence_is_inactive_and_zero():
    a = Analyzer()
    for k in range(120):
        f = a.update(np.zeros(CHUNK, dtype=np.float32), now=k * 0.023)
    assert f["active"] is False and f["level"] == 0 and f["bpm"] == 0 and f["beat"] is False


def test_bass_tone_lands_in_bass_band():
    a = Analyzer()
    t = np.arange(CHUNK) / SAMPLE_RATE
    f = None
    for k in range(60):
        tone = 0.5 * np.sin(2 * np.pi * 70 * (t + k * CHUNK / SAMPLE_RATE))
        f = a.update(tone.astype(np.float32), now=k * 0.023)
    assert f["active"] and f["bass"] > 0.5 and f["bass"] > f["treble"] * 3


def test_tempo_and_beats_from_synthetic_loop():
    a = Analyzer()
    feats = feed(a, SyntheticSource, 10, bpm=120)
    assert abs(feats[-1]["bpm"] - 120) < 4, feats[-1]["bpm"]
    beats = [f["ts"] for f in feats if f["beat"]]
    assert len(beats) >= 12
    # most detected beats sit near a multiple of 0.5 s (120 bpm)
    near = sum(1 for b in beats if min(b % 0.5, 0.5 - b % 0.5) < 0.06)
    assert near / len(beats) > 0.7, (near, len(beats))
    assert 0 <= feats[-1]["phase"] < 1 and feats[-1]["level"] > 0.2


def test_tempo_tracks_a_different_bpm():
    a = Analyzer()
    feats = feed(a, SyntheticSource, 10, bpm=90)
    assert abs(feats[-1]["bpm"] - 90) < 4, feats[-1]["bpm"]


def test_sensitivity_scales_levels():
    quiet = Analyzer(sensitivity=1.0)
    loud = Analyzer(sensitivity=2.0)
    t = np.arange(CHUNK) / SAMPLE_RATE
    for k in range(40):
        tone = (0.02 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        q = quiet.update(tone, now=k * 0.023)
        l = loud.update(tone, now=k * 0.023)
    assert l["mid"] >= q["mid"]


def test_fifo_source_streams_and_recovers(tmp_path):
    path = str(tmp_path / "audio.fifo")
    got = []
    src = FifoSource(lambda m: got.append(m), path, playback=None)
    src.start()
    deadline = time.time() + 3
    while not os.path.exists(path) and time.time() < deadline:
        time.sleep(0.05)
    assert os.path.exists(path)
    pcm = SyntheticSource(lambda m: None, None).render(0, CHUNK * 20)
    stereo = np.stack([pcm, pcm], axis=1).tobytes()

    def writer():
        with open(path, "wb") as fh:
            fh.write(stereo)
    th = threading.Thread(target=writer); th.start(); th.join(timeout=3)
    deadline = time.time() + 3
    while len(got) < 20 and time.time() < deadline:
        time.sleep(0.05)
    assert len(got) >= 20 and got[0].shape == (CHUNK,)
    assert src.streaming or len(got) >= 20
    # writer closed; the source stays alive for the next song
    time.sleep(1.3)
    th2 = threading.Thread(target=writer); th2.start(); th2.join(timeout=3)
    deadline = time.time() + 3
    before = len(got)
    while len(got) < before + 20 and time.time() < deadline:
        time.sleep(0.05)
    assert len(got) >= before + 20
    src.stop()


def test_audio_engine_synthetic_source(tmp_path):
    eng = AudioEngine(str(tmp_path / "f.fifo"))
    assert eng.features()["active"] is False
    st = eng.set(source="synthetic", sensitivity=1.5, sync=True)
    assert st["source"] == "synthetic" and st["sync"] is True and st["sensitivity"] == 1.5
    deadline = time.time() + 4
    while time.time() < deadline and not eng.features().get("active"):
        time.sleep(0.05)
    f = eng.features()
    assert f["active"] and f["level"] > 0
    with pytest.raises(ValueError):
        eng.set(source="nope")
    eng.set(source="off")
    assert eng.features()["active"] is False
    eng.shutdown()


def test_audio_api(client, config):
    st = client.get("/api/audio").get_json()
    assert st["source"] == "off" and any(s["id"] == "spotify" for s in st["sources"])
    res = client.post("/api/audio", json={"source": "synthetic", "sync": True, "demoBpm": 100})
    assert res.status_code == 200 and res.get_json()["source"] == "synthetic"
    assert client.post("/api/audio", json={"source": "bogus"}).status_code == 400
    deadline = time.time() + 4
    frame = None
    while time.time() < deadline:
        frame = client.get("/api/frame").get_json()
        if frame.get("audio", {}).get("active"):
            break
        time.sleep(0.05)
    assert frame["audio"]["active"] and "bass" in frame["audio"]
    assert client.get("/api/state").get_json()["audio"]["sync"] is True
    import json
    with open(config.state_file) as fh:
        assert json.load(fh)["audio"]["demoBpm"] == 100
    client.post("/api/audio", json={"source": "off"})
    assert "audio" not in client.get("/api/frame").get_json()


def test_music_sync_pumps_brightness_and_tempo(controller):
    from animations.effects.static_effects import Solid
    from tree import TreeLayout

    class FakeAudio:
        sync = True
        def __init__(self): self.env = 1.0
        def features(self): return {"active": True, "beat_env": self.env, "bpm": 240.0, "beat": False, "level": 1.0,
                                    "bass": 1, "mid": 1, "treble": 1, "onset": 0, "phase": 0, "ts": 0}
    audio = FakeAudio()
    anim = Solid(controller, TreeLayout([10]), {"color": [200, 200, 200]}, fps=60, audio=audio)
    th = threading.Thread(target=anim.run_animation, daemon=True); th.start()
    time.sleep(0.2)
    on_beat = controller.get_frame()[0][0]
    audio.env = 0.0
    time.sleep(0.2)
    off_beat = controller.get_frame()[0][0]
    anim.stop(); th.join(timeout=1)
    assert on_beat == 200 and 100 <= off_beat <= 115         # 0.55 gain between beats
    assert anim.t > 0.3                                       # tempo lock (240 bpm -> 2x) sped time up
