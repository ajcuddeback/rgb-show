"""Every registered animation must render valid frames for a range of pixel counts."""
import pytest

from animations import registry
from animations.base import Animation
from config import Config
from neopixel_controller import NeoPixelController
from tree import TreeLayout

ALL = sorted(registry.all_animations().items())


def _mapped_tree(n):
    import math
    import random
    rnd = random.Random(n)
    pts = [[(1 - 0.8 * i / n) * math.cos(i * 0.4) + rnd.uniform(-0.05, 0.05),
            (1 - 0.8 * i / n) * math.sin(i * 0.4), i / max(1, n - 1)] for i in range(n)]
    if n > 10:
        pts[3] = None
    return TreeLayout.from_points(pts)


@pytest.mark.parametrize("name,cls", ALL, ids=[n for n, _ in ALL])
@pytest.mark.parametrize("num_pixels", [1, 7, 50, 100, 250])
@pytest.mark.parametrize("kind", ["wraps", "mapped"])
def test_renders_valid_frames(name, cls, num_pixels, kind):
    cfg = Config(num_pixels=num_pixels, simulate=True)
    controller = NeoPixelController(num_pixels, simulate=True)
    tree = TreeLayout(cfg.resolved_rings()) if kind == "wraps" else _mapped_tree(num_pixels)
    anim = cls(controller, tree, {}, speed=1.0, fps=30)
    for step in range(40):
        anim.render(step * 0.1)
        assert len(anim.frame) == num_pixels
        for px in anim.frame:
            assert len(px) == 3
            assert all(0 <= c <= 255 and isinstance(c, int) for c in px), (name, px)
    controller.show_frame(anim.frame)


@pytest.mark.parametrize("name,cls", ALL, ids=[n for n, _ in ALL])
def test_describe_and_defaults(name, cls):
    desc = cls.describe()
    assert desc["name"] == name
    assert desc["label"] and desc["description"]
    assert desc["category"] in registry.CATEGORY_ORDER
    keys = {p["key"] for p in desc["params"]}
    assert keys == set(cls.defaults().keys())
    for p in desc["params"]:
        assert p["type"] in ("color", "colors", "number", "select", "boolean")


@pytest.mark.parametrize("name,cls", ALL, ids=[n for n, _ in ALL])
def test_live_param_update_does_not_break_render(name, cls):
    controller = NeoPixelController(100, simulate=True)
    tree = TreeLayout(Config(num_pixels=100).resolved_rings())
    anim = cls(controller, tree, {}, speed=1.0, fps=30)
    anim.render(0.5)
    # Push extreme-but-valid values for every param
    extremes = {}
    for p in cls.PARAMS:
        if p.type == "number":
            extremes[p.key] = p.max
        elif p.type == "colors":
            extremes[p.key] = [[255, 255, 255]] * p.max_items
        elif p.type == "color":
            extremes[p.key] = "#ffffff"
        elif p.type == "boolean":
            extremes[p.key] = True
    anim.update_params(extremes)
    for step in range(10):
        anim.render(1 + step * 0.2)
    # And minimums
    minimums = {p.key: (p.min if p.type == "number" else [[0, 0, 0]] if p.type == "colors" else "#000000" if p.type == "color" else False)
                for p in cls.PARAMS if p.type != "select"}
    anim.update_params(minimums)
    for step in range(10):
        anim.render(4 + step * 0.2)


def test_colors_param_enforces_min_items_and_hex_input():
    cls = registry.get("wave")
    params = cls.coerce_params({"colors": ["#ff0000"]})     # wave requires >= 2
    assert len(params["colors"]) >= 2
    assert params["colors"][0] == (255, 0, 0)


def test_unknown_select_falls_back_to_default():
    cls = registry.get("rainbow")
    assert cls.coerce_params({"mode": "bogus"})["mode"] == "spiral"


def test_number_is_clamped():
    cls = registry.get("chase")
    assert cls.coerce_params({"gap": 999})["gap"] == 8
    assert cls.coerce_params({"gap": -5})["gap"] == 2


def test_stop_is_instant_even_mid_sleep():
    import threading
    import time

    class Slow(Animation):
        PARAMS = []
        FPS = 1  # one-second frames

        def render(self, t):
            self.fill((1, 2, 3))

    controller = NeoPixelController(10, simulate=True)
    tree = TreeLayout([10])
    anim = Slow(controller, tree, {}, fps=1)
    th = threading.Thread(target=anim.run_animation, daemon=True)
    th.start()
    time.sleep(0.05)
    t0 = time.monotonic()
    anim.stop()
    th.join(timeout=2)
    assert not th.is_alive()
    assert time.monotonic() - t0 < 0.5


def test_old_preset_params_are_ignored_not_clamped():
    """Params whose units changed were renamed so saved presets fall back to defaults instead of extremes."""
    fw = registry.get("fireworks").coerce_params({"size": 14})
    assert "size" not in fw and fw["burst"] == 0.7
    ic = registry.get("icicles").coerce_params({"length": 5})
    assert "length" not in ic and ic["drip_length"] == 0.18
