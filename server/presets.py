#!/usr/bin/env python3
# Presets: named (animation + params) combos saved on the Pi as JSON.

import json
import logging
import os
import threading
import uuid
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class PresetStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._presets: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path) as fh:
                data = json.load(fh)
            if isinstance(data, list):
                self._presets = [p for p in data if isinstance(p, dict) and "id" in p]
        except (OSError, ValueError) as exc:
            log.warning("Could not read presets %s: %s", self.path, exc)

    def _flush(self) -> None:
        if not self.path:
            return
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(self._presets, fh, indent=2)
            os.replace(tmp, self.path)
        except OSError as exc:
            log.warning("Could not write presets %s: %s", self.path, exc)

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(p) for p in self._presets]

    def get(self, preset_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for p in self._presets:
                if p["id"] == preset_id:
                    return dict(p)
        return None

    def add(self, name: str, animation: str, params: Dict[str, Any],
            speed: Optional[float] = None, brightness: Optional[float] = None) -> Dict[str, Any]:
        preset = {
            "id": uuid.uuid4().hex[:10],
            "name": (name or animation).strip()[:60],
            "animation": animation,
            "params": params,
        }
        if speed is not None:
            preset["speed"] = speed
        if brightness is not None:
            preset["brightness"] = brightness
        with self._lock:
            self._presets.append(preset)
            self._flush()
        return dict(preset)

    def delete(self, preset_id: str) -> bool:
        with self._lock:
            before = len(self._presets)
            self._presets = [p for p in self._presets if p["id"] != preset_id]
            changed = len(self._presets) != before
            if changed:
                self._flush()
        return changed
