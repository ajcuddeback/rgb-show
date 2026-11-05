import os
import sys

import pytest

SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from config import Config  # noqa: E402
from app import create_app  # noqa: E402


@pytest.fixture
def config(tmp_path):
    return Config(
        num_pixels=100, simulate=True, autostart=False, fps=60,
        state_file=str(tmp_path / "state.json"), presets_file=str(tmp_path / "presets.json"),
    )


@pytest.fixture
def app(config):
    application = create_app(config)
    yield application
    application.extensions["rgb"]["engine"].shutdown()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def engine(app):
    return app.extensions["rgb"]["engine"]


@pytest.fixture
def controller(app):
    return app.extensions["rgb"]["controller"]
