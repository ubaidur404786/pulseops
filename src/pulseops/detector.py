"""Find anomalies with a simple z-score check (see decisions.md, D-002).

Idea: learn what "normal" looks like from the first minutes, then flag a metric
when it stays far away from normal for a few minutes in a row.
"""

from dataclasses import dataclass

import pandas as pd

WARMUP = 30  # first 30 minutes are treated as the healthy baseline
Z_LIMIT = 4.0  # how many standard deviations away counts as "weird"
PERSIST = 3  # how many minutes in a row it has to stay weird


@dataclass
class Anomaly:
    service: str
    metric: str
    start: int  # first step of the weird streak
    peak_z: float


def zscores(values: pd.Series) -> pd.Series:
    """How far each value is from the warm-up baseline, in standard deviations."""
    baseline = values.iloc[:WARMUP]
    # A tiny std would make every small wiggle look huge, so put a floor on it.
    std = max(baseline.std(), 1e-6, abs(baseline.mean()) * 0.01)
    return (values - baseline.mean()) / std


def first_streak(flags: pd.Series, length: int) -> int | None:
    """Index where `flags` is True for `length` steps in a row, or None."""
    run = 0
    for step, flagged in flags.items():
        run = run + 1 if flagged else 0
        if run == length:
            return int(step) - length + 1
    return None


def detect(metrics: pd.DataFrame) -> list[Anomaly]:
    """Check every metric column and return the ones that went wrong, earliest first."""
    anomalies = []
    for name in metrics.columns:
        z = zscores(metrics[name])
        after_warmup = z.iloc[WARMUP:]
        start = first_streak(after_warmup.abs() > Z_LIMIT, PERSIST)
        if start is None:
            continue
        service, metric = name.split(".")
        peak = float(after_warmup.abs().max())
        anomalies.append(Anomaly(service=service, metric=metric, start=start, peak_z=peak))
    return sorted(anomalies, key=lambda a: a.start)
