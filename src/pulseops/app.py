"""PulseOps Streamlit app.

Pick a fault, watch PulseOps find it, then approve or reject the proposed fix.
Run with:  uv run streamlit run src/pulseops/app.py
"""

import streamlit as st

from pulseops.audit import log_decision, read_log
from pulseops.detector import detect
from pulseops.rca import rank_suspects
from pulseops.report import build_report
from pulseops.services import METRICS, SERVICES, column
from pulseops.simulator import FAULTS, make_scenario

st.set_page_config(page_title="PulseOps", layout="wide")
st.title("PulseOps — incident triage")
st.caption("Simulated services · z-score detection · rule-based root cause · human approval")

# --- Sidebar: choose what breaks ---
with st.sidebar:
    st.header("Inject a fault")
    kind = st.selectbox("Fault", ["none (healthy)", *FAULTS])
    service = st.selectbox("Broken service", SERVICES, disabled=kind == "none (healthy)")
    seed = st.number_input("Seed", min_value=0, value=7, step=1)

fault_kind = None if kind == "none (healthy)" else kind
scenario = make_scenario(fault_kind, service, int(seed))
anomalies = detect(scenario.metrics)
suspects = rank_suspects(anomalies, scenario.deploys)
report = build_report(anomalies, suspects)
incident_id = f"{fault_kind}-{service}-{seed}"

# --- Metrics charts ---
st.subheader("Metrics")
tabs = st.tabs(METRICS)
for tab, metric in zip(tabs, METRICS, strict=True):
    with tab:
        columns = [column(s, metric) for s in SERVICES]
        chart_data = scenario.metrics[columns].rename(columns=lambda c: c.split(".")[0])
        st.line_chart(chart_data, x_label="minute", y_label=metric)

if scenario.deploys:
    st.caption("Deploys: " + ", ".join(f"{d.service} @ min {d.step}" for d in scenario.deploys))

# --- Findings ---
left, right = st.columns(2)
with left:
    st.subheader("Report")
    st.markdown(report.text)
with right:
    st.subheader("Suspects")
    if suspects:
        st.dataframe(
            [{"service": s.service, "score": s.score, "first wrong at": s.start} for s in suspects],
            hide_index=True,
        )
    if scenario.fault:
        # In real life we wouldn't know this. Here it lets you check the answer.
        st.info(
            f"Truth: **{scenario.fault.service}** had `{scenario.fault.kind}` "
            f"starting at minute {scenario.fault.start}."
        )

# --- Human approval ---
if report.action:
    st.subheader("Proposed action")
    st.write(report.action)
    approve, reject = st.columns(2)
    if approve.button("Approve", type="primary"):
        log_decision(incident_id, suspects[0].service, report.action, "approved")
        st.success("Approved and logged. (Nothing is actually executed in this demo.)")
    if reject.button("Reject"):
        log_decision(incident_id, suspects[0].service, report.action, "rejected")
        st.warning("Rejected and logged.")

with st.expander("Audit log"):
    log = read_log()
    if log:
        st.dataframe(log[::-1], hide_index=True)
    else:
        st.write("No decisions yet.")
