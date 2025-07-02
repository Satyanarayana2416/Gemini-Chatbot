import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import uuid
import pandas as pd


# --- INIT SETUP ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

CSV_FILE = "chat_history.csv"
if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
    chat_df = pd.read_csv(CSV_FILE)
else:
    chat_df = pd.DataFrame(columns=["chat_id", "title", "role", "content"])
    chat_df.to_csv(CSV_FILE, index=False)

# --- SESSION STATE ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if "chat_title" not in st.session_state:
    st.session_state.chat_title = "Untitled Chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SAVE FUNCTION ---
def save_message(role, content):
    global chat_df
    new_row = {
        "chat_id": st.session_state.chat_id,
        "title": st.session_state.chat_title,
        "role": role,
        "content": content
    }
    chat_df = pd.concat([chat_df, pd.DataFrame([new_row])], ignore_index=True)
    chat_df.to_csv(CSV_FILE, index=False)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📁 Chat Sessions")

    st.subheader("✏️ Rename Chat")
    new_title = st.text_input("Chat Title", value=st.session_state.get("chat_title", "Untitled Chat"))
    st.session_state.chat_title = new_title
    chat_df.loc[chat_df["chat_id"] == st.session_state.chat_id, "title"] = new_title
    chat_df.to_csv(CSV_FILE, index=False)

    st.markdown("---")
    st.subheader("🗂️ Saved Chats")

    for cid in chat_df["chat_id"].unique()[::-1]:
        title = chat_df[chat_df["chat_id"] == cid]["title"].iloc[0]
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(f"📄 {title}", key=f"load_{cid}"):
                st.session_state.chat_id = cid
                st.session_state.chat_title = title
                st.session_state.messages = chat_df[chat_df["chat_id"] == cid][["role", "content"]].to_dict("records")
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{cid}"):
                chat_df = chat_df[chat_df["chat_id"] != cid]
                chat_df.to_csv(CSV_FILE, index=False)
                if st.session_state.chat_id == cid:
                    st.session_state.chat_id = str(uuid.uuid4())
                    st.session_state.chat_title = "Untitled Chat"
                    st.session_state.messages = []
                st.rerun()

    if st.button("➕ New Chat"):
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.chat_title = "Untitled Chat"
        st.session_state.messages = []
        st.rerun()

# --- MAIN CHAT UI ---
st.title("💬 Purnith Chatbot")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Say something...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    response = model.generate_content(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    save_message("assistant", response.text)
    with st.chat_message("assistant"):
        st.markdown(response.text)

# --- END OF MAIN UI ---