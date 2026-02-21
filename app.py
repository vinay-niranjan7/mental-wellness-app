import matplotlib
matplotlib.use("Agg")

import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from groq import Groq
import time

# ===============================
# PAGE CONFIG
# ===============================

st.set_page_config(
    page_title="AI Mental Wellness Companion",
    page_icon="🧠",
    layout="wide"
)

# ===============================
# LOAD API KEY
# ===============================

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# ===============================
# SESSION STATE
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

    theme_mode = st.toggle("🌙 Dark Mode", value=False)
    private_mode = st.toggle("🔒 Private Mode", value=False)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "💬 Chat",
            "📊 Analytics",
            "📔 Journal",
            "🧘 Wellness Tools",
            "🌱 Growth Tracker",
            "📝 Weekly Reflection",
            "ℹ About"
        ]
    )

# ===============================
# THEME STYLING
# ===============================

if theme_mode:
    st.markdown("""
    <style>
    .stApp {background-color: #0E1117; color: #FAFAFA;}
    section[data-testid="stSidebar"] {background-color: #161B22;}
    .stMetric {background-color: #1E2228; padding: 10px; border-radius: 10px; color: white;}
    .stButton button {background-color: #2E8B57; color: white; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stMetric {background-color: #E6EAF1; padding: 10px; border-radius: 10px;}
    .stButton button {border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

# ===============================
# CRISIS DETECTION
# ===============================

CRISIS_WORDS = ["suicide", "kill myself", "end my life", "self harm", "i want to die"]

def safety_check(text):
    return any(word in text.lower() for word in CRISIS_WORDS)

# ===============================
# AI EMOTION DETECTION
# ===============================

def detect_emotion():
    try:
        recent_text = ""
        for role, msg in st.session_state.chat_history[-6:]:
            if role == "user":
                recent_text += msg + "\n"

        response = client.chat.completions.create(
            messages=[
                {"role": "system",
                 "content": "Classify the user's emotional state into one word only: Anxiety, Sadness, Anger, Burnout, Positive, Neutral."},
                {"role": "user", "content": recent_text}
            ],
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=10,
        )

        emotion = response.choices[0].message.content.strip()
    except:
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
# AI RESPONSE (WITH MEMORY LIMIT)
# ===============================

def generate_response():
    try:
        messages = [
            {"role": "system",
             "content": "You are a compassionate mental health support assistant. Be empathetic and supportive."}
        ]

        recent_history = st.session_state.chat_history[-20:]

        for role, message in recent_history:
            messages.append({"role": role, "content": message})

        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=200,
        )

        return response.choices[0].message.content
    except:
        return "AI service temporarily unavailable."

# ===============================
# AI MOOD INSIGHT
# ===============================

def generate_mood_insight():
    if not st.session_state.mood_labels:
        return "Not enough data yet."

    try:
        mood_text = ", ".join(st.session_state.mood_labels)

        response = client.chat.completions.create(
            messages=[
                {"role": "system",
                 "content": "Provide a short emotional insight based on mood trend."},
                {"role": "user",
                 "content": f"Mood history: {mood_text}"}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=100,
        )

        return response.choices[0].message.content
    except:
        return "Insight unavailable."

# ===============================
# CHAT PAGE
# ===============================

if page == "💬 Chat":

    st.title("💬 AI Mental Health Companion")
    st.warning("⚠ Not a licensed therapist. In crisis, contact emergency services.")

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

    user_input = st.chat_input("How are you feeling today?")

    if user_input:

        if safety_check(user_input):
            st.error("🚨 If in danger, contact local emergency services immediately.")
        else:
            if not private_mode:
                st.session_state.chat_history.append(("user", user_input))

            emotion, score = detect_emotion()

            if not private_mode:
                st.session_state.mood_scores.append(score)
                st.session_state.mood_labels.append(emotion)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = generate_response()
                    st.write(reply)

            if not private_mode:
                st.session_state.chat_history.append(("assistant", reply))

# ===============================
# ANALYTICS PAGE
# ===============================

elif page == "📊 Analytics":

    st.title("📊 Emotional Analytics")

    if not st.session_state.mood_scores:
        st.info("No data yet.")
    else:
        fig, ax = plt.subplots()
        ax.plot(st.session_state.mood_scores)
        ax.set_ylabel("Mood Score")
        st.pyplot(fig)

        st.metric("Average Mood",
                  round(sum(st.session_state.mood_scores) /
                        len(st.session_state.mood_scores), 2))

        st.subheader("AI Insight")
        st.info(generate_mood_insight())

# ===============================
# JOURNAL PAGE
# ===============================

elif page == "📔 Journal":

    st.title("📔 Journal")

    text = st.text_area("Write your thoughts")

    if st.button("Save Entry"):
        if text.strip():
            entry = f"{datetime.now()}\n{text}\n"
            st.session_state.journal_entries.append(entry)
            st.success("Saved")

    for entry in reversed(st.session_state.journal_entries):
        st.text(entry)

# ===============================
# WELLNESS TOOLS
# ===============================

elif page == "🧘 Wellness Tools":

    st.title("🧘 Wellness Tools")

    tool = st.selectbox("Choose tool",
                        ["Breathing", "Grounding", "Gratitude"])

    if tool == "Breathing":
        st.write("Inhale 4s • Hold 4s • Exhale 6s")
        if st.button("Start"):
            for i in range(100):
                time.sleep(0.03)
                st.progress(i + 1)

    elif tool == "Grounding":
        st.write("5 things you see, 4 feel, 3 hear, 2 smell, 1 taste")

    elif tool == "Gratitude":
        st.text_area("Write 3 things you're grateful for")

# ===============================
# GROWTH TRACKER
# ===============================

elif page == "🌱 Growth Tracker":

    st.title("🌱 Growth Tracker")

    if not st.session_state.mood_scores:
        st.info("No data yet.")
    else:
        positive_ratio = (
            st.session_state.mood_scores.count(1) /
            len(st.session_state.mood_scores)
        )
        stability = 1 - abs(sum(st.session_state.mood_scores)) / \
            (len(st.session_state.mood_scores) + 1)

        col1, col2 = st.columns(2)
        col1.metric("Positive Ratio",
                    f"{round(positive_ratio * 100)}%")
        col2.metric("Stability Index",
                    round(stability, 2))

# ===============================
# WEEKLY REFLECTION
# ===============================

elif page == "📝 Weekly Reflection":

    st.title("📝 AI Weekly Reflection")

    st.info(generate_mood_insight())

# ===============================
# ABOUT
# ===============================

elif page == "ℹ About":

    st.title("ℹ About")

    st.write("""
AI-powered mental wellness companion built with:

- Llama 3.1 (Groq free API)
- Context-aware memory
- AI emotion detection
- Mood analytics
- Growth tracking
- Wellness interventions
""")
