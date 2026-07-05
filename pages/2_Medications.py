"""Medications page — add/delete medications."""

import streamlit as st

import db

st.set_page_config(page_title="Medications", page_icon="💊", layout="wide")
db.init_db()

st.title("💊 Medications")
st.caption("Manage your medication list, dosages, and schedules.")

with st.expander("➕ Add a new medication", expanded=len(db.get_medications()) == 0):
    with st.form("add_medication_form", clear_on_submit=True):
        name = st.text_input("Medication name", placeholder="e.g. Metformin")
        dosage = st.text_input("Dosage", placeholder="e.g. 500mg")
        frequency = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
        times = st.text_input(
            "Scheduled time(s) — comma separated, 24hr format",
            placeholder="e.g. 08:00, 20:00",
        )
        notes = st.text_area("Notes (optional)", placeholder="e.g. Take with food")
        submitted = st.form_submit_button("Add Medication", use_container_width=True)

        if submitted:
            if not name or not dosage or not times:
                st.error("Please fill in medication name, dosage, and at least one scheduled time.")
            else:
                db.add_medication(name.strip(), dosage.strip(), frequency, times.strip(), notes.strip())
                st.success(f"Added {name} to your medication list.")
                st.rerun()

st.divider()
st.subheader("Your Medications")

meds = db.get_medications()
if not meds:
    st.info("No medications added yet. Use the form above to add your first one.")
else:
    for med in meds:
        col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
        with col1:
            st.write(f"**{med['name']}**")
            if med["notes"]:
                st.caption(med["notes"])
        with col2:
            st.write(med["dosage"])
        with col3:
            st.write(f"{med['frequency']} — {med['times']}")
        with col4:
            if st.button("🗑️ Delete", key=f"del_{med['id']}", use_container_width=True):
                db.delete_medication(med["id"])
                st.rerun()
        st.divider()
