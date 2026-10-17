"""Checks for the small console tools and the game-length format."""

import importlib.util
import pathlib
import random

from sc2um.replay import format_length

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_win_rate_simulator_defaults_to_neutral_coin():
    sim = _load("win_rate_simulator")
    assert sim.simulate_matchup.__defaults__[0] == 0.5
    assert "not a measure" in sim.__doc__
    share = sim.simulate_matchup(games=2000, rng=random.Random(0))
    assert 0.45 < share < 0.55


def test_lattice_visualizer_uses_valid_colour():
    source = (ROOT / "tools" / "lattice_visualizer.py").read_text(encoding="utf-8")
    assert "powrush_blue" not in source
    assert 'node_color="#1f4e9c"' in source


def test_format_length_uses_colons():
    class FakeLength:
        def __init__(self, text):
            self.text = text

        def __str__(self):
            return self.text

    assert format_length(FakeLength("07.48")) == "07:48"
    assert format_length(FakeLength("01.02.03")) == "01:02:03"
    assert format_length(None) is None
