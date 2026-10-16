"""Measure how well PulseOps works on many simulated incidents.

For every fault kind and every service, we run several seeds and check:
- detection rate: did we notice anything at all?
- time to detect: minutes between the fault starting and our first anomaly
- top-1 / top-3: was the real root cause our #1 guess / in our top 3?
We also run healthy scenarios to count false alarms.

Run it with:  uv run python -m pulseops.evaluate
"""

import json
from pathlib import Path

from pulseops.detector import detect
from pulseops.rca import rank_suspects
from pulseops.services import SERVICES
from pulseops.simulator import FAULTS, make_scenario


def evaluate_kind(kind: str, seeds: range) -> dict:
    """Scores for one fault kind, across all services and seeds."""
    runs = detected = top1 = top3 = 0
    detect_times = []

    for service in SERVICES:
        for seed in seeds:
            scenario = make_scenario(kind, service, seed)
            anomalies = detect(scenario.metrics)
            suspects = rank_suspects(anomalies, scenario.deploys)
            runs += 1

            if not anomalies:
                continue
            detected += 1
            detect_times.append(anomalies[0].start - scenario.fault.start)

            ranked = [s.service for s in suspects]
            top1 += ranked[:1] == [service]
            top3 += service in ranked[:3]

    return {
        "fault": kind,
        "runs": runs,
        "detection_rate": detected / runs,
        "mean_minutes_to_detect": sum(detect_times) / len(detect_times) if detect_times else None,
        "top1_accuracy": top1 / runs,
        "top3_accuracy": top3 / runs,
    }


def false_alarm_rate(seeds: range) -> float:
    """Share of healthy scenarios where we still raised an anomaly."""
    alarms = sum(1 for seed in seeds if detect(make_scenario(None, seed=seed).metrics))
    return alarms / len(seeds)


def run_evaluation(seeds_per_case: int = 20) -> dict:
    seeds = range(seeds_per_case)
    rows = [evaluate_kind(kind, seeds) for kind in FAULTS]
    total_runs = sum(r["runs"] for r in rows)
    overall = {
        "fault": "all",
        "runs": total_runs,
        "detection_rate": sum(r["detection_rate"] * r["runs"] for r in rows) / total_runs,
        "mean_minutes_to_detect": sum(r["mean_minutes_to_detect"] * r["runs"] for r in rows)
        / total_runs,
        "top1_accuracy": sum(r["top1_accuracy"] * r["runs"] for r in rows) / total_runs,
        "top3_accuracy": sum(r["top3_accuracy"] * r["runs"] for r in rows) / total_runs,
    }
    # Healthy runs use different seeds so they don't repeat the fault runs' noise.
    healthy_seeds = range(1000, 1000 + seeds_per_case * 5)
    return {
        "rows": rows + [overall],
        "false_alarm_rate": false_alarm_rate(healthy_seeds),
        "healthy_runs": len(healthy_seeds),
    }


def to_markdown(results: dict) -> str:
    lines = [
        "| Fault | Runs | Detected | Minutes to detect | Top-1 root cause | Top-3 root cause |",
        "|---|---|---|---|---|---|",
    ]
    for r in results["rows"]:
        lines.append(
            f"| {r['fault']} | {r['runs']} | {r['detection_rate']:.0%} | "
            f"{r['mean_minutes_to_detect']:.1f} | {r['top1_accuracy']:.0%} | "
            f"{r['top3_accuracy']:.0%} |"
        )
    lines.append("")
    lines.append(
        f"False alarms on {results['healthy_runs']} healthy runs: {results['false_alarm_rate']:.0%}"
    )
    return "\n".join(lines)


def main() -> None:
    results = run_evaluation()
    print(to_markdown(results))
    Path("results").mkdir(exist_ok=True)
    Path("results/eval.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\nSaved to results/eval.json")


if __name__ == "__main__":
    main()
