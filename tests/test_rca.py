from pulseops.detector import Anomaly, detect
from pulseops.rca import rank_suspects
from pulseops.simulator import Deploy, make_scenario


def test_no_anomalies_means_no_suspects():
    assert rank_suspects([], []) == []


def test_service_with_healthy_dependencies_wins():
    # payments broke first, orders and gateway (its callers) followed.
    anomalies = [
        Anomaly("payments", "error_rate", start=50, peak_z=40),
        Anomaly("orders", "error_rate", start=51, peak_z=20),
        Anomaly("gateway", "error_rate", start=53, peak_z=10),
    ]
    suspects = rank_suspects(anomalies, deploys=[])
    assert suspects[0].service == "payments"
    assert suspects[0].reasons  # every score must come with a reason


def test_recent_deploy_adds_points():
    anomalies = [Anomaly("orders", "error_rate", start=60, peak_z=30)]
    with_deploy = rank_suspects(anomalies, [Deploy("orders", step=57)])
    without = rank_suspects(anomalies, [])
    assert with_deploy[0].score > without[0].score


def test_end_to_end_database_fault():
    scenario = make_scenario("slow_queries", "database", seed=11)
    suspects = rank_suspects(detect(scenario.metrics), scenario.deploys)
    assert suspects[0].service == "database"
