"""
Rule-based (offline, keyword-driven) chatbot for the Healthcare Monitoring AI Agent.

No external LLM API is used. LangChain's PromptTemplate is used purely to
format reminder/response text in a consistent, template-driven way.
"""

import re
from datetime import date
from langchain_core.prompts import PromptTemplate

import db

REMINDER_TEMPLATE = PromptTemplate.from_template(
    "Reminder: it's time to take {dosage} of {name}. "
    "You have {pending_count} dose(s) still pending today."
)

LOG_CONFIRM_TEMPLATE = PromptTemplate.from_template(
    "Got it — I've logged that you took {name} ({dosage}). Nice work staying on track!"
)

METRIC_TEMPLATE = PromptTemplate.from_template(
    "Your most recent {metric_type} reading was {value} {unit}, recorded on {recorded_at}."
)

HEALTH_TIPS = [
    "Staying hydrated helps your body absorb medications more effectively — aim for 6-8 glasses of water a day.",
    "Try to take your medications at the same time every day; consistency improves adherence and effectiveness.",
    "Regular light exercise, like a 20-minute walk, can support both cardiovascular and mental health.",
    "Getting 7-9 hours of sleep helps your body regulate blood sugar and blood pressure.",
    "Keep a small log of any side effects you notice — it helps you and your doctor spot patterns early.",
    "Don't skip meals before taking medications that are meant to be taken with food.",
]

GREETINGS = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "namaste"]
HELP_KEYWORDS = ["help", "what can you do", "commands", "options"]
LOG_KEYWORDS = ["i took", "took my", "just took", "taken", "i had"]
DUE_KEYWORDS = ["due", "reminder", "what's next", "upcoming", "schedule", "pending"]
METRIC_KEYWORDS = ["weight", "blood pressure", "glucose", "heart rate", "temperature", "oxygen", "reading", "metric"]
TIP_KEYWORDS = ["tip", "advice", "healthy", "suggestion", "wellness"]
ADHERENCE_KEYWORDS = ["adherence", "how am i doing", "progress", "streak"]


def _match_any(text, keywords):
    return any(k in text for k in keywords)


def _extract_medication_name(text):
    """Try to pull a medication name out of a free-text log message."""
    meds = db.get_medications()
    text_lower = text.lower()
    for med in meds:
        if med["name"].lower() in text_lower:
            return med["name"]

    for kw in LOG_KEYWORDS:
        if kw in text_lower:
            remainder = text_lower.split(kw, 1)[1].strip()
            match = re.match(r"([a-zA-Z\- ]+)", remainder)
            if match:
                candidate = match.group(1).strip().rstrip(".")
                if candidate:
                    return candidate
    return None


def get_response(user_input: str) -> str:
    text = user_input.strip().lower()
    if not text:
        return "I didn't catch that — could you try again?"

    if _match_any(text, GREETINGS):
        return (
            "Hello! I'm your health assistant. I can log medications you've taken, "
            "tell you what's due today, look up your recent health readings, or share a wellness tip. "
            "Try something like \"I took metformin\" or \"what's due today?\""
        )

    if _match_any(text, HELP_KEYWORDS):
        return (
            "Here's what I can help with:\n"
            "- Log a dose: \"I took metformin\"\n"
            "- Check what's due: \"what's due today?\"\n"
            "- Check a reading: \"what's my latest blood pressure?\"\n"
            "- Check your adherence: \"how am I doing?\"\n"
            "- Get a wellness tip: \"give me a health tip\""
        )

    if _match_any(text, ADHERENCE_KEYWORDS):
        rate = db.get_adherence_rate(7)
        return f"Your 7-day medication adherence rate is {rate}%. Keep it up!"

    if _match_any(text, LOG_KEYWORDS):
        med_name = _extract_medication_name(text)
        if not med_name:
            return "I couldn't tell which medication you meant. Could you name it, e.g. \"I took metformin\"?"
        med = db.log_medication_taken_by_name(med_name)
        if not med:
            return f"I don't have \"{med_name}\" in your medication list yet. You can add it on the Medications page."
        return LOG_CONFIRM_TEMPLATE.format(name=med["name"], dosage=med["dosage"])

    if _match_any(text, DUE_KEYWORDS):
        alerts = db.get_due_alerts()
        if not alerts:
            return "Nothing due right now — you're all caught up for today!"
        pending_count = len(alerts)
        next_dose = alerts[0]
        return REMINDER_TEMPLATE.format(
            dosage=next_dose["dosage"], name=next_dose["name"], pending_count=pending_count
        )

    if _match_any(text, METRIC_KEYWORDS):
        metric_map = {
            "weight": "Weight",
            "blood pressure": "Blood Pressure (Systolic)",
            "glucose": "Blood Glucose",
            "heart rate": "Heart Rate",
            "temperature": "Temperature",
            "oxygen": "Oxygen Saturation",
        }
        for key, metric_type in metric_map.items():
            if key in text:
                latest = db.get_latest_metric(metric_type)
                if not latest:
                    return f"You haven't logged any {metric_type} readings yet. Add one on the Health Metrics page."
                return METRIC_TEMPLATE.format(
                    metric_type=metric_type,
                    value=latest["value"],
                    unit=latest["unit"],
                    recorded_at=latest["recorded_at"][:16].replace("T", " "),
                )
        return "Which metric would you like — weight, blood pressure, glucose, heart rate, temperature, or oxygen saturation?"

    if _match_any(text, TIP_KEYWORDS):
        import random
        return random.choice(HEALTH_TIPS)

    return (
        "I'm not sure I understood that. I can log medications (\"I took metformin\"), "
        "check what's due, look up a recent reading, or share a health tip — try one of those!"
    )
