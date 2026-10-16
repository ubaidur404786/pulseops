# Architecture

Diagram: [`architecture.svg`](architecture.svg)

## The pipeline

```
simulator ──► detector ──► rca ──► report ──► app (approve / reject) ──► audit log
   │                                                   ▲
   └── truth (the real root cause) ──► evaluate ───────┘ (same pipeline, many runs)
```

| File | Input | Output |
|---|---|---|
| `services.py` | — | the service list, who calls whom, normal metric levels |
| `simulator.py` | fault kind, target service, seed | `Scenario`: metrics table, deploy events, true root cause |
| `detector.py` | metrics table | list of `Anomaly` (service, metric, start step, peak z) |
| `rca.py` | anomalies, deploys | ranked list of `Suspect` (service, score, reasons) |
| `report.py` | suspects, anomalies, runbook | incident report text + proposed action |
| `audit.py` | a decision | one line appended to `audit_log.jsonl` |
| `evaluate.py` | number of runs, seed | detection + root-cause metrics |
| `app.py` | user clicks | the Streamlit page |

## Service map

```
gateway ──► orders ──► payments ──► database
   │          └──────────────────► database
   └──► inventory ───────────────► database
```

A fault in a service also shows up, weaker and a bit later, in every service that
calls it. That's why "the first broken service whose dependencies look healthy" is a
good root-cause guess.

## Metrics

Every service has `latency_ms`, `error_rate` and `cpu`, one value per minute
(120 minutes per scenario, first 30 used as the normal baseline).
