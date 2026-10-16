import pytest

from pulseops.simulator import STEPS, make_scenario


def test_healthy_scenario_has_no_fault():
    scenario = make_scenario(None, seed=1)
    assert scenario.fault is None
    assert len(scenario.metrics) == STEPS


def test_same_seed_gives_same_data():
    a = make_scenario("error_burst", "payments", seed=3)
    b = make_scenario("error_burst", "payments", seed=3)
    assert a.metrics.equals(b.metrics)


def test_fault_raises_the_broken_metric():
    scenario = make_scenario("slow_queries", "database", seed=2)
    latency = scenario.metrics["database.latency_ms"]
    start = scenario.fault.start
    assert latency.iloc[start:].mean() > latency.iloc[:start].mean() + 100


def test_fault_leaks_into_callers_but_not_unrelated_services():
    scenario = make_scenario("error_burst", "payments", seed=4)
    start = scenario.fault.start
    orders = scenario.metrics["orders.error_rate"]
    inventory = scenario.metrics["inventory.error_rate"]  # inventory never calls payments
    assert orders.iloc[start + 5 :].mean() > orders.iloc[:start].mean() + 0.05
    assert abs(inventory.iloc[start + 5 :].mean() - inventory.iloc[:start].mean()) < 0.01


def test_bad_deploy_adds_a_deploy_before_the_fault():
    scenario = make_scenario("bad_deploy", "orders", seed=5)
    deploys = [d for d in scenario.deploys if d.service == "orders"]
    assert any(d.step < scenario.fault.start for d in deploys)


def test_unknown_fault_kind_fails_loudly():
    with pytest.raises(ValueError):
        make_scenario("meteor_strike", "gateway")
