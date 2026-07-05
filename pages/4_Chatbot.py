"""Chatbot page — offline, rule-based health assistant chat UI."""

import streamlit as st

import db
import chatbot

st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")
db.init_db()

st.title("💬 Health Assistant Chat")
st.caption("Ask about your medications, schedule, health readings, or get a wellness tip. (Offline, rule-based — no external AI service.)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "Hi! I'm your health assistant. Try asking me \"what's due today?\" or tell me \"I took metformin\".",
        }
    ]

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type a message...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    response = chatbot.get_response(user_input)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()

st.divider()
st.subheader("Quick prompts")
qp1, qp2, qp3, qp4 = st.columns(4)
quick_prompts = ["What's due today?", "How am I doing?", "Give me a health tip", "Help"]
cols = [qp1, qp2, qp3, qp4]
for col, prompt in zip(cols, quick_prompts):
    with col:
        if st.button(prompt, use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            response = chatbot.get_response(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
