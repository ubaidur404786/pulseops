import pandas as pd

from pulseops.detector import detect, first_streak
from pulseops.simulator import make_scenario


def test_first_streak_needs_consecutive_steps():
    flags = pd.Series([False, True, False, True, True, True, False])
    assert first_streak(flags, 3) == 3
    assert first_streak(flags, 4) is None


def test_healthy_runs_raise_no_anomalies():
    for seed in range(10):
        assert detect(make_scenario(None, seed=seed).metrics) == []


def test_detects_the_broken_service_soon_after_the_fault():
    scenario = make_scenario("cpu_saturation", "inventory", seed=8)
    anomalies = detect(scenario.metrics)
    first = anomalies[0]
    assert first.service == "inventory"
    assert 0 <= first.start - scenario.fault.start <= 3
