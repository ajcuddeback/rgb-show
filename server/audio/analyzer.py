#!/usr/bin/env python3
# Audio analysis
# Author: Austin Cuddeback (ajcuddeback@gmail.com)
#
# Turns a stream of PCM audio into a handful of numbers animations can use:
#   level / bass / mid / treble   0..1 loudness, auto-gain so quiet songs still fill the tree
#   beat                          True on the frame a beat was detected
#   beat_env                      1.0 on a beat, decaying to 0 (great for flashes)
#   bpm, phase                    estimated tempo and position within the current beat (0..1)
#   active                        there is signal (not silence)
#
# Classic approach: FFT per chunk, band energies, spectral flux for onsets with
# an adaptive threshold, and autocorrelation of the onset envelope for tempo.

import math
import threading
import time
from typing import Dict, Optional

import numpy as np

SAMPLE_RATE = 44100
CHUNK = 1024          # ~23 ms per analysis frame
FFT_SIZE = 2048

BANDS = {"bass": (40, 160), "mid": (160, 2000), "treble": (2000, 9000)}


class Analyzer:
    def __init__(self, sample_rate: int = SAMPLE_RATE, sensitivity: float = 1.0):
        self.sr = sample_rate
        self.sensitivity = sensitivity
        self._lock = threading.Lock()
        self._buf = np.zeros(FFT_SIZE, dtype=np.float32)
        self._window = np.hanning(FFT_SIZE).astype(np.float32)
        freqs = np.fft.rfftfreq(FFT_SIZE, 1.0 / sample_rate)
        self._band_bins = {k: (freqs >= lo) & (freqs < hi) for k, (lo, hi) in BANDS.items()}
        self._flux_bins = (freqs >= 40) & (freqs < 4000)
        self._prev_mag: Optional[np.ndarray] = None

        self._peak = {k: 1e-4 for k in list(BANDS) + ["level"]}   # running maxima for auto-gain
        self._smooth = {k: 0.0 for k in list(BANDS) + ["level"]}

        fps = sample_rate / CHUNK
        self._fps = fps
        self._flux_hist = np.zeros(int(fps * 1.5), dtype=np.float32)   # for the adaptive threshold
        self._onset_env = np.zeros(int(fps * 8), dtype=np.float32)     # for tempo
        self._hist_i = 0
        self._last_flux = 0.0
        self._last_beat_t = -10.0
        self._last_bpm_calc = 0.0
        self._bpm = 0.0
        self._beat_times = []
        self._frames = 0
        self._silence_frames = 0
        self._features: Dict = self._empty()

    @staticmethod
    def _empty() -> Dict:
        return {"level": 0.0, "bass": 0.0, "mid": 0.0, "treble": 0.0, "onset": 0.0,
                "beat": False, "beat_env": 0.0, "bpm": 0.0, "phase": 0.0, "active": False, "ts": time.monotonic()}

    # ------------------------------------------------------------------ input
    def update(self, mono: np.ndarray, now: Optional[float] = None) -> Dict:
        """Feed a mono float32 chunk (any length, -1..1). Returns the new feature snapshot."""
        now = time.monotonic() if now is None else now
        mono = np.asarray(mono, dtype=np.float32).ravel()
        if mono.size == 0:
            return self._features
        if mono.size >= FFT_SIZE:
            self._buf = mono[-FFT_SIZE:].copy()
        else:
            self._buf = np.concatenate([self._buf[mono.size:], mono])
        self._frames += 1

        mag = np.abs(np.fft.rfft(self._buf * self._window)) / FFT_SIZE
        rms = float(np.sqrt(np.mean(self._buf ** 2)))

        raw = {k: float(mag[bins].mean()) if bins.any() else 0.0 for k, bins in self._band_bins.items()}
        raw["level"] = rms

        silent = rms < 2e-4
        self._silence_frames = self._silence_frames + 1 if silent else 0
        active = self._silence_frames < self._fps * 1.5

        # Auto gain: each band is normalized by its own slowly-decaying running peak.
        decay = 0.9985       # ~15 s to halve at 43 fps
        levels = {}
        for k, v in raw.items():
            pk = max(self._peak[k] * decay, v, 1e-5)
            self._peak[k] = pk
            x = min(1.0, (v / pk) * self.sensitivity) if active else 0.0
            x = x ** 0.8
            s = self._smooth[k]
            s = x if x > s else s * 0.82 + x * 0.18        # fast attack, slower release
            self._smooth[k] = s
            levels[k] = s

        # Onset detection: positive spectral flux in the low/mid range vs an adaptive threshold.
        flux = 0.0
        if self._prev_mag is not None:
            d = mag[self._flux_bins] - self._prev_mag[self._flux_bins]
            flux = float(np.sum(d[d > 0]))
        self._prev_mag = mag
        n_hist = self._flux_hist.size
        self._flux_hist[self._hist_i % n_hist] = flux
        self._onset_env[self._hist_i % self._onset_env.size] = flux
        self._hist_i += 1
        thresh = float(self._flux_hist.mean()) * 1.6 + 1e-6
        beat = False
        min_gap = 60.0 / 220.0
        if active and flux > thresh and flux >= self._last_flux and (now - self._last_beat_t) > min_gap and self._hist_i > n_hist:
            beat = True
            self._last_beat_t = now
            self._beat_times.append(now)
            self._beat_times = [t for t in self._beat_times if now - t < 8]
        self._last_flux = flux

        # Tempo: autocorrelate the onset envelope every half second.
        if now - self._last_bpm_calc > 0.5 and self._hist_i > self._onset_env.size // 2:
            self._last_bpm_calc = now
            self._bpm = self._estimate_bpm()

        period = 60.0 / self._bpm if self._bpm > 0 else 0.0
        since = now - self._last_beat_t
        phase = (since / period) % 1.0 if period else 0.0
        beat_env = math.exp(-since * 5.0) if active else 0.0
        onset_norm = min(1.0, flux / (thresh * 2.0)) if thresh > 0 else 0.0

        f = {
            "level": levels["level"], "bass": levels["bass"], "mid": levels["mid"], "treble": levels["treble"],
            "onset": onset_norm, "beat": beat, "beat_env": beat_env, "bpm": round(self._bpm, 1), "phase": phase,
            "active": active, "ts": now,
        }
        with self._lock:
            self._features = f
        return f

    def _estimate_bpm(self) -> float:
        env = self._onset_env - self._onset_env.mean()
        if not np.any(env):
            return self._bpm
        ac = np.correlate(env, env, mode="full")[env.size - 1:]
        if ac[0] <= 0:
            return self._bpm
        ac = ac / ac[0]
        lo = int(self._fps * 60 / 180)      # 180 bpm
        hi = int(self._fps * 60 / 60)       # 60 bpm
        if hi >= ac.size:
            hi = ac.size - 1
        if lo >= hi:
            return self._bpm
        seg = ac[lo:hi]
        k = int(np.argmax(seg)) + lo
        bpm = 60.0 * self._fps / k
        if self._bpm > 0:
            # favour continuity; fold octave errors toward the previous estimate
            for cand in (bpm, bpm * 2, bpm / 2):
                if abs(cand - self._bpm) < abs(bpm - self._bpm):
                    bpm = cand
            bpm = self._bpm * 0.7 + bpm * 0.3
        return float(min(200.0, max(50.0, bpm)))

    # ----------------------------------------------------------------- output
    def features(self) -> Dict:
        with self._lock:
            return dict(self._features)

    def reset(self) -> None:
        with self._lock:
            self._features = self._empty()
        self._smooth = {k: 0.0 for k in self._smooth}


class NullAudio:
    """What animations get when audio is off: silence, no sync."""
    sync = False

    def features(self) -> Dict:
        return Analyzer._empty()
