#!/usr/bin/env python3
# Audio sources and playback
#
#   SyntheticSource   a built-in drum loop so you can see the music effects with no speaker
#   FifoSource        raw PCM written by librespot (Spotify Connect) to a FIFO; we analyze it
#                     and play it out the speaker, so lights and sound are one stream
#   DeviceSource      any input device (USB mic, loopback) via sounddevice
#   Playback          sounddevice output -> aplay subprocess -> silent fallback

import logging
import math
import os
import select
import shutil
import subprocess
import threading
import time
from typing import Callable, List, Optional

import numpy as np

from .analyzer import CHUNK, SAMPLE_RATE

log = logging.getLogger(__name__)

try:  # optional: needs the PortAudio shared library (apt install libportaudio2)
    import sounddevice as _sd  # type: ignore
    SOUNDDEVICE_ERROR = ""
except Exception as exc:  # pragma: no cover - depends on the machine
    _sd = None
    SOUNDDEVICE_ERROR = str(exc)


# ---------------------------------------------------------------- playback
class Playback:
    """Writes 16-bit stereo PCM to a speaker. Picks the best available backend."""

    def __init__(self, device: Optional[str] = None):
        self.device = device
        self.backend = "none"
        self.latency = 0.0
        self._stream = None
        self._proc = None
        if _sd is not None:
            try:
                kwargs = {"samplerate": SAMPLE_RATE, "channels": 2, "dtype": "int16"}
                if device and device != "default":
                    kwargs["device"] = device
                self._stream = _sd.OutputStream(**kwargs)
                self._stream.start()
                self.latency = float(self._stream.latency or 0.05)
                self.backend = "sounddevice"
                return
            except Exception as exc:
                log.warning("sounddevice output unavailable (%s); trying aplay", exc)
        aplay = shutil.which("aplay")
        if aplay:
            cmd = [aplay, "-q", "-t", "raw", "-f", "S16_LE", "-r", str(SAMPLE_RATE), "-c", "2"]
            if device and device != "default":
                cmd += ["-D", device]
            try:
                self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                self.backend = "aplay"
                self.latency = 0.12
                return
            except Exception as exc:
                log.warning("aplay unavailable: %s", exc)
        log.warning("No audio output available; music will be analyzed but not played")

    def write(self, pcm_int16_stereo: np.ndarray) -> None:
        try:
            if self._stream is not None:
                self._stream.write(pcm_int16_stereo)
            elif self._proc is not None and self._proc.stdin:
                self._proc.stdin.write(pcm_int16_stereo.tobytes())
        except Exception as exc:
            log.warning("Audio output failed (%s); disabling playback", exc)
            self.close()

    def close(self) -> None:
        try:
            if self._stream is not None:
                self._stream.stop(); self._stream.close()
        except Exception:
            pass
        self._stream = None
        if self._proc is not None:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
            except Exception:
                pass
        self._proc = None
        self.backend = "none"


def list_output_devices() -> List[dict]:
    out = [{"id": "default", "label": "System default"}]
    if _sd is None:
        return out
    try:
        for i, d in enumerate(_sd.query_devices()):
            if d.get("max_output_channels", 0) > 0:
                out.append({"id": str(i), "label": d["name"]})
    except Exception:
        pass
    return out


def list_input_devices() -> List[dict]:
    if _sd is None:
        return []
    try:
        return [{"id": f"device:{i}", "label": d["name"]} for i, d in enumerate(_sd.query_devices())
                if d.get("max_input_channels", 0) > 0]
    except Exception:
        return []


# ----------------------------------------------------------------- sources
class BaseSource:
    name = "base"

    def __init__(self, on_chunk: Callable[[np.ndarray], None], playback: Optional[Playback] = None):
        self.on_chunk = on_chunk
        self.playback = playback
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.error: Optional[str] = None
        self.streaming = False          # True while audio is actually flowing

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._guard, name=f"audio-{self.name}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=2.0)
        if self.playback:
            self.playback.close()

    def _guard(self) -> None:
        try:
            self.run()
        except Exception as exc:
            log.exception("Audio source %s crashed", self.name)
            self.error = str(exc)
        finally:
            self.streaming = False

    def run(self) -> None:
        raise NotImplementedError

    def _emit(self, stereo_int16: np.ndarray) -> None:
        mono = stereo_int16.astype(np.float32).mean(axis=1) / 32768.0
        self.on_chunk(mono)
        if self.playback is not None:
            self.playback.write(stereo_int16)


