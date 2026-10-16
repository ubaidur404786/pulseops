"""Rank which service most likely caused the incident (see decisions.md, D-003).

Each anomalous service gets points from three simple rules, and every point comes
with a reason we can show to the engineer:

1. +2 if none of the services it calls look broken (problem starts here, not below).
2. +1 if it went wrong first.
3. +1.5 if it was deployed shortly before its metrics went wrong.
"""

from dataclasses import dataclass, field

from pulseops.detector import Anomaly
from pulseops.services import DEPENDS_ON
from pulseops.simulator import Deploy

DEPLOY_WINDOW = 10  # a deploy up to 10 minutes before the problem counts as "recent"


@dataclass
class Suspect:
    service: str
    score: float
    start: int
    reasons: list[str] = field(default_factory=list)


def rank_suspects(anomalies: list[Anomaly], deploys: list[Deploy]) -> list[Suspect]:
    """Return suspects sorted from most to least likely."""
    if not anomalies:
        return []

    # When did each service first go wrong?
    first_seen: dict[str, int] = {}
    for anomaly in anomalies:
        if anomaly.service not in first_seen or anomaly.start < first_seen[anomaly.service]:
            first_seen[anomaly.service] = anomaly.start

    earliest = min(first_seen.values())
    suspects = []

    for service, start in first_seen.items():
        suspect = Suspect(service=service, score=0.0, start=start)

        broken_deps = [dep for dep in DEPENDS_ON[service] if dep in first_seen]
        if not broken_deps:
            suspect.score += 2
            suspect.reasons.append("none of the services it calls look broken")
        else:
            suspect.reasons.append(f"it calls services that are also broken: {broken_deps}")

        if start == earliest:
            suspect.score += 1
            suspect.reasons.append(f"it was the first to go wrong (minute {start})")

        for deploy in deploys:
            if deploy.service == service and 0 <= start - deploy.step <= DEPLOY_WINDOW:
                suspect.score += 1.5
                suspect.reasons.append(f"it was deployed at minute {deploy.step}")
                break

        suspects.append(suspect)

    # Highest score first; on a tie, whoever broke first.
    return sorted(suspects, key=lambda s: (-s.score, s.start))
