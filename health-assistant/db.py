"""
SQLite data layer for the Healthcare Monitoring AI Agent.

Tables:
- medications: registered medications with dosage/schedule info
- medication_logs: daily taken/missed records per medication
- health_metrics: logged health readings (weight, BP, glucose, heart rate, etc.)
"""

import sqlite3
import os
from datetime import datetime, date, timedelta
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "health.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            times TEXT NOT NULL,
            notes TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS medication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER NOT NULL,
            scheduled_date TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            logged_at TEXT,
            FOREIGN KEY (medication_id) REFERENCES medications (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            recorded_at TEXT NOT NULL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Medications CRUD
# ---------------------------------------------------------------------------

def add_medication(name, dosage, frequency, times, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO medications (name, dosage, frequency, times, notes, active, created_at)
           VALUES (?, ?, ?, ?, ?, 1, ?)""",
        (name, dosage, frequency, times, notes, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    ensure_today_logs()


def get_medications(active_only=True):
    conn = get_connection()
    cur = conn.cursor()
    if active_only:
        cur.execute("SELECT * FROM medications WHERE active = 1 ORDER BY name")
    else:
        cur.execute("SELECT * FROM medications ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_medication_by_id(med_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medications WHERE id = ?", (med_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_medication(med_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE medications SET active = 0 WHERE id = ?", (med_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Medication logs / schedule
# ---------------------------------------------------------------------------

def ensure_today_logs(target_date=None):
    """Make sure today's schedule rows exist for every active medication."""
    target_date = target_date or date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    meds = cur.execute("SELECT * FROM medications WHERE active = 1").fetchall()
    for med in meds:
        times = [t.strip() for t in med["times"].split(",") if t.strip()]
        for t in times:
            existing = cur.execute(
                """SELECT id FROM medication_logs
                   WHERE medication_id = ? AND scheduled_date = ? AND scheduled_time = ?""",
                (med["id"], target_date, t),
            ).fetchone()
            if not existing:
                cur.execute(
                    """INSERT INTO medication_logs (medication_id, scheduled_date, scheduled_time, status)
                       VALUES (?, ?, ?, 'Pending')""",
                    (med["id"], target_date, t),
                )
    conn.commit()
    conn.close()


def get_today_schedule(target_date=None):
    target_date = target_date or date.today().isoformat()
    ensure_today_logs(target_date)
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT ml.id, ml.medication_id, ml.scheduled_date, ml.scheduled_time,
                  ml.status, ml.logged_at, m.name, m.dosage
           FROM medication_logs ml
           JOIN medications m ON m.id = ml.medication_id
           WHERE ml.scheduled_date = ?
           ORDER BY ml.scheduled_time""",
        (target_date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_log_status(log_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE medication_logs SET status = ?, logged_at = ? WHERE id = ?",
        (status, datetime.now().isoformat(), log_id),
    )
    conn.commit()
    conn.close()


def log_medication_taken_by_name(med_name, when=None):
    """Used by the chatbot for natural-language logging like 'I took metformin'."""
    when = when or date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    med = cur.execute(
        "SELECT * FROM medications WHERE active = 1 AND LOWER(name) LIKE ?",
        (f"%{med_name.lower()}%",),
    ).fetchone()
    if not med:
        conn.close()
        return None

    ensure_today_logs(when)
    log = cur.execute(
        """SELECT * FROM medication_logs
           WHERE medication_id = ? AND scheduled_date = ? AND status = 'Pending'
           ORDER BY scheduled_time LIMIT 1""",
        (med["id"], when),
    ).fetchone()

    if log:
        cur.execute(
            "UPDATE medication_logs SET status = 'Taken', logged_at = ? WHERE id = ?",
            (datetime.now().isoformat(), log["id"]),
        )
        conn.commit()
        conn.close()
        return dict(med)

    conn.close()
    return dict(med)


def get_due_alerts(target_date=None):
    """Doses that are Pending or Missed for today - used for dashboard alerts."""
    target_date = target_date or date.today().isoformat()
    ensure_today_logs(target_date)
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT ml.id, ml.scheduled_time, ml.status, m.name, m.dosage
           FROM medication_logs ml
           JOIN medications m ON m.id = ml.medication_id
           WHERE ml.scheduled_date = ? AND ml.status IN ('Pending', 'Missed')
           ORDER BY ml.scheduled_time""",
        (target_date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_adherence_rate(days=7):
    """Percentage of doses marked Taken over the last N days."""
    conn = get_connection()
    cur = conn.cursor()
    start_date = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = cur.execute(
        "SELECT status FROM medication_logs WHERE scheduled_date >= ?",
        (start_date,),
    ).fetchall()
    conn.close()
    total = len(rows)
    if total == 0:
        return 100.0
    taken = sum(1 for r in rows if r["status"] == "Taken")
    return round((taken / total) * 100, 1)


# ---------------------------------------------------------------------------
# Health metrics
# ---------------------------------------------------------------------------

METRIC_UNITS = {
    "Weight": "kg",
    "Blood Pressure (Systolic)": "mmHg",
    "Blood Pressure (Diastolic)": "mmHg",
    "Blood Glucose": "mg/dL",
    "Heart Rate": "bpm",
    "Temperature": "°C",
    "Oxygen Saturation": "%",
}


def add_health_metric(metric_type, value, unit=None, notes="", recorded_at=None):
    unit = unit or METRIC_UNITS.get(metric_type, "")
    recorded_at = recorded_at or datetime.now().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO health_metrics (metric_type, value, unit, recorded_at, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (metric_type, value, unit, recorded_at, notes),
    )
    conn.commit()
    conn.close()


def get_metrics_df(metric_type=None):
    conn = get_connection()
    if metric_type:
        df = pd.read_sql_query(
            "SELECT * FROM health_metrics WHERE metric_type = ? ORDER BY recorded_at",
            conn,
            params=(metric_type,),
        )
    else:
        df = pd.read_sql_query("SELECT * FROM health_metrics ORDER BY recorded_at", conn)
    conn.close()
    if not df.empty:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    return df


def get_latest_metric(metric_type):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT * FROM health_metrics WHERE metric_type = ? ORDER BY recorded_at DESC LIMIT 1",
        (metric_type,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def import_metrics_csv(file):
    """
    Import a CSV with columns: metric_type, value, unit (optional), recorded_at (optional), notes (optional).
    Returns number of rows imported.
    """
    df = pd.read_csv(file)
    required = {"metric_type", "value"}
    if not required.issubset(set(df.columns)):
        raise ValueError("CSV must contain at least 'metric_type' and 'value' columns")

    conn = get_connection()
    cur = conn.cursor()
    count = 0
    for _, row in df.iterrows():
        metric_type = str(row["metric_type"]).strip()
        value = float(row["value"])
        unit = str(row["unit"]).strip() if "unit" in df.columns and pd.notna(row.get("unit")) else METRIC_UNITS.get(metric_type, "")
        recorded_at = str(row["recorded_at"]) if "recorded_at" in df.columns and pd.notna(row.get("recorded_at")) else datetime.now().isoformat()
        notes = str(row["notes"]) if "notes" in df.columns and pd.notna(row.get("notes")) else ""
        cur.execute(
            """INSERT INTO health_metrics (metric_type, value, unit, recorded_at, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (metric_type, value, unit, recorded_at, notes),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def mark_overdue_as_missed(target_date=None):
    """Mark any Pending dose from a past date as Missed (called on app load)."""
    target_date = target_date or date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE medication_logs SET status = 'Missed' WHERE status = 'Pending' AND scheduled_date < ?",
        (target_date,),
    )
    conn.commit()
    conn.close()
