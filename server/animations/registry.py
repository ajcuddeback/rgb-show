#!/usr/bin/env python3
# Animation registry
#
# Auto-discovers every Animation subclass in this package so adding a new
# effect is just dropping a file in `animations/effects/`.

import importlib
import inspect
import logging
import pkgutil
from typing import Dict, List, Type

from .base import Animation

log = logging.getLogger(__name__)

CATEGORY_ORDER = ["Static", "Motion", "Sparkle", "Nature", "Showpiece"]

_registry: Dict[str, Type[Animation]] = {}


def _discover() -> None:
    from . import effects  # noqa: F401  (package)

    for mod in pkgutil.iter_modules(effects.__path__):
        module = importlib.import_module(f"{effects.__name__}.{mod.name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, Animation) and cls is not Animation and cls.__module__ == module.__name__:
                name = cls.name()
                if name in _registry and _registry[name] is not cls:
                    log.warning("Duplicate animation name %s (%s vs %s)", name, cls, _registry[name])
                _registry[name] = cls


def all_animations() -> Dict[str, Type[Animation]]:
    if not _registry:
        _discover()
    return _registry


def get(name: str) -> Type[Animation]:
    return all_animations()[name]


def describe_all() -> List[dict]:
    items = [cls.describe() for cls in all_animations().values()]

    def sort_key(item):
        cat = item["category"]
        return (CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else 99, item["label"])

    return sorted(items, key=sort_key)