class SyntheticSource(BaseSource):
    """Kick / hat / bass loop at a fixed tempo. Real-time paced."""
    name = "synthetic"

    def __init__(self, on_chunk, playback=None, bpm: float = 120.0):
        super().__init__(on_chunk, playback)
        self.bpm = bpm

    def render(self, t0: float, n: int) -> np.ndarray:
        """Deterministic loop audio for samples starting at time t0 (seconds)."""
        t = t0 + np.arange(n) / SAMPLE_RATE
        beat = 60.0 / self.bpm
        pos = t % beat
        bar = (t // beat) % 4
        kick = np.sin(2 * np.pi * (150 * np.exp(-pos * 14) + 45) * pos) * np.exp(-pos * 9) * 0.9
        hat_pos = (t + beat / 2) % beat
        rng = np.random.default_rng(int(t0 * 1000) & 0xFFFF)
        hat = rng.standard_normal(n).astype(np.float32) * np.exp(-hat_pos * 60) * 0.25
        bass_note = [55.0, 55.0, 65.4, 49.0][int(bar[0])]
        bass = np.sin(2 * np.pi * bass_note * t) * 0.3 * (0.6 + 0.4 * np.exp(-pos * 4))
        pad = 0.08 * (np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 277.2 * t) + np.sin(2 * np.pi * 329.6 * t))
        mix = np.clip(kick + hat + bass + pad, -1, 1)
        return (mix * 32767).astype(np.int16)

    def run(self) -> None:
        self.streaming = True
        start = time.monotonic()
        samples = 0
        while not self._stop.is_set():
            t0 = samples / SAMPLE_RATE
            mono = self.render(t0, CHUNK)
            self._emit(np.stack([mono, mono], axis=1))
            samples += CHUNK
            # pace to real time
            ahead = (samples / SAMPLE_RATE) - (time.monotonic() - start)
            if ahead > 0.02:
                self._stop.wait(min(ahead - 0.01, 0.05))


class FifoSource(BaseSource):
    """Reads S16LE 44.1 kHz stereo from a named pipe (librespot --backend pipe)."""
    name = "spotify"

    def __init__(self, on_chunk, path: str, playback=None):
        super().__init__(on_chunk, playback)
        self.path = path

    def run(self) -> None:
        frame_bytes = CHUNK * 2 * 2
        while not self._stop.is_set():
            if not os.path.exists(self.path):
                try:
                    os.makedirs(os.path.dirname(self.path), exist_ok=True)
                    os.mkfifo(self.path)
                    os.chmod(self.path, 0o666)
                except OSError as exc:
                    self.error = f"Cannot create FIFO {self.path}: {exc}"
                    self._stop.wait(2)
                    continue
            try:
                fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError as exc:
                self.error = f"Cannot open FIFO {self.path}: {exc}"
                self._stop.wait(2)
                continue
            self.error = None
            buf = b""
            idle = 0.0
            try:
                while not self._stop.is_set():
                    r, _, _ = select.select([fd], [], [], 0.25)
                    if not r:
                        idle += 0.25
                        if idle > 1.0 and self.streaming:
                            self.streaming = False
                            self.on_chunk(np.zeros(CHUNK, dtype=np.float32))   # let the analyzer see silence
                        continue
                    data = os.read(fd, 65536)
                    if not data:          # writer went away (song paused / librespot restarted)
                        idle += 0.1
                        if idle > 1.0 and self.streaming:
                            self.streaming = False
                            self.on_chunk(np.zeros(CHUNK, dtype=np.float32))
                        self._stop.wait(0.1)
                        continue
                    idle = 0.0
                    self.streaming = True
                    buf += data
                    while len(buf) >= frame_bytes:
                        chunk, buf = buf[:frame_bytes], buf[frame_bytes:]
                        self._emit(np.frombuffer(chunk, dtype=np.int16).reshape(-1, 2))
            finally:
                os.close(fd)


class DeviceSource(BaseSource):
    """Any sounddevice input (USB mic, loopback/monitor). Not played back."""
    name = "device"

    def __init__(self, on_chunk, device_id: str):
        super().__init__(on_chunk, None)
        self.device_id = device_id

    def run(self) -> None:
        if _sd is None:
            self.error = f"sounddevice unavailable: {SOUNDDEVICE_ERROR}"
            return
        dev = int(self.device_id.split(":", 1)[1]) if self.device_id.startswith("device:") else self.device_id
        q: List[np.ndarray] = []
        lock = threading.Lock()

        def cb(indata, frames, time_info, status):
            with lock:
                q.append(indata.copy())

        with _sd.InputStream(samplerate=SAMPLE_RATE, blocksize=CHUNK, channels=1, dtype="float32", device=dev, callback=cb):
            self.streaming = True
            while not self._stop.is_set():
                with lock:
                    items, q[:] = q[:], []
                for item in items:
                    self.on_chunk(item[:, 0])
                self._stop.wait(0.01)
