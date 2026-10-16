"""Run the whole PulseOps flow in the terminal, one step at a time.

Use it to see what each file produces, or put a breakpoint on any step in your IDE.

    uv run python scripts/debug_flow.py                      # database error burst
    uv run python scripts/debug_flow.py slow_queries payments 3
    uv run python scripts/debug_flow.py healthy               # no fault
"""

import sys
from pathlib import Path

from pulseops.audit import log_decision, read_log
from pulseops.detector import WARMUP, detect, zscores
from pulseops.rca import rank_suspects
from pulseops.report import build_report
from pulseops.services import DEPENDS_ON
from pulseops.simulator import make_scenario

kind = sys.argv[1] if len(sys.argv) > 1 else "error_burst"
service = sys.argv[2] if len(sys.argv) > 2 else "database"
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
if kind == "healthy":
    kind, service = None, None


def title(text: str) -> None:
    print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")


# Step 0: the service map (services.py)
title("STEP 0  services.py -> who calls whom")
for name, deps in DEPENDS_ON.items():
    print(f"  {name:10} calls {deps or 'nothing'}")

# Step 1: fake telemetry with one hidden fault (simulator.py)
title("STEP 1  simulator.py -> 120 minutes of metrics")
scenario = make_scenario(kind, service, seed)
print(f"  table shape: {scenario.metrics.shape} (rows = minutes, columns = service.metric)")
print(f"  deploys: {scenario.deploys}")
print(f"  hidden truth: {scenario.fault}")
if scenario.fault:
    col = f"{scenario.fault.service}.error_rate"
    start = scenario.fault.start
    print(f"\n  {col} around the fault start (minute {start}):")
    print(scenario.metrics[col].iloc[start - 3 : start + 8].round(3).to_string())

# Step 2: find what looks weird (detector.py)
title("STEP 2  detector.py -> anomalies")
if scenario.fault:
    z = zscores(scenario.metrics[col])
    print(f"  z-scores of {col} (normal is between -4 and 4):")
    print(z.iloc[start - 3 : start + 8].round(1).to_string())
anomalies = detect(scenario.metrics)
print(f"\n  {len(anomalies)} anomalies (baseline = first {WARMUP} minutes):")
for a in anomalies:
    print(f"  - {a.service}.{a.metric} from minute {a.start}, peak z = {a.peak_z:.0f}")

# Step 3: who is the root cause? (rca.py)
title("STEP 3  rca.py -> ranked suspects")
suspects = rank_suspects(anomalies, scenario.deploys)
for s in suspects:
    print(f"  {s.service:10} score {s.score}  reasons: {s.reasons}")

# Step 4: report + proposed action (report.py + runbooks/)
title("STEP 4  report.py -> report for the engineer")
report = build_report(anomalies, suspects)
print(report.text)

# Step 5: human decision (audit.py). Written to a separate file so the real log stays clean.
title("STEP 5  audit.py -> approve and log it")
if suspects:
    log_file = Path("debug_audit_log.jsonl")
    log_decision(f"debug-seed-{seed}", suspects[0].service, report.action, "approved", log_file)
    print(f"  last entry in {log_file}: {read_log(log_file)[-1]}")

# Did we get it right?
title("RESULT")
if scenario.fault is None:
    print(f"  healthy run -> {'correct, no alarm' if not anomalies else 'FALSE ALARM'}")
elif suspects:
    hit = suspects[0].service == scenario.fault.service
    print(f"  truth: {scenario.fault.service} | our #1: {suspects[0].service} -> {hit}")
else:
    print("  MISSED: the fault was too weak to detect")
