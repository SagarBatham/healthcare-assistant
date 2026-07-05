"""Schedule page — mark doses Taken/Missed for today."""

import streamlit as st
from datetime import date, timedelta

import db

st.set_page_config(page_title="Schedule", page_icon="📅", layout="wide")
db.init_db()

st.title("📅 Medication Schedule")
st.caption("Review and mark your medication doses.")

selected_date = st.date_input("Date", value=date.today())
schedule = db.get_today_schedule(selected_date.isoformat())

if not schedule:
    st.info("No medications scheduled for this date. Add a medication on the Medications page first.")
else:
    for item in schedule:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        with col1:
            st.write(f"**{item['name']}**")
            st.caption(item["dosage"])
        with col2:
            st.write(f"⏰ {item['scheduled_time']}")
        with col3:
            status_color = {"Taken": "✅ Taken", "Missed": "⚠️ Missed", "Pending": "⏳ Pending"}
            st.write(status_color.get(item["status"], item["status"]))
        with col4:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Mark Taken", key=f"taken_{item['id']}", use_container_width=True):
                    db.update_log_status(item["id"], "Taken")
                    st.rerun()
            with btn_col2:
                if st.button("Mark Missed", key=f"missed_{item['id']}", use_container_width=True):
                    db.update_log_status(item["id"], "Missed")
                    st.rerun()
        st.divider()

st.subheader("📈 Adherence Summary")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Today", f"{sum(1 for s in schedule if s['status'] == 'Taken')}/{len(schedule)}" if schedule else "0/0")
with c2:
    st.metric("7-Day Adherence", f"{db.get_adherence_rate(7)}%")
with c3:
    st.metric("30-Day Adherence", f"{db.get_adherence_rate(30)}%")
