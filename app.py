import matplotlib
matplotlib.use("Agg")

import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from groq import Groq

# ===============================
# LOAD GROQ API KEY
# ===============================

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

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
# AI EMOTION DETECTION (Context Aware)
# ===============================

def detect_emotion():

    try:
        recent_text = ""
        for role, msg in st.session_state.chat_history[-6:]:
            if role == "user":
                recent_text += msg + "\n"

        emotion_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Based on the conversation, classify the user's overall emotional state into one of these categories only: Anxiety, Sadness, Anger, Burnout, Positive, Neutral. Respond with just one word."
                },
                {
                    "role": "user",
                    "content": recent_text
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=10,
        )

        emotion = emotion_completion.choices[0].message.content.strip()

    except Exception:
        emotion = "Neutral"

    score_map = {
        "Anxiety": -1,
        "Sadness": -1,
        "Anger": -1,
        "Burnout": -1,
        "Positive": 1,
        "Neutral": 0
    }

    return emotion, score_map.get(emotion, 0)

# ===============================
# AI RESPONSE WITH MEMORY LIMIT
# ===============================

def generate_response():

    try:
        messages = [
            {
                "role": "system",
                "content": "You are a compassionate mental health support assistant. Provide empathetic, safe, and supportive responses."
            }
        ]

        recent_history = st.session_state.chat_history[-20:]

        for role, message in recent_history:
            messages.append({
                "role": role,
                "content": message
            })

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=200,
        )

        return chat_completion.choices[0].message.content

    except Exception:
        return "AI service is temporarily unavailable. Please try again."

# ===============================
# AI MOOD INSIGHT GENERATION
# ===============================

def generate_mood_insight():

    if not st.session_state.mood_labels:
        return "Not enough data yet."

    try:
        mood_text = ", ".join(st.session_state.mood_labels)

        insight_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the user's mood trend and provide a short supportive insight in 2-3 sentences."
                },
                {
                    "role": "user",
                    "content": f"Mood history: {mood_text}"
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=100,
        )

        return insight_completion.choices[0].message.content

    except Exception:
        return "Mood insight unavailable."

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
            st.error("""
🚨 If you're in immediate danger:

• 🇺🇸 Call or text 988  
• 🇬🇧 Samaritans: 116 123  
• Or contact local emergency services
""")
        else:
            st.session_state.chat_history.append(("user", user_input))

            emotion, score = detect_emotion()
            st.session_state.mood_scores.append(score)
            st.session_state.mood_labels.append(emotion)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = generate_response()
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

        st.subheader("AI Mood Insight")
        insight = generate_mood_insight()
        st.info(insight)

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
This AI Mental Wellness Companion integrates Llama 3.1 via Groq's free API to provide empathetic, context-aware support.

### Features:
- Context-aware conversational memory
- AI-based emotion classification
- Crisis keyword detection
- Mood analytics dashboard
- AI-generated mood insights
- Personal journaling tool

This system is designed for supportive guidance only and does not replace professional mental health care.
""")
