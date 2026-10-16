"""PulseOps Streamlit dashboard.

Pick a fault, watch PulseOps find it, then approve or reject the proposed fix.
Run with:  uv run streamlit run src/pulseops/app.py
"""

import streamlit as st

from pulseops.audit import log_decision, read_log
from pulseops.detector import detect
from pulseops.rca import rank_suspects
from pulseops.report import build_report
from pulseops.services import DEPENDS_ON, METRICS, SERVICES, column
from pulseops.simulator import FAULTS, make_scenario

HEALTHY = "none (healthy)"
METRIC_LABELS = {
    "latency_ms": "Latency (ms)",
    "error_rate": "Error rate (share failed)",
    "cpu": "CPU (%)",
}
FAULT_HELP = {
    "slow_queries": "requests get slower (latency up)",
    "error_burst": "many requests fail (error rate up)",
    "cpu_saturation": "the machine is overloaded (CPU up); stays local",
    "bad_deploy": "a new release breaks it; a deploy event appears just before",
}

st.set_page_config(page_title="PulseOps", page_icon="🩺", layout="wide")


def show_guide() -> None:
    """The 'how to use' box. Open on first visit so new readers aren't lost."""
    with st.expander("📘 How to use this dashboard (start here)", expanded=True):
        st.markdown(
            """
**What this is.** A pretend online shop with 5 services. PulseOps watches their
metrics, notices when something goes wrong, guesses **which service started it**,
and proposes a fix that **a human must approve**. All data is simulated, so we
always know the right answer and you can check PulseOps against it.

**Try it in 4 steps**
1. **Sidebar → Fault**: choose what goes wrong (or keep *healthy* to see a calm system).
2. **Sidebar → Broken service**: choose where it happens. Tip: `database` shows the
   domino effect best, because everything depends on it.
3. **Read the dashboard top to bottom**:
   - *KPI cards*: is there an incident, when it was detected, the top suspect,
     and whether PulseOps got it right.
   - *Service health*: 🔴 root suspect, 🟠 affected (knock-on), 🟢 normal.
   - *Metrics tab*: x-axis = minute (0–120), y-axis = metric value, one line per service.
   - *Root cause tab*: every suspect with a score and the plain-English reasons.
4. **Incident tab → Approve or Reject** the proposed action. It is written to the
   audit log. Nothing is really executed; this is a demo.

**Seed** changes the random noise and fault strength. Same seed = same result.
Mild faults (low strength) can be missed; that is a known, measured limitation.
            """
        )


def sidebar() -> tuple[str | None, str, int]:
    with st.sidebar:
        st.title("🩺 PulseOps")
        st.caption("Incident triage demo · work in progress")
        st.header("1 · Inject a fault")
        kind = st.selectbox("Fault", [HEALTHY, *FAULTS])
        if kind != HEALTHY:
            st.caption(f"ℹ️ {FAULT_HELP[kind]}")
        service = st.selectbox("Broken service", SERVICES, index=4, disabled=kind == HEALTHY)
        seed = st.number_input("Seed (randomness)", min_value=0, value=7, step=1)
        st.divider()
        st.markdown("**Service map** (arrow = *calls*)")
        st.markdown(
            "- **gateway** → orders, inventory\n"
            "- **orders** → payments, database\n"
            "- **payments** → database\n"
            "- **inventory** → database"
        )
        st.markdown(
            "[GitHub repo](https://github.com/ubaidur404786/pulseops) · "
            "[Data notebook](https://github.com/ubaidur404786/pulseops/blob/main/notebooks/01_data.ipynb)"
        )
    fault_kind = None if kind == HEALTHY else kind
    return fault_kind, service, int(seed)


def service_status(service: str, anomalies, suspects) -> str:
    """Traffic-light status for one service."""
    if suspects and suspects[0].service == service:
        return "root"
    if any(a.service == service for a in anomalies):
        return "affected"
    return "ok"


fault_kind, service, seed = sidebar()
scenario = make_scenario(fault_kind, service, seed)
anomalies = detect(scenario.metrics)
suspects = rank_suspects(anomalies, scenario.deploys)
report = build_report(anomalies, suspects)
incident_id = f"{fault_kind}-{service}-{seed}"

st.title("Incident triage dashboard")
st.caption("Simulated services · z-score detection · rule-based root cause · human approval")
show_guide()

