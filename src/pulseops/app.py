"""PulseOps Streamlit dashboard.

Pick a fault, watch PulseOps find it, then approve or reject the proposed fix.
Run with:  uv run streamlit run src/pulseops/app.py
"""

import streamlit as st

from pulseops import ui
from pulseops.audit import log_decision, read_log
from pulseops.detector import detect
from pulseops.rca import rank_suspects
from pulseops.report import build_report
from pulseops.services import DEPENDS_ON, METRICS, SERVICES, column
from pulseops.simulator import FAULTS, make_scenario

HEALTHY = "none (healthy)"
METRIC_LABELS = {
    "latency_ms": "Latency (ms)",
    "error_rate": "Error rate (share of failed requests)",
    "cpu": "CPU usage (%)",
}
FAULT_HELP = {
    "slow_queries": "Requests get slower: latency goes up.",
    "error_burst": "Many requests fail: error rate goes up.",
    "cpu_saturation": "The machine is overloaded: CPU goes up. Doesn't spread.",
    "bad_deploy": "A new release breaks it. A deploy event appears just before.",
}

st.set_page_config(page_title="PulseOps", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)


def sidebar() -> tuple[str | None, str, int]:
    with st.sidebar:
        st.markdown("#### Scenario")
        st.caption("Choose what breaks. Everything below updates instantly.")
        # Optional link presets, e.g. ?fault=error_burst&service=database, so a scenario
        # can be shared (and screenshotted) without clicking.
        kinds = [HEALTHY, *FAULTS]
        preset_kind = st.query_params.get("fault", HEALTHY)
        preset_service = st.query_params.get("service", "database")
        kind = st.selectbox(
            "Fault type", kinds, index=kinds.index(preset_kind) if preset_kind in kinds else 0
        )
        if kind != HEALTHY:
            st.caption(FAULT_HELP[kind])
        service = st.selectbox(
            "Broken service",
            SERVICES,
            index=SERVICES.index(preset_service) if preset_service in SERVICES else 4,
            disabled=kind == HEALTHY,
        )
        seed = st.number_input(
            "Seed",
            min_value=0,
            value=7,
            step=1,
            help="Changes the random noise and fault strength. Same seed, same result.",
        )
        st.divider()
        st.markdown("#### Service map")
        st.caption("An arrow means *calls*.")
        st.markdown(
            "- **gateway** → orders, inventory\n"
            "- **orders** → payments, database\n"
            "- **payments** → database\n"
            "- **inventory** → database"
        )
        st.divider()
        st.markdown(
            "[Source code](https://github.com/ubaidur404786/pulseops) · "
            "[Data notebook](https://github.com/ubaidur404786/pulseops/blob/main/notebooks/01_data.ipynb)"
        )
        st.caption("Demo with simulated data · work in progress")
    fault_kind = None if kind == HEALTHY else kind
    return fault_kind, service, int(seed)


def status_of(service: str, anomalies, suspects) -> str:
    """root / affected / ok for one service."""
    if suspects and suspects[0].service == service:
        return "root"
    if any(a.service == service for a in anomalies):
        return "affected"
    return "ok"


def show_guide() -> None:
    with st.expander("Getting started: how to use this dashboard", expanded=True):
        st.markdown(
            "A pretend online shop runs 5 services. PulseOps watches their metrics, notices "
            "when something goes wrong, finds **which service started it**, and proposes a "
            "fix that **a human must approve**. The data is simulated, so the right answer "
            "is always known and you can check PulseOps against it."
        )
        st.markdown(
            ui.steps(
                [
                    "<b>Pick a scenario</b> in the left sidebar: a fault type and the service "
                    "it hits. Try <code>error_burst</code> on <code>database</code>; everything "
                    "depends on the database, so you see the domino effect.",
                    "<b>Read the summary tiles</b>: is there an incident, when it was detected, "
                    "the top suspect, and whether that matches the truth.",
                    "<b>Check service status</b>: <i>Root cause</i> is where it started, "
                    "<i>Degraded</i> services are knock-on effects, <i>Operational</i> is fine.",
                    "<b>Open the tabs</b>: <i>Metrics</i> (x = minute 0 to 120, y = value, one "
                    "line per service), <i>Root cause</i> (scores and reasons), "
                    "<i>Response</i> (report and proposed fix).",
                    "<b>Approve or reject</b> the fix in <i>Response</i>. The decision goes to "
                    "the <i>Audit log</i>. Nothing is really executed.",
                ]
            ),
            unsafe_allow_html=True,
        )


fault_kind, service, seed = sidebar()
scenario = make_scenario(fault_kind, service, seed)
anomalies = detect(scenario.metrics)
suspects = rank_suspects(anomalies, scenario.deploys)
report = build_report(anomalies, suspects)
incident_id = f"{fault_kind}-{service}-{seed}" if fault_kind else f"healthy-{seed}"

st.markdown(ui.top_bar(incident_id, bool(anomalies)), unsafe_allow_html=True)
show_guide()

