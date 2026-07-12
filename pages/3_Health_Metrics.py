"""Health Metrics page — log readings, CSV import, trend charts."""

import streamlit as st
import pandas as pd

import db

st.set_page_config(page_title="Health Metrics", page_icon="📊", layout="wide")
db.init_db()

st.title("📊 Health Metrics")
st.caption("Log readings, import from CSV, and view trends over time.")

tab_log, tab_import, tab_trends = st.tabs(["Log a Reading", "Import CSV", "Trends"])

with tab_log:
    with st.form("log_metric_form", clear_on_submit=True):
        metric_type = st.selectbox("Metric", list(db.METRIC_UNITS.keys()))
        value = st.number_input("Value", min_value=0.0, step=0.1, format="%.1f")
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Log Reading", use_container_width=True)
        if submitted:
            db.add_health_metric(metric_type, value, notes=notes)
            st.success(f"Logged {metric_type}: {value} {db.METRIC_UNITS.get(metric_type, '')}")
            st.rerun()

with tab_import:
    st.write("Upload a CSV with columns: `metric_type`, `value`, and optionally `unit`, `recorded_at`, `notes`.")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is not None:
        try:
            count = db.import_metrics_csv(uploaded)
            st.success(f"Imported {count} readings.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    st.divider()
    st.caption("Example CSV format:")
    example_df = pd.DataFrame(
        {
            "metric_type": ["Weight", "Blood Glucose"],
            "value": [70.5, 95],
            "unit": ["kg", "mg/dL"],
            "recorded_at": ["2026-06-20T08:00:00", "2026-06-20T08:05:00"],
            "notes": ["Morning weigh-in", "Fasting"],
        }
    )
    st.dataframe(example_df, use_container_width=True)

with tab_trends:
    metric_filter = st.selectbox("Select metric to view", ["All"] + list(db.METRIC_UNITS.keys()), key="trend_metric")
    #This is Metric Filter
    df = db.get_metrics_df(None if metric_filter == "All" else metric_filter)

    if df.empty:
        st.info("No readings logged yet. Add one in the 'Log a Reading' tab.")
    else:
        if metric_filter == "All":
            for mtype in df["metric_type"].unique():
                sub = df[df["metric_type"] == mtype]
                st.subheader(mtype)
                st.line_chart(sub.set_index("recorded_at")["value"])
        else:
            st.subheader(metric_filter)
            st.line_chart(df.set_index("recorded_at")["value"])

        st.divider()
        st.subheader("Recent Readings")
        display_df = df.sort_values("recorded_at", ascending=False).head(20)[
            ["metric_type", "value", "unit", "recorded_at", "notes"]
        ]
        st.dataframe(display_df, use_container_width=True)
