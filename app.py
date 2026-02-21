import matplotlib
matplotlib.use("Agg")

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import calendar
from datetime import datetime, date
from groq import Groq

# PDF GENERATION
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
import os

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

if "mood_intensity" not in st.session_state:
    st.session_state.mood_intensity = []

if "mood_dates" not in st.session_state:
    st.session_state.mood_dates = []

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

CRISIS_WORDS = ["suicide", "kill myself", "end my life", "self harm", "i want to die"]

def safety_check(text):
    return any(word in text.lower() for word in CRISIS_WORDS)

# ===============================
# EMOTION + INTENSITY DETECTION
# ===============================

def detect_emotion():

    try:
        recent_text = ""
        for role, msg in st.session_state.chat_history[-6:]:
            if role == "user":
                recent_text += msg + "\n"

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Classify the user's emotional state.
Choose one emotion: Anxiety, Sadness, Anger, Burnout, Positive, Neutral.
Also assign intensity from 1 to 5.
Respond strictly in format:
Emotion: <emotion>
Intensity: <number>"""
                },
                {"role": "user", "content": recent_text}
            ],
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=20,
        )

        result = completion.choices[0].message.content

        lines = result.split("\n")
        emotion = lines[0].split(":")[1].strip()
        intensity = int(lines[1].split(":")[1].strip())

    except:
        emotion = "Neutral"
        intensity = 3

    score_map = {
        "Anxiety": -1,
        "Sadness": -1,
        "Anger": -1,
        "Burnout": -1,
        "Positive": 1,
        "Neutral": 0
    }

    return emotion, score_map.get(emotion, 0), intensity

# ===============================
# AI RESPONSE
# ===============================

def generate_response():

    messages = [
        {
            "role": "system",
            "content": "You are a compassionate mental health support assistant."
        }
    ]

    for role, message in st.session_state.chat_history[-20:]:
        messages.append({"role": role, "content": message})

    completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=200,
    )

    return completion.choices[0].message.content

# ===============================
# COPING STRATEGY GENERATOR
# ===============================

def generate_coping_strategy():

    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Provide one short practical coping strategy."},
            {"role": "user", "content": "User emotional context: " + ", ".join(st.session_state.mood_labels[-3:])}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=100,
    )

    return completion.choices[0].message.content

# ===============================
# CHAT PAGE
# ===============================

if page == "💬 Chat":

    st.title("💬 AI Mental Health Companion")

    # Daily Check-in Reminder
    today = date.today().isoformat()
    if today not in st.session_state.mood_dates:
        st.info("💛 You haven't checked in today.")

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

    user_input = st.chat_input("How are you feeling today?")

    if user_input:

        if safety_check(user_input):
            st.error("🚨 If in danger call emergency services or 988 (US).")
        else:
            st.session_state.chat_history.append(("user", user_input))

            emotion, score, intensity = detect_emotion()

            st.session_state.mood_scores.append(score * intensity)
            st.session_state.mood_labels.append(emotion)
            st.session_state.mood_intensity.append(intensity)
            st.session_state.mood_dates.append(today)

            with st.chat_message("assistant"):
                reply = generate_response()
                st.write(reply)

            st.session_state.chat_history.append(("assistant", reply))

    if st.button("🧘 Suggest Coping Strategy"):
        strategy = generate_coping_strategy()
        st.success(strategy)

# ===============================
# ANALYTICS PAGE
# ===============================

elif page == "📊 Analytics":

    st.title("📊 Emotional Analytics")

    if len(st.session_state.mood_scores) == 0:
        st.info("Start chatting to see analytics.")
    else:

        # Trend Graph
        fig1, ax1 = plt.subplots()
        ax1.plot(st.session_state.mood_scores)
        ax1.set_title("Mood Trend")
        st.pyplot(fig1)

        # Mood Calendar
        st.subheader("📅 Mood Calendar")

        current_year = datetime.now().year
        current_month = datetime.now().month

        cal = calendar.monthcalendar(current_year, current_month)
        month_matrix = np.zeros((len(cal), 7))

        for i, week in enumerate(cal):
            for j, day in enumerate(week):
                if day != 0:
                    day_str = f"{current_year}-{current_month:02d}-{day:02d}"
                    if day_str in st.session_state.mood_dates:
                        idx = st.session_state.mood_dates.index(day_str)
                        month_matrix[i][j] = st.session_state.mood_scores[idx]

        fig2, ax2 = plt.subplots()
        ax2.imshow(month_matrix, aspect="auto")
        ax2.set_title("Monthly Mood Heatmap")
        st.pyplot(fig2)

        # PDF Export
        if st.button("📄 Export Analytics as PDF"):

            pdf_path = "mental_wellness_report.pdf"
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            elements = []

            styles = getSampleStyleSheet()
            elements.append(Paragraph("Mental Wellness Report", styles["Title"]))
            elements.append(Spacer(1, 0.3 * inch))

            avg = round(np.mean(st.session_state.mood_scores), 2)
            elements.append(Paragraph(f"Average Mood Score: {avg}", styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))

            data = [["Session", "Mood Score"]]
            for i, score in enumerate(st.session_state.mood_scores):
                data.append([str(i+1), str(score)])

            table = Table(data)
            elements.append(table)

            doc.build(elements)

            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF Report", f, file_name=pdf_path)

            os.remove(pdf_path)

# ===============================
# JOURNAL PAGE
# ===============================

elif page == "📔 Journal":

    st.title("📔 Journal")

    text = st.text_area("Write here...")

    if st.button("Save Entry"):
        if text.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.journal_entries.append(f"{timestamp}\n{text}\n")
            st.success("Saved!")

    for entry in reversed(st.session_state.journal_entries):
        st.text(entry)

# ===============================
# ABOUT PAGE
# ===============================

elif page == "ℹ About":

    st.title("About This App")

    st.write("""
AI-powered mental wellness companion using:
- Llama 3.1 via Groq
- Mood intensity scoring
- Mood calendar heatmap
- Coping strategy generator
- PDF analytics export
- Journaling system

This app is for support only and not a replacement for professional care.
""")
