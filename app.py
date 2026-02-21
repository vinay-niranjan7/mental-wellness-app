import os
import matplotlib
matplotlib.use("Agg")

import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime


# ===============================
# LOAD ENV VARIABLES
# ===============================

HF_TOKEN = st.secrets["HF_TOKEN"]

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# ===============================
# PAGE CONFIG
# ===============================

st.set_page_config(
    page_title="AI Mental Wellness Companion",
    page_icon="🧠",
    layout="wide"
)

# ===============================
# SESSION STATE INIT
# ===============================

if "mood_scores" not in st.session_state:
    st.session_state.mood_scores = []

if "mood_labels" not in st.session_state:
    st.session_state.mood_labels = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "journal_entries" not in st.session_state:
    st.session_state.journal_entries = []

# ===============================
# SIDEBAR
# ===============================

with st.sidebar:
    st.title("🧠 Mental Wellness App")
    page = st.radio("Navigate", ["💬 Chat", "📊 Analytics", "📔 Journal", "ℹ About"])

# ===============================
# EMOTION DETECTION
# ===============================

def detect_emotion(text):
    text = text.lower()

    if any(word in text for word in ["anxious", "nervous", "worried", "panic"]):
        return "Anxiety", -1
    elif any(word in text for word in ["sad", "depressed", "hopeless", "lonely"]):
        return "Sadness", -1
    elif any(word in text for word in ["angry", "mad", "frustrated", "irritated"]):
        return "Anger", -1
    elif any(word in text for word in ["tired", "burnout", "exhausted", "drained"]):
        return "Burnout", -1
    elif any(word in text for word in ["happy", "excited", "grateful", "good", "great", "awesome"]):
        return "Positive", 1
    else:
        return "Neutral", 0

# ===============================
# CRISIS DETECTION
# ===============================

CRISIS_WORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
    "i want to die"
]

def safety_check(text):
    return any(word in text.lower() for word in CRISIS_WORDS)

# ===============================
# AI RESPONSE GENERATION
# ===============================

def generate_response(user_message, emotion):

    prompt = f"""
You are a compassionate AI mental health support assistant.
The user is experiencing {emotion}.
Respond with empathy, validation, and gentle encouragement.
Keep response under 120 words.

User: {user_message}
Assistant:
"""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            return f"API Error: {response.status_code}"

        result = response.json()

        if "error" in result:
            return f"Model Error: {result['error']}"

        if isinstance(result, list):
            return result[0]["generated_text"].strip()

        return "Unexpected API response."

    except Exception as e:
        return f"Connection error: {str(e)}"

# ===============================
# CHAT PAGE
# ===============================

if page == "💬 Chat":

    st.title("💬 AI Mental Health Companion")
    st.warning("⚠ This is not a licensed therapist. In crisis, contact emergency services.")

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

    user_input = st.chat_input("How are you feeling today?")

    if user_input:

        if safety_check(user_input):
            st.error("🚨 If you're in immediate danger, contact a suicide prevention hotline immediately.")
        else:
            emotion, score = detect_emotion(user_input)

            st.session_state.mood_scores.append(score)
            st.session_state.mood_labels.append(emotion)
            st.session_state.chat_history.append(("user", user_input))

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = generate_response(user_input, emotion)
                    st.write(reply)

            st.session_state.chat_history.append(("assistant", reply))

# ===============================
# ANALYTICS PAGE
# ===============================

elif page == "📊 Analytics":

    st.title("📊 Emotional Analytics Dashboard")

    if len(st.session_state.mood_scores) == 0:
        st.info("No mood data yet. Start chatting to see analytics.")
    else:

        st.subheader("Mood Trend Over Time")

        fig1, ax1 = plt.subplots()
        ax1.plot(st.session_state.mood_scores)
        ax1.set_xlabel("Session")
        ax1.set_ylabel("Mood Level (-1 to 1)")
        st.pyplot(fig1)

        average = sum(st.session_state.mood_scores) / len(st.session_state.mood_scores)
        st.metric("Average Mood Score", round(average, 2))

        st.subheader("Emotion Distribution")

        emotion_counts = {}
        for label in st.session_state.mood_labels:
            emotion_counts[label] = emotion_counts.get(label, 0) + 1

        fig2, ax2 = plt.subplots()
        ax2.pie(
            emotion_counts.values(),
            labels=emotion_counts.keys(),
            autopct='%1.1f%%'
        )
        st.pyplot(fig2)

# ===============================
# JOURNAL PAGE
# ===============================

elif page == "📔 Journal":

    st.title("📔 Daily Journal")

    journal_text = st.text_area("Write your thoughts here...")

    if st.button("Save Entry"):
        if journal_text.strip():
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"{date}\n{journal_text}\n\n"
            st.session_state.journal_entries.append(entry)
            st.success("Journal entry saved!")

    if st.session_state.journal_entries:

        st.subheader("Your Entries")

        for entry in reversed(st.session_state.journal_entries):
            st.text(entry)

        full_text = "\n".join(st.session_state.journal_entries)

        st.download_button(
            "Download Journal",
            full_text,
            file_name="journal.txt"
        )

# ===============================
# ABOUT PAGE
# ===============================

elif page == "ℹ About":

    st.title("ℹ About This Project")

    st.write("""
This AI Mental Wellness Companion was developed as part of an IBM Virtual Internship project.

### Features:
- AI-powered empathetic chatbot
- Emotion detection
- Crisis keyword detection
- Mood analytics dashboard
- Personal journaling tool
- Responsible AI disclaimer

### Technologies Used:
- Python
- Streamlit
- HuggingFace Inference API
- Matplotlib

This system is designed for supportive guidance only and does not replace professional mental health care.
""")

