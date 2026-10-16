"""The pretend system we're monitoring: which services exist and who calls whom."""

SERVICES = ["gateway", "orders", "payments", "inventory", "database"]

# DEPENDS_ON[x] = the services that x calls.
DEPENDS_ON = {
    "gateway": ["orders", "inventory"],
    "orders": ["payments", "database"],
    "payments": ["database"],
    "inventory": ["database"],
    "database": [],
}

METRICS = ["latency_ms", "error_rate", "cpu"]

# Normal level and noise (standard deviation) for each metric.
NORMAL = {
    "latency_ms": (120.0, 8.0),
    "error_rate": (0.01, 0.003),
    "cpu": (40.0, 4.0),
}


def callers_of(service: str) -> list[str]:
    """Services that call `service` directly."""
    return [name for name, deps in DEPENDS_ON.items() if service in deps]


def column(service: str, metric: str) -> str:
    """Column name used in the metrics table, e.g. 'orders.latency_ms'."""
    return f"{service}.{metric}"
