import base64
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _decode(name: str, tmp_path_factory) -> str:
    """Fixtures are stored base64-encoded; decode to a real .SC2Replay file."""
    data = base64.b64decode((FIXTURES / f"{name}.SC2Replay.b64").read_text())
    out = tmp_path_factory.mktemp("replays") / f"{name}.SC2Replay"
    out.write_bytes(data)
    return os.fspath(out)


@pytest.fixture(scope="session")
def replay_1v1(tmp_path_factory):
    return _decode("lotv_1v1_pvp", tmp_path_factory)


@pytest.fixture(scope="session")
def replay_2v2(tmp_path_factory):
    return _decode("lotv_2v2", tmp_path_factory)
