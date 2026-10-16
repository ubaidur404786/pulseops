"""Generate fake metrics for our services, optionally with one injected fault.

Because we inject the fault ourselves, we always know the real root cause.
That's what makes evaluation possible (see decisions.md, D-001).
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from pulseops.services import METRICS, NORMAL, SERVICES, callers_of, column

STEPS = 120  # one step = one minute

# How much each fault pushes the metrics of the broken service.
FAULTS = {
    "slow_queries": {"latency_ms": 250.0, "cpu": 30.0},
    "error_burst": {"error_rate": 0.15},
    "cpu_saturation": {"cpu": 45.0, "latency_ms": 120.0},
    "bad_deploy": {"error_rate": 0.12, "latency_ms": 80.0},
}

# Only these metrics leak into the callers. CPU stays local to the broken service.
PROPAGATES = {"latency_ms", "error_rate"}


@dataclass
class Fault:
    kind: str
    service: str
    start: int
    severity: float = 1.0  # 1.0 = full strength, 0.2 = a mild problem that's hard to spot


@dataclass
class Deploy:
    service: str
    step: int


@dataclass
class Scenario:
    metrics: pd.DataFrame  # one row per step, one column per "service.metric"
    deploys: list[Deploy] = field(default_factory=list)
    fault: Fault | None = None  # the truth; None means a normal, healthy run


def normal_metrics(rng: np.random.Generator) -> pd.DataFrame:
    """Healthy metrics: normal level plus random noise."""
    data = {}
    for service in SERVICES:
        for metric in METRICS:
            mean, std = NORMAL[metric]
            values = rng.normal(mean, std, STEPS)
            # Real metrics have short blips (a GC pause, one slow request).
            # They last 1-2 minutes and should NOT be reported as incidents.
            if rng.random() < 0.3:
                blip_at = int(rng.integers(30, STEPS - 2))
                values[blip_at : blip_at + int(rng.integers(1, 3))] += std * rng.uniform(5, 8)
            data[column(service, metric)] = values
    return pd.DataFrame(data)


def affected_services(service: str, rng: np.random.Generator) -> list[tuple[str, int, int]]:
    """Walk up the call graph from the broken service.

    Returns (service, hops_away, delay_in_steps). Callers feel the problem later
    and weaker the further away they are.
    """
    result = [(service, 0, 0)]
    seen = {service}
    queue = [(service, 0, 0)]
    while queue:
        current, hops, delay = queue.pop(0)
        for caller in callers_of(current):
            if caller in seen:
                continue
            seen.add(caller)
            # 0 = same minute (requests time out right away), up to 2 minutes later.
            caller_delay = delay + int(rng.integers(0, 3))
            result.append((caller, hops + 1, caller_delay))
            queue.append((caller, hops + 1, caller_delay))
    return result


def inject_fault(metrics: pd.DataFrame, fault: Fault, rng: np.random.Generator) -> None:
    """Add the fault's effect to the metrics table (changes it in place).

    Problems don't appear all at once: the effect ramps up over a few minutes.
    """
    ramp_minutes = int(rng.integers(3, 10))
    steps = np.arange(STEPS)
    for service, hops, delay in affected_services(fault.service, rng):
        strength = fault.severity * 0.6**hops
        # 0 before the start, then climbs to 1 over `ramp_minutes`.
        ramp = np.clip((steps - (fault.start + delay) + 1) / ramp_minutes, 0, 1)
        for metric, bump in FAULTS[fault.kind].items():
            if hops > 0 and metric not in PROPAGATES:
                continue
            metrics[column(service, metric)] += bump * strength * ramp


def random_deploys(rng: np.random.Generator, count: int) -> list[Deploy]:
    """Harmless deploys that happen anyway. They make root-cause ranking harder."""
    return [
        Deploy(service=str(rng.choice(SERVICES)), step=int(rng.integers(30, STEPS)))
        for _ in range(count)
    ]


def make_scenario(kind: str | None = None, service: str | None = None, seed: int = 0) -> Scenario:
    """Build one scenario.

    kind=None gives a healthy run. If kind is set but service isn't, a random
    service is picked as the root cause.
    """
    rng = np.random.default_rng(seed)
    metrics = normal_metrics(rng)
    deploys = random_deploys(rng, count=int(rng.integers(0, 3)))

    if kind is None:
        return Scenario(metrics=metrics, deploys=deploys)

    if kind not in FAULTS:
        raise ValueError(f"Unknown fault kind: {kind}. Choose from {list(FAULTS)}")
    if service is None:
        service = str(rng.choice(SERVICES))

    fault = Fault(
        kind=kind,
        service=service,
        start=int(rng.integers(45, 90)),
        severity=float(rng.uniform(0.1, 1.0)),
    )
    inject_fault(metrics, fault, rng)

    # A bad deploy is, well, a deploy. It lands a few minutes before things break.
    if kind == "bad_deploy":
        deploys.append(Deploy(service=service, step=fault.start - int(rng.integers(1, 5))))

    return Scenario(metrics=metrics, deploys=deploys, fault=fault)
