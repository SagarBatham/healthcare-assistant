"""
Healthcare Monitoring AI Agent — Dashboard (main entry point).

Shows a health snapshot, today's schedule preview, missed-dose alerts,
and quick actions. Run with:
    streamlit run app.py --server.port $PORT --server.address 0.0.0.0
"""

import streamlit as st
from datetime import date

import db

st.set_page_config(
    page_title="Healthcare Monitoring AI Agent",
    page_icon="💊",
    layout="wide",
)

db.init_db()
db.mark_overdue_as_missed()

st.title("💊 Healthcare Monitoring AI Agent")
st.caption("Your personal health assistant — medication tracking, health metrics, and wellness guidance.")

# --- Health snapshot -------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

adherence = db.get_adherence_rate(7)
today_schedule = db.get_today_schedule()
alerts = db.get_due_alerts()
active_meds = db.get_medications()

with col1:
    st.metric("7-Day Adherence", f"{adherence}%")
with col2:
    st.metric("Active Medications", len(active_meds))
with col3:
    taken_today = sum(1 for s in today_schedule if s["status"] == "Taken")
    st.metric("Doses Taken Today", f"{taken_today}/{len(today_schedule)}")
with col4:
    st.metric("Pending / Missed", len(alerts))

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("📅 Today's Schedule")
    if not today_schedule:
        st.info("No medications scheduled. Add one on the Medications page.")
    else:
        for item in today_schedule:
            status_icon = {"Taken": "✅", "Missed": "⚠️", "Pending": "⏳"}.get(item["status"], "⏳")
            st.write(f"{status_icon} **{item['scheduled_time']}** — {item['name']} ({item['dosage']}) — *{item['status']}*")

with right:
    st.subheader("🚨 Alerts")
    if not alerts:
        st.success("No missed or pending doses right now.")
    else:
        for alert in alerts:
            if alert["status"] == "Missed":
                st.error(f"Missed: {alert['name']} at {alert['scheduled_time']}")
            else:
                st.warning(f"Due: {alert['name']} at {alert['scheduled_time']}")

st.divider()

st.subheader("⚡ Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    st.page_link("pages/1_Schedule.py", label="Mark a Dose", icon="✅")
with qa2:
    st.page_link("pages/2_Medications.py", label="Add Medication", icon="➕")
with qa3:
    st.page_link("pages/3_Health_Metrics.py", label="Log a Reading", icon="📊")
with qa4:
    st.page_link("pages/4_Chatbot.py", label="Ask the Assistant", icon="💬")

st.divider()
st.caption(f"Today is {date.today().strftime('%A, %B %d, %Y')}. Use the sidebar to navigate between pages.")
