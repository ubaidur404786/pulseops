"""Keep a record of every approve/reject decision (see decisions.md, D-005).

One JSON object per line, so the file is easy to read and to append to.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

LOG_FILE = Path("audit_log.jsonl")


def log_decision(
    incident: str, service: str, action: str, decision: str, log_file: Path = LOG_FILE
) -> dict:
    """Append one decision to the log and return what was written."""
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be 'approved' or 'rejected'")

    entry = {
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "incident": incident,
        "service": service,
        "action": action,
        "decision": decision,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_log(log_file: Path = LOG_FILE) -> list[dict]:
    """All past decisions, oldest first."""
    if not log_file.exists():
        return []
    lines = log_file.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]
