from pulseops.audit import log_decision, read_log
from pulseops.detector import Anomaly
from pulseops.rca import Suspect
from pulseops.report import build_report, read_action


def test_every_service_has_a_runbook_action():
    for service in ["gateway", "orders", "payments", "inventory", "database"]:
        action, runbook = read_action(service)
        assert runbook == f"{service}.md"
        assert "manually" not in action


def test_report_names_top_suspect_and_action(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    anomalies = [Anomaly("database", "latency_ms", start=50, peak_z=30)]
    suspects = [Suspect("database", 3.0, 50, ["it was the first to go wrong (minute 50)"])]
    report = build_report(anomalies, suspects)
    assert "database" in report.text
    assert report.runbook == "database.md"
    assert report.action in report.text


def test_healthy_report_has_no_action():
    report = build_report([], [])
    assert report.action == ""


def test_audit_log_appends_and_reads_back(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    log_decision("inc-1", "orders", "Roll back", "approved", log_file)
    log_decision("inc-2", "payments", "Roll back", "rejected", log_file)
    entries = read_log(log_file)
    assert [e["decision"] for e in entries] == ["approved", "rejected"]
