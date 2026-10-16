"""Turn the evidence into a short incident report (see decisions.md, D-004).

By default the report is a plain template, so it always works. If the OLLAMA_MODEL
environment variable is set, we ask a local Ollama model to rewrite it in nicer
words, using only the evidence we give it.
"""

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from pulseops.detector import Anomaly
from pulseops.rca import Suspect

RUNBOOK_DIR = Path(__file__).parent / "runbooks"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")


@dataclass
class Report:
    text: str
    action: str  # what we propose to do; needs human approval
    runbook: str  # which runbook file the action comes from


def read_action(service: str) -> tuple[str, str]:
    """Return (action, runbook file name) for a service.

    The action is the first line under '## Action' in the service's runbook.
    """
    path = RUNBOOK_DIR / f"{service}.md"
    if not path.exists():
        return "No runbook found. Investigate manually.", "none"

    lines = path.read_text(encoding="utf-8").splitlines()
    in_action = False
    for line in lines:
        if line.strip() == "## Action":
            in_action = True
        elif in_action and line.strip():
            return line.strip(), path.name
    return "Runbook has no action. Investigate manually.", path.name


def template_report(anomalies: list[Anomaly], suspects: list[Suspect]) -> Report:
    """Build the report from plain text pieces. No LLM involved."""
    if not suspects:
        return Report(text="No anomalies found. All services look normal.", action="", runbook="")

    top = suspects[0]
    action, runbook = read_action(top.service)

    lines = [f"Most likely root cause: **{top.service}** (score {top.score:.1f})", "", "Why:"]
    lines += [f"- {reason}" for reason in top.reasons]

    lines += ["", "What looked wrong (first 6):"]
    for anomaly in anomalies[:6]:
        lines.append(
            f"- {anomaly.service}.{anomaly.metric} from minute {anomaly.start} "
            f"(peak {anomaly.peak_z:.0f} std devs from normal)"
        )

    if len(suspects) > 1:
        others = ", ".join(f"{s.service} ({s.score:.1f})" for s in suspects[1:3])
        lines += ["", f"Other suspects: {others}"]

    lines += ["", f"Proposed action (from `{runbook}`): {action}"]
    return Report(text="\n".join(lines), action=action, runbook=runbook)


def ask_ollama(prompt: str, model: str) -> str:
    """Send a prompt to a local Ollama server and return its answer."""
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    request = urllib.request.Request(
        OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())["response"]


def build_report(anomalies: list[Anomaly], suspects: list[Suspect]) -> Report:
    """Template report, optionally rewritten by a local LLM."""
    report = template_report(anomalies, suspects)
    model = os.getenv("OLLAMA_MODEL")
    if not model or not suspects:
        return report

    prompt = (
        "You are helping an on-call engineer. Rewrite this incident evidence as a short, "
        "clear summary (max 120 words). Use ONLY the facts below. Do not invent causes, "
        "numbers or actions.\n\n" + report.text
    )
    try:
        report.text = ask_ollama(prompt, model) + "\n\n---\nEvidence:\n" + report.text
    except OSError:
        # Ollama isn't running. The template report is still fine.
        pass
    return report
