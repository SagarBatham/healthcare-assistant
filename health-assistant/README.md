# Healthcare Monitoring AI Agent

A personal health assistant built with **Streamlit**, **SQLite**, and a **LangChain**-templated, rule-based chatbot. Tracks medications, logs adherence, records health metrics, and answers health questions offline (no external LLM API required).

## Features

- **Dashboard** — health snapshot, today's schedule, missed-dose alerts, quick actions
- **Schedule** — mark each scheduled dose as Taken / Missed
- **Medications** — add/remove medications with dosage, frequency, and times
- **Health Metrics** — log readings (weight, blood pressure, glucose, heart rate, temperature, oxygen), import from CSV, view trend charts
- **Chatbot** — offline, keyword-based assistant: log doses in natural language ("I took metformin"), check what's due, look up recent readings, get wellness tips

## Tech Stack

- **UI:** Streamlit (multipage app)
- **Database:** SQLite (`health.db`, created automatically on first run)
- **Data handling:** pandas
- **Text templating:** LangChain `PromptTemplate` (no LLM API key needed — the chatbot is rule-based)

## Project Structure

```
health-assistant/
├── app.py                    # Dashboard (main entry point)
├── db.py                     # SQLite data layer (CRUD, schedule, adherence, metrics)
├── chatbot.py                # Rule-based chatbot logic
├── pages/
│   ├── 1_Schedule.py         # Mark doses Taken/Missed
│   ├── 2_Medications.py      # Add/delete medications
│   ├── 3_Health_Metrics.py   # Log readings, CSV import, trend charts
│   └── 4_Chatbot.py          # Chat UI
├── .streamlit/
│   └── config.toml           # Sage green / cream theme
└── requirements.txt
```

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Deploying to Streamlit Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select this repository and branch.
4. Set **Main file path** to `app.py` (or `health-assistant/app.py` if this folder lives inside a larger repo).
5. Click **Deploy**.

No API keys or secrets are required — the chatbot is fully rule-based and works offline.
