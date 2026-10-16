# PulseOps

**Finds which service broke, explains why, and asks a human before fixing anything.**

> **Status: work in progress.** The core pipeline works and is measured. Demo video and
> real Prometheus data are still being added.

## The problem

When something breaks in a system made of many services, the alerts go off everywhere
at once. The payments service fails, so orders fail, so the gateway fails, and the
on-call engineer gets three alerts that all look like "the problem". A lot of the
incident time goes into working out *which* service actually started it.

## The solution

1. **Watch metrics**: latency, error rate and CPU for every service, every minute.
2. **Spot anomalies** with a z-score check: the first 30 minutes give each metric's
   normal mean and spread; a value more than 4 standard deviations away for 3 minutes
   in a row is an anomaly, so one-off blips are ignored. No training needed.
3. **Rank the likely root cause** with three rules anyone can check:
   - none of the services it calls look broken,
   - it went wrong first,
   - it was deployed just before the trouble started.

   Every score comes with a written reason. Rules, not an LLM, because they give the
   same answer every time, can be unit-tested, and can't invent causes.
4. **Propose a fix** from that service's runbook.
5. **Wait for a human.** The engineer approves or rejects, and every decision is
   written to an audit log. Nothing runs on its own.

## Live app

**https://pulseops-ecck.onrender.com** (free plan: the first load can take ~1 minute)

![PulseOps dashboard: a database error burst, traced to its root cause](docs/figures/dashboard.png)

**How to use it:** pick a **Fault type** and a **Broken service** in the sidebar (try
`error_burst` on `database`). The summary tiles and the service status table show what
PulseOps found; the **Root cause** tab gives the reasons; **Response** lets you approve
or reject the fix. The "Ground truth" box shows the real answer, so you can check
PulseOps. A step-by-step guide is built into the app, the sidebar switches between dark
and light ([light screenshot](docs/figures/dashboard-light.png)), and a link like
`?fault=error_burst&service=database&theme=light` opens a scenario directly.

## The data

> Full walk-through, from zero: [notebooks/01_data.ipynb](notebooks/01_data.ipynb).

**The system.** A small online shop made of 5 services. An arrow means "calls":

```
gateway ──> orders ──> payments ──> database
   └──────> inventory ─────────────> database
```

**What we measure.** Every minute, 3 numbers per service: `latency_ms` (how slow),
`error_rate` (share of failed requests) and `cpu` (how busy). So one scenario is a table
of **120 minutes × 15 columns** (`service.metric`, e.g. `database.error_rate`).

**Healthy.** Numbers wiggle around a normal level (x = minute, y = share of failed requests):

![Healthy run](docs/figures/01_healthy.png)

**Before vs after a fault.** The same metric, healthy (grey) and with the database
broken (red). It ramps up over a few minutes and *stays* up, unlike a short blip:

![Before vs after](docs/figures/02_before_after.png)

**The domino effect.** Everything that calls the database goes red too, a bit weaker
and a bit later. Five alarms, one real cause:

![Domino effect](docs/figures/03_domino.png)

**Where the data comes from.** A simulator ([`simulator.py`](src/pulseops/simulator.py))
makes a healthy table, then adds a fault on top (slow queries, error burst, CPU
saturation or bad deploy) with random strength. Because the fault is injected, the true
root cause is always known, so accuracy can be measured. In a real company the same
table would come from **Prometheus** and deploy events from the CI/CD tool. That's the
next phase, not built yet.

Sample files are in [`data/`](data/) (`labels.csv` holds the true answer for each).
Rebuild them and the figures with:

```bash
uv sync --group notebook
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_data.ipynb
```

## Results

Measured on 400 simulated incidents (4 fault types × 5 services × 20 seeds) plus
100 healthy runs. Faults have random strength (10–100%), ramp up over 3–9 minutes,
and spread to the calling services with a 0–2 minute delay.

| Fault | Runs | Detected | Minutes to detect | Top-1 root cause | Top-3 root cause |
|---|---|---|---|---|---|
| slow_queries | 100 | 100% | 1.9 | 100% | 100% |
| error_burst | 100 | 100% | 0.6 | 100% | 100% |
| cpu_saturation | 100 | 93% | 3.5 | 93% | 93% |
| bad_deploy | 100 | 100% | 0.8 | 100% | 100% |
| all | 400 | 98% | 1.7 | 98% | 98% |

False alarms on 100 healthy runs: 0%. Reproduce with `uv run python -m pulseops.evaluate`.

**Read these numbers carefully.** Faults spread cleanly along a known service map, so
the ranking rules have an easy job. The misses are mild CPU faults that never rise above
the noise. Real systems are messier (retries, shared infrastructure, missing metrics),
so expect lower accuracy there.

## Architecture

![Architecture](docs/architecture.svg)

| File | Job |
|---|---|
| `services.py` | the service map and normal metric levels |
| `simulator.py` | generates metrics and injects faults with a known root cause |
| `detector.py` | z-score anomaly detection |
| `rca.py` | ranks root-cause suspects, with reasons |
| `report.py` | writes the incident report and picks the runbook action |
| `audit.py` | logs approve / reject decisions |
| `evaluate.py` | runs hundreds of scenarios and measures accuracy |
| `app.py`, `ui.py` | Streamlit dashboard and its styling |

**Delivery.** GitHub Actions runs lint, tests and a quality gate
(`tests/test_evaluate.py` fails the build if accuracy drops), then builds the Docker
image. Render builds the same Dockerfile ([`render.yaml`](render.yaml)) and hosts the app.

More detail: [docs/architecture.md](docs/architecture.md) ·
design choices: [docs/decisions.md](docs/decisions.md)

## Run it locally

Needs Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ubaidur404786/pulseops.git
cd pulseops
uv sync
uv run streamlit run src/pulseops/app.py
```

Or with Docker (the same image Render runs):

```bash
docker build -t pulseops .
docker run -p 8501:8501 pulseops
```

Tests and evaluation:

```bash
uv run pytest
uv run python -m pulseops.evaluate
```

**Optional LLM summary.** With [Ollama](https://ollama.com) running locally, set
`OLLAMA_MODEL` (see `.env.example`) and a local model rewrites the report in friendlier
words. It only gets the evidence PulseOps found; it doesn't choose the root cause.

## Known limitations

- **Simulated data only.** No real services or Prometheus yet.
- One fault at a time. Two overlapping incidents aren't handled.
- The detector uses a fixed baseline. It can't handle daily traffic patterns.
- Runbooks are per service, not per fault type, so the proposed action is sometimes
  generic.
- Approving an action only logs it. Nothing is actually executed.
- The local-LLM summary hasn't been tested yet.
- On Render's free plan the app sleeps when idle and the audit log resets on every
  redeploy.
- Demo video not recorded yet.

## Contact

Questions about the design or the numbers? Reach me on [LinkedIn](https://www.linkedin.com/in/ubaid-ur-rehman-422212177/)
or open an issue.

## License

MIT
