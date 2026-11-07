"""Streamlit SOC dashboard for the Telemedicine AI-IDS prototype.

Academic prototype only. All event data shown is synthetic unless ingested from real sources by the user.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from api_client import ApiClient

st.set_page_config(page_title="Telemedicine AI-IDS SOC Dashboard", layout="wide", page_icon=":shield:")

SEVERITY_COLORS = {"critical": "#e74c3c", "high": "#e67e22", "medium": "#f1c40f", "low": "#2ecc71"}

st.markdown(
    """
    <style>
        .block-container {padding-top: 1.5rem;}
        div[data-testid="stMetric"] {background-color: #161B22; padding: 10px; border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state():
    for key, default in [("token", None), ("username", None), ("role", None)]:
        if key not in st.session_state:
            st.session_state[key] = default


def login_view():
    st.title("Telemedicine AI-IDS \u2014 Analyst Login")
    st.caption("Academic prototype \u2014 AI-Driven Intrusion Detection Framework for Telemedicine Cybersecurity in South Africa")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        resp = ApiClient().login(username, password)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.token = data["access_token"]
            st.session_state.username = data["username"]
            st.session_state.role = data["role"]
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.info("Demo administrator account: username `admin`, password `Admin@12345` (see README for limitations).")


def logout():
    ApiClient(st.session_state.token).post("/auth/logout")
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()


def overview_page(client: ApiClient):
    st.header("Security Operations Overview")
    resp = client.get("/reports/summary")
    if resp.status_code != 200:
        st.error("Could not load summary data from the backend.")
        return
    summary = resp.json()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Security Events", summary["total_events"])
    c2.metric("Total Threats Detected", summary["total_threats_detected"])
    c3.metric("Total Alerts", summary["total_alerts"])
    c4.metric("Total Incidents", summary["total_incidents"])

    sev = summary["severity_distribution"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Critical Alerts", sev.get("critical", 0))
    c2.metric("High Alerts", sev.get("high", 0))
    c3.metric("Medium Alerts", sev.get("medium", 0))
    c4.metric("Low Alerts", sev.get("low", 0))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Severity Distribution")
        sev_df = pd.DataFrame({"severity": list(sev.keys()), "count": list(sev.values())})
        fig = px.pie(sev_df, names="severity", values="count", color="severity",
                     color_discrete_map=SEVERITY_COLORS, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Incident Status Breakdown")
        inc = summary["incident_status_breakdown"]
        inc_df = pd.DataFrame({"status": list(inc.keys()), "count": list(inc.values())})
        fig2 = px.bar(inc_df, x="status", y="count", color="status")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Detection Model Status")
    model_info = summary["model_info"]
    mc1, mc2 = st.columns(2)
    mc1.metric("Random Forest Trained", "Yes" if model_info["random_forest_trained"] else "No")
    mc2.metric("Isolation Forest Trained", "Yes" if model_info["isolation_forest_trained"] else "No")

    if summary.get("evaluation_metrics"):
        with st.expander("Latest Model Evaluation Metrics"):
            st.json(summary["evaluation_metrics"])

    st.subheader("Threat Detection Trend")
    results_resp = client.get("/detection/results", params={"limit": 200})
    if results_resp.status_code == 200 and results_resp.json():
        df = pd.DataFrame(results_resp.json())
        df["created_at"] = pd.to_datetime(df["created_at"])
        trend = df.groupby([df["created_at"].dt.date, "severity"]).size().reset_index(name="count")
        trend.columns = ["date", "severity", "count"]
        fig3 = px.line(trend, x="date", y="count", color="severity", color_discrete_map=SEVERITY_COLORS, markers=True)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No detection results yet. Run threat detection from the 'Threat Detection' page.")


def events_page(client: ApiClient):
    st.header("Security Events & Telemetry Ingestion")
    st.caption("Synthetic telemedicine security event data \u2014 SYNTHETIC DATA ONLY, no real patient information.")

    uploaded = st.file_uploader("Upload CSV of security events", type=["csv"])
    if uploaded and st.button("Ingest CSV"):
        resp = client.post("/events/upload", files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")})
        if resp.status_code == 200:
            result = resp.json()
            st.success(f"Ingested {result['valid_rows']} / {result['total_rows']} rows ({result['invalid_rows']} invalid).")
            if result["errors"]:
                with st.expander(f"View {len(result['errors'])} validation errors"):
                    for err in result["errors"]:
                        st.text(err)
        else:
            st.error(f"Ingestion failed: {resp.text}")

    st.subheader("Recent Security Events")
    events_resp = client.get("/events", params={"limit": 200})
    if events_resp.status_code == 200:
        events = events_resp.json()
        if events:
            st.dataframe(pd.DataFrame(events), use_container_width=True, height=400)
        else:
            st.info("No security events stored yet. Upload a CSV above to get started.")


def detection_page(client: ApiClient):
    st.header("AI-Based Threat Detection")
    st.caption("Random Forest (known attack patterns) + Isolation Forest (anomalous/unknown behaviour) + hybrid risk scoring.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Train / Retrain Detection Models", type="primary"):
            with st.spinner("Training Random Forest + Isolation Forest on the labelled synthetic dataset..."):
                resp = client.post("/detection/train")
            if resp.status_code == 200:
                st.success("Models trained and evaluated successfully.")
                st.json(resp.json())
            else:
                st.error(f"Training failed: {resp.text}")
    with col2:
        if st.button("Run Detection on New Events"):
            resp = client.post("/detection/run")
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Processed {data['events_processed']} events, generated {data['alerts_generated']} alerts.")
                st.json(data["severity_breakdown"])
            else:
                st.error(f"Detection run failed: {resp.text}")

    eval_resp = client.get("/detection/evaluation")
    if eval_resp.status_code == 200:
        metrics = eval_resp.json()
        st.subheader("Random Forest Evaluation (held-out test split)")
        rf = metrics["random_forest"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Accuracy", rf["accuracy"])
        m2.metric("Precision", rf["precision"])
        m3.metric("Recall", rf["recall"])
        m4.metric("F1-score", rf["f1_score"])
        st.caption(
            f"False positive rate: {rf['false_positive_rate']} | "
            f"Avg prediction latency: {rf['avg_prediction_latency_ms']} ms/event | "
            f"Train/test size: {rf['train_size']}/{rf['test_size']}"
        )
        cm = rf["confusion_matrix"]
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm, x=["Pred Normal", "Pred Attack"], y=["Actual Normal", "Actual Attack"],
            colorscale="Blues", showscale=True, text=cm, texttemplate="%{text}",
        ))
        st.plotly_chart(fig_cm, use_container_width=True)

        st.subheader("Isolation Forest Evaluation")
        st.json(metrics["isolation_forest"])
        st.caption(
            "Isolation Forest flags deviations from learned normal behaviour; it does not guarantee "
            "detection of every unknown attack type."
        )
    else:
        st.info("No evaluation metrics yet. Click 'Train / Retrain Detection Models' above.")

    st.subheader("Recent Detection Results")
    results_resp = client.get("/detection/results", params={"limit": 100})
    if results_resp.status_code == 200 and results_resp.json():
        st.dataframe(pd.DataFrame(results_resp.json()), use_container_width=True, height=350)


def alerts_page(client: ApiClient):
    st.header("Alert Management")
    col1, col2, col3 = st.columns(3)
    severity_filter = col1.selectbox("Filter by severity", ["All", "critical", "high", "medium", "low"])
    status_filter = col2.selectbox("Filter by status", ["All", "open", "acknowledged", "escalated", "closed"])
    search = col3.text_input("Search by source IP or user ID")

    params = {}
    if severity_filter != "All":
        params["severity"] = severity_filter
    if status_filter != "All":
        params["status"] = status_filter
    if search:
        params["search"] = search

    resp = client.get("/alerts", params=params)
    if resp.status_code != 200:
        st.error("Could not load alerts.")
        return
    alerts = resp.json()
    if not alerts:
        st.info("No alerts match the current filters.")
        return

    for alert in alerts:
        with st.expander(f"[{alert['severity'].upper()}] {alert['title']} \u2014 risk {alert['risk_score']}"):
            st.write(alert["description"])
            st.caption(f"Status: {alert['status']} | Created: {alert['created_at']}")
            bc1, bc2 = st.columns(2)
            if alert["status"] == "open" and bc1.button("Acknowledge", key=f"ack_{alert['id']}"):
                r = client.post(f"/alerts/{alert['id']}/acknowledge")
                if r.status_code == 200:
                    st.success("Acknowledged.")
                    st.rerun()
            if alert["status"] != "escalated" and bc2.button("Escalate to Incident", key=f"esc_{alert['id']}"):
                r = client.post(f"/alerts/{alert['id']}/escalate")
                if r.status_code == 200:
                    st.success(f"Escalated to incident #{r.json()['id']}.")
                    st.rerun()
                else:
                    st.error(r.text)


def incidents_page(client: ApiClient):
    st.header("Incident Management")
    status_filter = st.selectbox("Filter by status", ["All", "open", "investigating", "escalated", "resolved", "closed"])
    params = {} if status_filter == "All" else {"status_filter": status_filter}
    resp = client.get("/incidents", params=params)
    if resp.status_code != 200:
        st.error("Could not load incidents.")
        return
    incidents = resp.json()
    if not incidents:
        st.info("No incidents recorded yet. Escalate an alert from the Alerts page to create one.")
        return

    status_options = ["open", "investigating", "escalated", "resolved", "closed"]
    for incident in incidents:
        with st.expander(f"#{incident['id']} {incident['title']} \u2014 [{incident['status']}]"):
            st.write(incident["description"] or "No description.")
            st.caption(f"Created: {incident['created_at']} | Updated: {incident['updated_at']}")

            new_status = st.selectbox(
                "Update status", status_options, index=status_options.index(incident["status"]),
                key=f"status_{incident['id']}",
            )
            resolution_notes = st.text_input("Resolution notes (if resolving)", key=f"res_{incident['id']}")
            if st.button("Update Status", key=f"upd_{incident['id']}"):
                r = client.put(
                    f"/incidents/{incident['id']}/status",
                    json={"status": new_status, "resolution_notes": resolution_notes or None},
                )
                if r.status_code == 200:
                    st.success("Status updated.")
                    st.rerun()
                else:
                    st.error(r.text)

            note_text = st.text_area("Add investigation note", key=f"note_{incident['id']}")
            if st.button("Add Note", key=f"addnote_{incident['id']}"):
                r = client.post(f"/incidents/{incident['id']}/notes", json={"note": note_text})
                if r.status_code == 200:
                    st.success("Note added.")
                    st.rerun()

            st.markdown("**Investigation history:**")
            for note in incident.get("notes", []):
                st.text(f"[{note['created_at']}] {note['note']}")


def reports_page(client: ApiClient):
    st.header("Reports & Audit History")
    resp = client.get("/reports/summary")
    if resp.status_code == 200:
        st.json(resp.json())

    col1, col2 = st.columns(2)
    with col1:
        csv_resp = client.get("/reports/export/csv")
        if csv_resp.status_code == 200:
            st.download_button("Download Alerts CSV", csv_resp.content, file_name="alerts_report.csv", mime="text/csv")
    with col2:
        pdf_resp = client.get("/reports/export/pdf")
        if pdf_resp.status_code == 200:
            st.download_button("Download Summary PDF", pdf_resp.content, file_name="security_report.pdf", mime="application/pdf")

    if st.session_state.role == "administrator":
        st.subheader("Audit Log")
        audit_resp = client.get("/reports/audit", params={"limit": 300})
        if audit_resp.status_code == 200 and audit_resp.json():
            st.dataframe(pd.DataFrame(audit_resp.json()), use_container_width=True, height=400)


def administration_page(client: ApiClient):
    st.header("Administration")
    if st.session_state.role != "administrator":
        st.warning("Administrator role required to manage users.")
        return

    st.subheader("Create New User")
    with st.form("create_user_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["security_analyst", "administrator"])
        submitted = st.form_submit_button("Create User")
    if submitted:
        resp = client.post("/auth/users", json={"username": username, "email": email, "password": password, "role": role})
        if resp.status_code == 201:
            st.success(f"User '{username}' created.")
        else:
            st.error(resp.text)

    st.subheader("Existing Users")
    users_resp = client.get("/auth/users")
    if users_resp.status_code == 200:
        st.dataframe(pd.DataFrame(users_resp.json()), use_container_width=True)


def main():
    init_state()
    if not st.session_state.token:
        login_view()
        return

    client = ApiClient(st.session_state.token)

    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username} ({st.session_state.role})")
        page = st.radio("Navigation", [
            "Overview", "Security Events", "Threat Detection", "Alerts", "Incidents", "Reports", "Administration",
        ])
        if st.button("Log out"):
            logout()

    pages = {
        "Overview": overview_page, "Security Events": events_page, "Threat Detection": detection_page,
        "Alerts": alerts_page, "Incidents": incidents_page, "Reports": reports_page,
        "Administration": administration_page,
    }
    pages[page](client)


if __name__ == "__main__":
    main()
