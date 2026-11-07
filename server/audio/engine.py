#!/usr/bin/env python3
# Audio engine: owns the analyzer, the active source and playback; exposes
# features to animations with the output latency compensated.

import collections
import logging
import threading
import time
from typing import Dict, List, Optional

from .analyzer import Analyzer, NullAudio
from .sources import (DeviceSource, FifoSource, Playback, SyntheticSource, SOUNDDEVICE_ERROR,
                      list_input_devices, list_output_devices, _sd)

log = logging.getLogger(__name__)


class AudioEngine:
    def __init__(self, fifo_path: str):
        self.fifo_path = fifo_path
        self.analyzer = Analyzer()
        self.source_id = "off"
        self.output_id = "default"
        self.sensitivity = 1.0
        self.sync = False
        self.demo_bpm = 120.0
        self._source = None
        self._playback: Optional[Playback] = None
        self._lock = threading.RLock()
        # Features are published slightly late so what the tree shows lines up with what the speaker plays.
        self._history = collections.deque(maxlen=64)
        self._latency = 0.0

    # ---------------------------------------------------------------- config
    def sources(self) -> List[dict]:
        out = [
            {"id": "off", "label": "Off"},
            {"id": "spotify", "label": "Spotify (play through the Pi)", "hint": "Pick 'Christmas Tree' in the Spotify app"},
            {"id": "synthetic", "label": "Demo beat", "hint": "Built-in drum loop, no speaker needed"},
        ]
        out += list_input_devices()
        return out

    def outputs(self) -> List[dict]:
        return list_output_devices()

    def set(self, source: Optional[str] = None, sensitivity: Optional[float] = None,
            sync: Optional[bool] = None, output: Optional[str] = None, demo_bpm: Optional[float] = None) -> dict:
        with self._lock:
            restart = False
            if sensitivity is not None:
                self.sensitivity = max(0.2, min(4.0, float(sensitivity)))
                self.analyzer.sensitivity = self.sensitivity
            if sync is not None:
                self.sync = bool(sync)
            if demo_bpm is not None:
                self.demo_bpm = max(50.0, min(200.0, float(demo_bpm)))
                restart = restart or self.source_id == "synthetic"
            if output is not None and output != self.output_id:
                self.output_id = str(output)
                restart = True
            if source is not None and source != self.source_id:
                valid = {s["id"] for s in self.sources()}
                if source not in valid:
                    raise ValueError(f"Unknown audio source '{source}'")
                self.source_id = source
                restart = True
            if restart:
                self._restart()
        return self.status()

    def _restart(self) -> None:
        self._stop_source()
        self.analyzer.reset()
        self._history.clear()
        if self.source_id == "off":
            return
        playback = None
        if self.source_id in ("spotify", "synthetic"):
            playback = Playback(self.output_id)
            self._latency = playback.latency if playback.backend != "none" else 0.0
        else:
            self._latency = 0.0
        self._playback = playback
        if self.source_id == "spotify":
            self._source = FifoSource(self._on_chunk, self.fifo_path, playback)
        elif self.source_id == "synthetic":
            self._source = SyntheticSource(self._on_chunk, playback, bpm=self.demo_bpm)
        else:
            self._source = DeviceSource(self._on_chunk, self.source_id)
        self._source.start()
        log.info("Audio source %s started (output=%s, latency=%.0f ms)", self.source_id,
                 playback.backend if playback else "-", self._latency * 1000)

    def _stop_source(self) -> None:
        if self._source is not None:
            self._source.stop()
            self._source = None
        if self._playback is not None:
            self._playback.close()
            self._playback = None

    def _on_chunk(self, mono) -> None:
        f = self.analyzer.update(mono)
        self._history.append(f)

    # ---------------------------------------------------------------- output
    def features(self) -> Dict:
        """Latest features, delayed by the output latency so lights match the speaker."""
        if self.source_id == "off":
            return NullAudio().features()
        if self._latency <= 0 or len(self._history) < 2:
            return self.analyzer.features()
        target = time.monotonic() - self._latency
        best = self._history[-1]
        for f in reversed(self._history):
            if f["ts"] <= target:
                best = f
                break
        return dict(best)

    def status(self) -> dict:
        src = self._source
        return {
            "source": self.source_id,
            "output": self.output_id,
            "sensitivity": self.sensitivity,
            "sync": self.sync,
            "demoBpm": self.demo_bpm,
            "streaming": bool(src and src.streaming),
            "error": src.error if src else None,
            "playback": self._playback.backend if self._playback else "none",
            "latencyMs": round(self._latency * 1000),
            "sources": self.sources(),
            "outputs": self.outputs(),
            "devicesAvailable": _sd is not None,
            "devicesError": SOUNDDEVICE_ERROR if _sd is None else "",
            "fifo": self.fifo_path,
            "features": self.features(),
        }

    def settings(self) -> dict:
        return {"source": self.source_id, "output": self.output_id, "sensitivity": self.sensitivity,
                "sync": self.sync, "demoBpm": self.demo_bpm}

    def shutdown(self) -> None:
        with self._lock:
            self._stop_source()
