# Decisions

Each entry: what we picked, why, and what else we looked at. Newest at the bottom.
Don't reopen a decision unless something new comes up — add a new entry instead.

## D-001 — Simulated telemetry first, real services later

**Picked:** a Python simulator that generates metrics for 5 services and injects faults
with a known root cause.
**Why:** evaluation needs ground truth. With real services I'd have to label every
incident by hand. The simulator gives me hundreds of labelled incidents in seconds,
so "top-1 root-cause accuracy" is a real, repeatable number.
**Considered:** Docker Compose microservices + Prometheus from day one. More realistic,
but 3–4x the work before I can measure anything. Moved to a later phase.

## D-002 — Rolling z-score detector with a persistence check

**Picked:** learn mean/std per metric from a warm-up window, flag a metric when
|z| > 4 for 3 steps in a row.
**Why:** I can explain it in one sentence, it has no training step, and the
persistence check removes most one-off noise spikes.
**Considered:** Isolation Forest, autoencoder. Better for complex seasonality, but
harder to explain and not needed for this data. Can be swapped in later because the
detector only has to return a list of `Anomaly` objects.

## D-003 — Rule-based root-cause ranking, not an LLM

**Picked:** score each anomalous service with three simple rules: (1) none of the
services it depends on look broken, (2) it went wrong first, (3) it was deployed just
before the problem started. Every point comes with a written reason.
**Why:** it's deterministic, testable and every score is explainable. An LLM picking
the root cause would be hard to evaluate and could make things up.
**Considered:** letting an LLM read all metrics and guess. Kept the LLM only for
writing the summary text (D-004).

## D-004 — Report is a template; a local LLM is optional

**Picked:** a plain text template by default. If `OLLAMA_MODEL` is set, the same
evidence is sent to a local Ollama model to write a friendlier summary.
**Why:** free, works offline, no API keys, nothing leaves the machine. The app and the
tests never depend on the LLM being there.
**Considered:** hosted free-tier APIs (Groq, Gemini). Fine too, but adds keys and rate
limits for no gain at this stage.

## D-005 — Human approval + JSONL audit log

**Picked:** the tool only *proposes* a runbook action. A person clicks Approve or
Reject, and every decision is appended to `audit_log.jsonl`.
**Why:** this is how real teams treat automated remediation. A JSONL file is enough
and easy to inspect.
**Considered:** SQLite. Not needed yet.

## D-006 — Streamlit for the UI

**Picked:** one Streamlit page.
**Why:** pure Python, free hosting on Streamlit Community Cloud, no separate frontend.
**Considered:** FastAPI + React. Much more code for the same demo.

## D-007 — Tooling: uv, ruff, pytest. No mypy for now.

**Why:** fewer moving parts. Type hints are still written; mypy can be added later
if the codebase grows.

## D-008 — One data notebook, committed with its outputs

**Picked:** `notebooks/01_data.ipynb` explains the whole data side (metrics, healthy vs
fault, domino effect, real-world source) and writes `data/*.csv` and
`docs/figures/*.png`. Outputs are committed so GitHub shows the plots without running it.
**Why:** one place a reader can learn the domain; the README figures come from real
simulator output, not drawings.
**Considered:** explaining it only in the README (too long), or plots generated in CI
(more moving parts). The notebook's libraries live in an optional `notebook` group, so
the app, Docker image and CI don't install them.

## D-009 — Host the whole Streamlit app on Render, no separate frontend

**What:** One Docker container on Render's free web plan runs the Streamlit app, which
is both the UI and the pipeline. GitHub holds the code and runs CI; it doesn't host a
frontend.

**Why:** Streamlit renders the page from Python on the server, so there is no static
frontend to split off. A GitHub Pages frontend would need a new JavaScript UI plus an
HTTP API in front of the pipeline: two new pieces, more to defend, no new skill shown
that matters for this project. The Dockerfile already exists, so Render reuses it as-is.

**Considered:** GitHub Pages + FastAPI backend on Render (too much new surface);
Streamlit Community Cloud (works, but Render with Docker proves the container runs).

**Cost:** free plan sleeps after idle time, and the disk resets on redeploy, so the audit
log is not durable online.