# --- KPI row: the answer in five numbers ---
first_alarm = min((a.start for a in anomalies), default=None)
top = suspects[0].service if suspects else "—"
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Status", "🚨 Incident" if anomalies else "✅ Healthy", border=True)
k2.metric("Anomalous metrics", len(anomalies), border=True)
k3.metric(
    "Detected at",
    f"min {first_alarm}" if first_alarm is not None else "—",
    delta=(
        f"{first_alarm - scenario.fault.start} min after start"
        if scenario.fault and first_alarm is not None
        else None
    ),
    delta_color="off",
    border=True,
)
k4.metric("Top suspect", top, border=True)
if scenario.fault:
    correct = top == scenario.fault.service
    k5.metric(
        "Correct?",
        "✅ Yes" if correct else "❌ No",
        f"truth: {scenario.fault.service}",
        delta_color="off",
        border=True,
    )
else:
    k5.metric("False alarm?", "❌ Yes" if anomalies else "✅ No", border=True)

# --- Service health grid ---
st.subheader("Service health")
badges = {
    "root": ("🔴 Root suspect", "red"),
    "affected": ("🟠 Affected", "orange"),
    "ok": ("🟢 Normal", "green"),
}
for col, name in zip(st.columns(len(SERVICES)), SERVICES, strict=True):
    status = service_status(name, anomalies, suspects)
    label, color = badges[status]
    with col.container(border=True):
        st.markdown(f"**{name}**")
        st.badge(label, color=color)
        broken = [a.metric for a in anomalies if a.service == name]
        calls = ", ".join(DEPENDS_ON[name]) or "nothing"
        st.caption(f"calls: {calls}")
        st.caption("anomalies: " + (", ".join(broken) if broken else "none"))

# --- Detail tabs ---
tab_metrics, tab_rca, tab_incident, tab_audit = st.tabs(
    ["📈 Metrics", "🔎 Root cause", "🛠️ Incident & approval", "📜 Audit log"]
)

with tab_metrics:
    st.caption(
        "x-axis: minute of the scenario (0–120). y-axis: the metric value. "
        "The first 30 minutes are the 'normal' baseline the detector learns from."
    )
    if scenario.fault:
        st.caption(
            f"⚡ Fault injected at **minute {scenario.fault.start}** "
            f"(strength {scenario.fault.severity:.0%})."
        )
    for metric in METRICS:
        with st.container(border=True):
            st.markdown(f"**{METRIC_LABELS.get(metric, metric)}**")
            columns = [column(s, metric) for s in SERVICES]
            chart_data = scenario.metrics[columns].rename(columns=lambda c: c.split(".")[0])
            st.line_chart(chart_data, x_label="minute", y_label=metric, height=220)
    if scenario.deploys:
        st.caption(
            "🚀 Deploys: " + ", ".join(f"{d.service} at minute {d.step}" for d in scenario.deploys)
        )

with tab_rca:
    if not suspects:
        st.success("No anomalies, so there is nothing to rank. All services look normal.")
    else:
        st.caption("Score = how many of the 3 rules point at this service. Higher = more likely.")
        best = max(s.score for s in suspects) or 1
        for rank, s in enumerate(suspects, start=1):
            with st.container(border=True):
                left, right = st.columns([1, 3])
                left.markdown(f"### #{rank} {s.service}")
                left.caption(f"first wrong at minute {s.start}")
                right.progress(min(s.score / best, 1.0), text=f"score {s.score:.2f}")
                for reason in s.reasons:
                    right.markdown(f"- {reason}")
        st.info(
            "The 3 rules: **(1)** none of the services it calls look broken, "
            "**(2)** it went wrong first, **(3)** it was deployed just before the trouble."
        )

with tab_incident:
    left, right = st.columns([3, 2])
    with left, st.container(border=True):
        st.markdown("#### Incident report")
        st.markdown(report.text)
    with right:
        if scenario.fault:
            # In real life we wouldn't know this. Here it lets you check the answer.
            st.info(
                f"**Truth:** `{scenario.fault.service}` had `{scenario.fault.kind}` "
                f"starting at minute {scenario.fault.start}."
            )
        if report.action:
            with st.container(border=True):
                st.markdown("#### Proposed action")
                st.write(report.action)
                st.caption(f"From runbook: {report.runbook}")
                approve, reject = st.columns(2)
                if approve.button("✅ Approve", type="primary", use_container_width=True):
                    log_decision(incident_id, suspects[0].service, report.action, "approved")
                    st.success("Approved and logged. Nothing is executed in this demo.")
                if reject.button("✖ Reject", use_container_width=True):
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
        st.write("No decisions yet. Approve or reject an action in the Incident tab.")