# --- Summary tiles ---
first_alarm = min((a.start for a in anomalies), default=None)
top = suspects[0].service if suspects else "none"
items = [
    ui.tile(
        "alert" if anomalies else "check",
        "Status",
        "Incident" if anomalies else "Healthy",
        "anomalies found" if anomalies else "no anomalies",
        "#f87171" if anomalies else "#4ade80",
    ),
    ui.tile("activity", "Anomalous metrics", str(len(anomalies)), "of 15 watched"),
    ui.tile(
        "clock",
        "Detected at",
        f"min {first_alarm}" if first_alarm is not None else "–",
        f"{first_alarm - scenario.fault.start} min after fault start"
        if scenario.fault and first_alarm is not None
        else "",
    ),
    ui.tile("target", "Top suspect", top, f"score {suspects[0].score:.1f}" if suspects else ""),
]
if scenario.fault:
    correct = top == scenario.fault.service
    items.append(
        ui.tile(
            "check" if correct else "x",
            "Matches truth",
            "Yes" if correct else "No",
            f"real cause: {scenario.fault.service}",
            "#4ade80" if correct else "#f87171",
        )
    )
else:
    items.append(
        ui.tile(
            "x" if anomalies else "check",
            "False alarm",
            "Yes" if anomalies else "No",
            "healthy run",
            "#f87171" if anomalies else "#4ade80",
        )
    )
st.markdown(ui.tiles(items), unsafe_allow_html=True)

# --- Service status table ---
st.markdown(ui.section("server", "Service status"), unsafe_allow_html=True)
rows = [
    {
        "service": name,
        "status": status_of(name, anomalies, suspects),
        "calls": ", ".join(DEPENDS_ON[name]) or "nothing",
        "anomalies": ", ".join(a.metric for a in anomalies if a.service == name) or "none",
    }
    for name in SERVICES
]
st.markdown(ui.service_table(rows), unsafe_allow_html=True)

# --- Detail tabs ---
tab_metrics, tab_rca, tab_response, tab_audit = st.tabs(
    ["Metrics", "Root cause", "Response", "Audit log"]
)

with tab_metrics:
    st.caption(
        "x-axis: minute of the scenario (0 to 120). y-axis: the metric value. "
        "The first 30 minutes are the normal baseline the detector learns from."
    )
    if scenario.fault:
        st.caption(
            f"Fault injected at minute **{scenario.fault.start}**, "
            f"strength {scenario.fault.severity:.0%}."
        )
    chart_cols = st.columns(len(METRICS))
    for col, metric in zip(chart_cols, METRICS, strict=True):
        with col.container(border=True):
            st.markdown(f"**{METRIC_LABELS.get(metric, metric)}**")
            columns = [column(s, metric) for s in SERVICES]
            chart_data = scenario.metrics[columns].rename(columns=lambda c: c.split(".")[0])
            st.line_chart(chart_data, x_label="minute", y_label=metric, height=240)
    if scenario.deploys:
        st.markdown(ui.section("rocket", "Deploys"), unsafe_allow_html=True)
        st.dataframe(
            [{"service": d.service, "minute": d.step} for d in scenario.deploys],
            hide_index=True,
        )

with tab_rca:
    if not suspects:
        st.success("No anomalies, so there is nothing to rank. All services look normal.")
    else:
        st.caption(
            "Score = how strongly the 3 rules point at this service: (1) none of the "
            "services it calls look broken, (2) it went wrong first, (3) it was deployed "
            "just before the trouble."
        )
        best = max(s.score for s in suspects) or 1
        for rank, s in enumerate(suspects, start=1):
            with st.container(border=True):
                left, right = st.columns([1, 3])
                left.markdown(f"**#{rank} · {s.service}**")
                left.caption(f"first anomaly at minute {s.start}")
                right.progress(min(s.score / best, 1.0), text=f"score {s.score:.2f}")
                for reason in s.reasons:
                    right.markdown(f"- {reason}")

with tab_response:
    left, right = st.columns([3, 2])
    with left, st.container(border=True):
        st.markdown(ui.section("layers", "Incident report"), unsafe_allow_html=True)
        st.markdown(report.text)
    with right:
        if scenario.fault:
            # In real life we wouldn't know this. Here it lets you check the answer.
            st.info(
                f"**Ground truth:** `{scenario.fault.service}` had `{scenario.fault.kind}` "
                f"from minute {scenario.fault.start}."
            )
        if report.action:
            with st.container(border=True):
                st.markdown(ui.section("book", "Proposed action"), unsafe_allow_html=True)
                st.write(report.action)
                st.caption(f"Runbook: {report.runbook}")
                approve, reject = st.columns(2)
                if approve.button("Approve", type="primary", use_container_width=True):
                    log_decision(incident_id, suspects[0].service, report.action, "approved")
                    st.success("Approved and logged. Nothing is executed in this demo.")
                if reject.button("Reject", use_container_width=True):
                    log_decision(incident_id, suspects[0].service, report.action, "rejected")
                    st.warning("Rejected and logged.")
        else:
            st.success("Nothing to approve: no incident.")

with tab_audit:
    st.caption("Every approve / reject decision, newest first. Resets when the server restarts.")
    log = read_log()
    if log:
        st.dataframe(log[::-1], hide_index=True, use_container_width=True)
    else:
        st.write("No decisions yet. Approve or reject an action in the Response tab.")
