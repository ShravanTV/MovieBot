import streamlit as st
import requests
import uuid
import os

API_URL = os.getenv('API_URL', 'http://backend:8000/query').rstrip('/')


st.title("MovieBot")

# Session state for chat history, session_id, and BMI
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())


# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div style="text-align:right;background:#DCF8C6;padding:8px;border-radius:10px;margin:4px 0;">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:left;background:#F1F0F0;padding:8px;border-radius:10px;margin:4px 0;">{msg["content"]}</div>', unsafe_allow_html=True)

# User input
if prompt := st.chat_input("Ask about movie..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.markdown(f'<div style="text-align:right;background:#DCF8C6;padding:8px;border-radius:10px;margin:4px 0;">{prompt}</div>', unsafe_allow_html=True)

    # Call backend API, include BMI if available
    payload = {
        "session_id": st.session_state["session_id"],
        "chat_history": st.session_state["messages"][-6:]
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        ai_message = response.json().get("ai_message", "")
    except Exception as e:
        ai_message = f"[Error contacting backend: {e}]"
    st.session_state["messages"].append({"role": "assistant", "content": ai_message})
    st.markdown(f'<div style="text-align:left;background:#F1F0F0;padding:8px;border-radius:10px;margin:4px 0;">{ai_message}</div>', unsafe_allow_html=True)


