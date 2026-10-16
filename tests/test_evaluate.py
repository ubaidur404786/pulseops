"""Quality gate: CI fails if root-cause accuracy drops below these levels.

The thresholds sit a bit under the current numbers, so a change that makes
PulseOps worse gets caught, but normal small changes don't break the build.
"""

from pulseops.evaluate import run_evaluation

TOP1_MIN = 0.80
DETECTION_MIN = 0.95
FALSE_ALARM_MAX = 0.05


def test_quality_gate():
    results = run_evaluation(seeds_per_case=5)
    overall = results["rows"][-1]
    assert overall["detection_rate"] >= DETECTION_MIN
    assert overall["top1_accuracy"] >= TOP1_MIN
    assert results["false_alarm_rate"] <= FALSE_ALARM_MAX
