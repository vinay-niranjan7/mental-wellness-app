import matplotlib
matplotlib.use("Agg")

import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
import time
import json
import os
import random
import requests
from groq import Groq

# ===============================
# PAGE CONFIG
# ===============================

st.set_page_config(
    page_title="AI Mental Wellness Companion",
    page_icon="🧠",
    layout="wide"
)

# ===============================
# CUSTOM CSS
# ===============================

st.markdown("""
<style>
.stApp { background-color: #f8f9fa; color: #212529; }
.affirmation-box { background: linear-gradient(135deg, #667eea, #764ba2); 
                   border-radius: 15px; padding: 20px; text-align: center; 
                   font-size: 1.2em; color: white; margin: 10px 0; }
.grounding-card { background: white; border-left: 4px solid #667eea; 
                  border-radius: 8px; padding: 15px; margin: 10px 0;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.quote-box { background: linear-gradient(135deg, #f093fb, #f5576c); 
             border-radius: 12px; padding: 20px; font-style: italic; 
             text-align: center; color: white; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ===============================
# GROQ CLIENT
# ===============================

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# ===============================
# PERSISTENT STORAGE (JSON per user)
# ===============================

DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

def _user_path(username: str) -> str:
    """Return a safe file path for the given username."""
    safe = "".join(c for c in username if c.isalnum() or c in ("-", "_")).lower()
    return os.path.join(DATA_DIR, f"{safe}.json")

# Keys that are persisted to disk
PERSISTENT_KEYS = [
    "mood_scores", "mood_labels", "mood_dates",
    "chat_history", "journal_entries", "gratitude_entries",
    "check_in_done_today", "last_check_in_date",
    "streak", "writing_streak", "last_journal_date",
    "affirmation_of_day", "affirmation_date",
    "streak_updated_date",
]

# Defaults for a brand-new user profile
PROFILE_DEFAULTS = {
    "mood_scores": [],
    "mood_labels": [],
    "mood_dates": [],
    "chat_history": [],
    "journal_entries": [],
    "gratitude_entries": [],
    "check_in_done_today": False,
    "last_check_in_date": None,
    "streak": 0,
    "writing_streak": 0,
    "last_journal_date": None,
    "affirmation_of_day": None,
    "affirmation_date": None,
    "streak_updated_date": None,
}

def load_user_data(username: str) -> dict:
    """Load a user's saved profile, or return fresh defaults."""
    path = _user_path(username)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Fill missing keys added in newer app versions
            for k, v in PROFILE_DEFAULTS.items():
                if k not in data:
                    data[k] = v
            # Sanitize any dirty labels saved by older app versions (e.g. "Positive.")
            _emotion_known = ["Anxiety", "Sadness", "Anger", "Burnout", "Positive", "Neutral"]
            _sentiment_known = ["Positive", "Negative", "Neutral"]
            data["mood_labels"] = [
                next((k for k in _emotion_known if k.lower() in lbl.lower()), "Neutral")
                for lbl in data.get("mood_labels", [])
            ]
            for entry in data.get("journal_entries", []):
                raw = entry.get("sentiment", "Neutral")
                entry["sentiment"] = next((k for k in _sentiment_known if k.lower() in raw.lower()), "Neutral")
            return data
        except Exception:
            pass
    return dict(PROFILE_DEFAULTS)

def save_user_data(username: str):
    """Write all persistent session-state keys to disk."""
    path = _user_path(username)
    payload = {k: st.session_state[k] for k in PERSISTENT_KEYS if k in st.session_state}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"Could not save data: {e}")

def flush():
    """Save to disk then rerun — convenience wrapper after mutations."""
    save_user_data(st.session_state.username)
    st.rerun()

# ===============================
# GOOGLE OAUTH — LOGIN GATE
# ===============================
# Uses Streamlit's built-in st.login() / st.user / st.logout().
# No extra library needed. Handles cookies + session automatically.
# Persistent across refreshes — Google cookie survives browser restarts.
# -------------------------------------------------------

if not st.user.is_logged_in:
    st.title("🧠 AI Mental Wellness Companion")
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### Your safe space to check in, reflect, and grow 🌱

        This app offers:
        - 💬 **AI-powered empathetic chat** support
        - 📊 **Mood analytics** to understand your patterns
        - 📔 **Private journaling** with AI prompts
        - 🧘 **Wellness tools** — breathing, grounding, affirmations
        - 🙏 **Gratitude log** for daily positivity

        > ⚠️ This is **not** a replacement for licensed mental health care.  
        > In a crisis, please contact your local emergency services.
        """)
        st.markdown("###")
        st.button("🔐 Sign in with Google", on_click=st.login, type="primary")
    with col2:
        st.markdown("<div style='text-align:center;font-size:5em;margin-top:40px'>🌿</div>",
                    unsafe_allow_html=True)
    st.stop()

# User is logged in — derive username from their Google profile
# Use first name for display, email as unique key for data file
_google_name  = st.user.get("name", "Friend")
_google_email = st.user.get("email", "unknown")
_display_name = _google_name.split()[0]  # first name only

# ===============================
# SESSION STATE BOOTSTRAP
# ===============================

if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# username drives the JSON filename — use email so it's unique per Google account
if "username" not in st.session_state:
    st.session_state.username = _google_email

# ===============================
# LOAD PERSISTENT DATA (once per session)
# ===============================

if not st.session_state.data_loaded:
    profile = load_user_data(st.session_state.username)
    for k, v in profile.items():
        st.session_state[k] = v
    st.session_state.data_loaded = True

# Defined here so every page section can use them
today = date.today()
today_str = str(today)

# ===============================
# SIDEBAR
# ===============================

with st.sidebar:
    st.title(f"🧠 Hi, {_display_name}!")
    st.caption(f"📧 {_google_email}")

    # Update streak exactly once per calendar day
    if st.session_state.get("streak_updated_date") != today_str:
        last_ci = st.session_state.last_check_in_date
        if last_ci:
            try:
                last_date = date.fromisoformat(last_ci) if isinstance(last_ci, str) else last_ci
                if last_date == today - timedelta(days=1):
                    st.session_state.streak += 1
                elif last_date != today:
                    st.session_state.streak = 1
                # If last_date == today: already counted this day, no change
            except ValueError:
                st.session_state.streak = 1
        else:
            st.session_state.streak = 1
        st.session_state.streak_updated_date = today_str
        save_user_data(st.session_state.username)

    st.markdown(f"🔥 **{st.session_state.streak}-day streak**")
    st.markdown("---")

    page = st.radio("Navigate", [
        "🏠 Home", "💬 Chat", "📊 Analytics",
        "📔 Journal", "🙏 Gratitude", "🧘 Wellness Tools", "ℹ About"
    ])

    st.markdown("---")
    st.button("🚪 Log Out", on_click=st.logout)

# ===============================
# CRISIS DETECTION
# ===============================

CRISIS_WORDS = [
    # Direct suicidal ideation
    "suicide", "suicidal", "kill myself", "killing myself",
    "end my life", "take my life", "end it all", "end it",
    "i want to die", "i wanna die", "wanna die", "want to die",
    "i'm going to die", "i will die", "i should die", "i deserve to die",
    "better off dead", "better off without me", "world without me",
    "no reason to live", "nothing to live for", "not worth living",
    "life is not worth living", "life isn't worth living",

    # Self-harm
    "self harm", "self-harm", "hurt myself", "harm myself",
    "cut myself", "cutting myself", "burn myself", "burning myself",
    "injure myself", "punish myself", "hurt myself on purpose",

    # Disappearing / giving up
    "want to disappear", "wish i could disappear", "disappear forever",
    "don't want to exist", "don't want to be here", "don't want to be alive",
    "wish i was never born", "wish i wasn't here", "wish i were dead",
    "tired of living", "tired of life", "done with life", "done with everything",
    "can't go on", "can't keep going", "can't do this anymore",
    "no point anymore", "no point in living", "no point going on",
    "give up on life", "giving up on life",

    # Hopelessness / farewell signals
    "goodbye forever", "final goodbye", "last goodbye", "saying goodbye",
    "nobody would miss me", "no one would miss me", "no one cares if i die",
    "nobody cares if i'm gone", "everyone is better off without me",
    "i have a plan to", "i've made a plan", "i've decided to end",
    "planned my death", "planning to kill",

    # Methods (intentionally vague to avoid instruction)
    "overdose on", "overdosing on", "take all my pills",
    "jump off", "hang myself", "hanging myself",
]

def safety_check(text):
    return any(w in text.lower() for w in CRISIS_WORDS)

# ===============================
# GROQ HELPERS
# ===============================

def detect_emotion():
    if not st.session_state.chat_history:
        return "Neutral", 0
    recent_text = "\n".join(
        msg for role, msg, _ in st.session_state.chat_history[-6:] if role == "user"
    )
    if not recent_text.strip():
        return "Neutral", 0
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Classify the user's emotional state into one of: Anxiety, Sadness, Anger, Burnout, Positive, Neutral. Respond with one word only."},
                {"role": "user", "content": recent_text}
            ],
            model="llama-3.1-8b-instant", temperature=0, max_tokens=10,
        )
        emotion = completion.choices[0].message.content.strip()
    except Exception:
        emotion = "Neutral"
    # Normalize to a known label — guards against "Positive." or "positive" variants
    known = ["Anxiety", "Sadness", "Anger", "Burnout", "Positive", "Neutral"]
    emotion = next((k for k in known if k.lower() in emotion.lower()), "Neutral")
    score_map = {"Anxiety": -1, "Sadness": -1, "Anger": -1, "Burnout": -1, "Positive": 1, "Neutral": 0}
    return emotion, score_map.get(emotion, 0)


def generate_response():
    try:
        messages = [{"role": "system", "content": (
            f"You are a compassionate mental health and emotional wellness assistant. "
            f"The user's name is {_display_name}. "
            "You ONLY discuss topics related to mental health, emotional wellbeing, stress, anxiety, depression, "
            "relationships, self-care, mindfulness, grief, motivation, loneliness, sleep, burnout, and similar "
            "emotional or psychological topics. "
            "If the user asks about ANYTHING else — such as shopping, cars, sports, technology, finance, coding, "
            "general knowledge, or any non-mental-health subject — you must politely decline and gently redirect "
            "them back to their emotional wellbeing. For example say: "
            "'I'm only able to support you with mental health and emotional wellness topics. "
            "Is there something on your mind emotionally that you'd like to talk about?' "
            "Never answer off-topic questions even if the user insists. "
            "Keep responses concise (2-4 sentences) and always warm and empathetic."
        )}]
        for role, message, _ in st.session_state.chat_history[-20:]:
            messages.append({"role": role, "content": message})
        completion = client.chat.completions.create(
            messages=messages, model="llama-3.1-8b-instant", temperature=0.7, max_tokens=200,
        )
        return completion.choices[0].message.content
    except Exception:
        return "I'm here for you. The AI service is temporarily unavailable — please try again in a moment."


def generate_mood_insight():
    if not st.session_state.mood_labels:
        return "Start chatting to receive mood insights."
    try:
        mood_text = ", ".join(st.session_state.mood_labels[-20:])
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Analyze the user's mood trend and provide a short supportive insight in 2-3 sentences. Be warm and encouraging."},
                {"role": "user", "content": f"Mood history: {mood_text}"}
            ],
            model="llama-3.1-8b-instant", temperature=0.5, max_tokens=120,
        )
        return completion.choices[0].message.content
    except Exception:
        return "Mood insight unavailable."


def generate_weekly_summary():
    if not st.session_state.mood_labels:
        return "No data available for a weekly summary yet."
    try:
        last_week = st.session_state.mood_labels[-14:]
        avg_score = sum(st.session_state.mood_scores[-14:]) / max(len(st.session_state.mood_scores[-14:]), 1)
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Write a warm, supportive weekly mood summary in 3-4 sentences. Include what went well and a gentle suggestion."},
                {"role": "user", "content": f"Emotions this week: {', '.join(last_week)}. Average mood score: {avg_score:.2f} (scale -1 to 1)."}
            ],
            model="llama-3.1-8b-instant", temperature=0.6, max_tokens=200,
        )
        return completion.choices[0].message.content
    except Exception:
        return "Summary unavailable."


def generate_journal_prompt():
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Generate one thoughtful, open-ended journaling prompt for mental wellness. Keep it to one sentence."},
                {"role": "user", "content": "Give me a journal prompt."}
            ],
            model="llama-3.1-8b-instant", temperature=0.9, max_tokens=60,
        )
        return completion.choices[0].message.content.strip().strip('"')
    except Exception:
        return "What's one thing you learned about yourself this week?"


def analyze_journal_sentiment(text):
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Analyze the sentiment of this journal entry. Respond with just one word: Positive, Negative, or Neutral."},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant", temperature=0, max_tokens=5,
        )
        raw = completion.choices[0].message.content.strip()
        known = ["Positive", "Negative", "Neutral"]
        result = next((k for k in known if k.lower() in raw.lower()), "Neutral")
        return result, {"Positive": 1, "Negative": -1, "Neutral": 0}.get(result, 0)
    except Exception:
        return "Neutral", 0


def get_daily_affirmation():
    today_str = str(date.today())
    if st.session_state.affirmation_date == today_str and st.session_state.affirmation_of_day:
        return st.session_state.affirmation_of_day
    fallback = [
        "You are worthy of love and belonging.",
        "Every day is a new opportunity to grow.",
        "You have survived every difficult day so far.",
        "Your feelings are valid and you are not alone.",
        "Progress, not perfection, is the goal.",
        "You are stronger than you know.",
        "Taking care of yourself is an act of courage.",
        "Small steps still move you forward."
    ]
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Generate one short, powerful daily affirmation for mental wellness. One sentence only, no quotes."},
                {"role": "user", "content": "Give me today's affirmation."}
            ],
            model="llama-3.1-8b-instant", temperature=0.9, max_tokens=50,
        )
        affirmation = completion.choices[0].message.content.strip()
    except Exception:
        affirmation = random.choice(fallback)
    st.session_state.affirmation_of_day = affirmation
    st.session_state.affirmation_date = today_str
    save_user_data(st.session_state.username)
    return affirmation


def get_quotable_quote():
    try:
        r = requests.get("https://api.quotable.io/random?tags=inspirational|motivational", timeout=4)
        if r.status_code == 200:
            d = r.json()
            return d.get("content", ""), d.get("author", "")
    except Exception:
        pass
    quotes = [
        ("The darkest night is often the bridge to the brightest tomorrow.", "Anonymous"),
        ("You don't have to be positive all the time.", "Lori Deschene"),
        ("Healing is not linear.", "Anonymous"),
    ]
    q = random.choice(quotes)
    return q[0], q[1]


# ===============================
# HOME PAGE
# ===============================

if page == "🏠 Home":
    st.title(f"🌿 Welcome back, {_display_name}!")

    today_str = str(date.today())
    if not st.session_state.check_in_done_today or st.session_state.last_check_in_date != today_str:
        st.info(f"💙 **Daily Check-in** — How are you feeling today, {_display_name}?")
        c1, c2 = st.columns([3, 1])
        with c1:
            mood_today = st.select_slider(
                "Rate your current mood",
                options=["😔 Very Low", "😕 Low", "😐 Neutral", "🙂 Good", "😄 Great"],
                value="😐 Neutral"
            )
        with c2:
            if st.button("✅ Check In", type="primary"):
                score_map = {"😔 Very Low": -1, "😕 Low": -0.5, "😐 Neutral": 0, "🙂 Good": 0.5, "😄 Great": 1}
                label_map = {"😔 Very Low": "Sadness", "😕 Low": "Sadness", "😐 Neutral": "Neutral",
                             "🙂 Good": "Positive", "😄 Great": "Positive"}
                st.session_state.mood_scores.append(score_map[mood_today])
                st.session_state.mood_labels.append(label_map[mood_today])
                st.session_state.mood_dates.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.check_in_done_today = True
                st.session_state.last_check_in_date = today_str
                flush()
    else:
        st.success("✅ You've already checked in today. Great job!")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        affirmation = get_daily_affirmation()
        st.markdown(
            f'<div class="affirmation-box">✨ <strong>Today\'s Affirmation</strong><br><br>"{affirmation}"</div>',
            unsafe_allow_html=True)
    with c2:
        quote, author = get_quotable_quote()
        st.markdown(
            f'<div class="quote-box">💬 <strong>Inspiring Quote</strong><br><br>"{quote}"<br><small>— {author}</small></div>',
            unsafe_allow_html=True)

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔥 Streak", f"{st.session_state.streak} days")
    with c2:
        st.metric("💬 Chats", len([r for r, _, _ in st.session_state.chat_history if r == "user"]))
    with c3:
        st.metric("📔 Journals", len(st.session_state.journal_entries))
    with c4:
        st.metric("🙏 Gratitude Logs", len(st.session_state.gratitude_entries))


# ===============================
# CHAT PAGE
# ===============================

elif page == "💬 Chat":
    st.title("💬 AI Mental Health Companion")
    st.warning("⚠️ This is not a licensed therapist. In crisis, contact emergency services.")

    if not st.session_state.chat_history:
        st.markdown("**💡 Not sure what to say? Try one of these:**")
        prompts = [
            "I've been feeling anxious lately...",
            "I'm having trouble sleeping.",
            "I want to talk about my stress at work.",
            "I've been feeling disconnected from people.",
            "I'm struggling to find motivation.",
        ]
        cols = st.columns(len(prompts))
        for i, p in enumerate(prompts):
            with cols[i]:
                if st.button(p, key=f"prompt_{i}", use_container_width=True):
                    st.session_state["_suggested_prompt"] = p
                    st.rerun()

    c1, c2 = st.columns([6, 1])
    with c2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            flush()

    for role, message, timestamp in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)
            st.caption(f"🕐 {timestamp}")

    initial_input = None
    if "_suggested_prompt" in st.session_state:
        initial_input = st.session_state["_suggested_prompt"]
        del st.session_state["_suggested_prompt"]

    user_input = st.chat_input("How are you feeling today?") or initial_input

    if user_input:
        if safety_check(user_input):
            st.error("""
🚨 **If you're in immediate danger, please reach out:**
- 🇺🇸 Suicide & Crisis Lifeline: **988** (call or text)
- 🌍 Or contact local emergency services

You are not alone. Help is available. 💙
""")
        else:
            ts = datetime.now().strftime("%b %d, %H:%M")
            st.session_state.chat_history.append(("user", user_input, ts))

            emotion, score = detect_emotion()
            st.session_state.mood_scores.append(score)
            st.session_state.mood_labels.append(emotion)
            st.session_state.mood_dates.append(datetime.now().strftime("%Y-%m-%d %H:%M"))

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = generate_response()
                    st.write(reply)
                    st.caption(f"🕐 {ts}")

            st.session_state.chat_history.append(("assistant", reply, ts))
            flush()


# ===============================
# ANALYTICS PAGE
# ===============================

elif page == "📊 Analytics":
    st.title("📊 Emotional Analytics Dashboard")

    if not st.session_state.mood_scores:
        st.info("No mood data yet. Check in on the Home page or start chatting!")
    else:
        avg = sum(st.session_state.mood_scores) / len(st.session_state.mood_scores)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("📈 Average Mood", round(avg, 2))
        with c2:
            most_common = max(set(st.session_state.mood_labels), key=st.session_state.mood_labels.count)
            st.metric("😶 Most Common Emotion", most_common)
        with c3:
            pos_pct = int(round(100 * st.session_state.mood_labels.count("Positive") / len(st.session_state.mood_labels)))
            st.metric("😊 Positive %", f"{pos_pct}%")

        st.markdown("---")
        st.subheader("📉 Mood Trend Over Time")
        fig1, ax1 = plt.subplots(figsize=(10, 3))
        ax1.plot(st.session_state.mood_scores, marker='o', linewidth=2, color='#667eea', markersize=5)
        ax1.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax1.fill_between(range(len(st.session_state.mood_scores)), st.session_state.mood_scores, 0,
                         alpha=0.2, color='#667eea')
        ax1.set_xlabel("Sessions")
        ax1.set_ylabel("Mood Score (-1 to 1)")
        ax1.set_ylim(-1.3, 1.3)
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)
        plt.close()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🥧 Emotion Distribution")
            emotion_counts = {}
            for label in st.session_state.mood_labels:
                emotion_counts[label] = emotion_counts.get(label, 0) + 1
            colors = ['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff', '#5f27cd']
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            ax2.pie(emotion_counts.values(), labels=emotion_counts.keys(),
                    autopct='%1.1f%%', colors=colors[:len(emotion_counts)], startangle=90)
            st.pyplot(fig2)
            plt.close()

        with c2:
            st.subheader("📅 Day of Week Patterns")
            days_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_scores = {d: [] for d in days_map}
            for i, d_str in enumerate(st.session_state.mood_dates):
                if i < len(st.session_state.mood_scores):
                    try:
                        d_obj = datetime.strptime(d_str, "%Y-%m-%d %H:%M")
                        day_scores[days_map[d_obj.weekday()]].append(st.session_state.mood_scores[i])
                    except Exception:
                        pass
            avg_by_day = {d: (sum(v) / len(v) if v else None) for d, v in day_scores.items()}
            days_with_data = [(d, avg_by_day[d]) for d in days_map if avg_by_day[d] is not None]
            if days_with_data:
                ds, vs = zip(*days_with_data)
                bar_colors = ['#54a0ff' if v >= 0 else '#ff6b6b' for v in vs]
                fig3, ax3 = plt.subplots(figsize=(5, 4))
                ax3.bar(ds, vs, color=bar_colors)
                ax3.set_ylabel("Avg Mood")
                ax3.set_ylim(-1.2, 1.2)
                ax3.axhline(0, color='gray', linestyle='--', alpha=0.5)
                ax3.grid(True, alpha=0.3, axis='y')
                best = max(days_with_data, key=lambda x: x[1])
                worst = min(days_with_data, key=lambda x: x[1])
                if len(days_with_data) > 1 and best[0] != worst[0]:
                    ax3.set_title(f"Best: {best[0]} | Worst: {worst[0]}", fontsize=10)
                elif len(days_with_data) == 1:
                    ax3.set_title(f"Only data for {best[0]} so far", fontsize=10)
                st.pyplot(fig3)
                plt.close()
            else:
                st.info("Not enough data yet for day-of-week patterns.")

        st.markdown("---")
        st.subheader("📋 Weekly Mood Summary Report")
        if st.button("🤖 Generate AI Summary"):
            with st.spinner("Generating your personalized summary..."):
                _summary = generate_weekly_summary()
            st.info(_summary)

        st.subheader("💡 AI Mood Insight")
        if st.button("🤖 Generate Mood Insight"):
            with st.spinner("Generating insight..."):
                _insight = generate_mood_insight()
            st.info(_insight)

        st.markdown("---")
        st.subheader("📄 Export Analytics")
        if st.button("📥 Prepare Mood Report"):
            lines = [
                f"Mental Wellness Report — {_display_name} ({_google_email})",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "=" * 40,
                f"Total Check-ins: {len(st.session_state.mood_scores)}",
                f"Average Mood Score: {round(avg, 2)}",
                f"Streak: {st.session_state.streak} days",
                "",
                "Mood History:",
            ]
            for i, (label, score) in enumerate(zip(st.session_state.mood_labels, st.session_state.mood_scores)):
                lines.append(f"  {i+1}. {label} ({score:+.1f})")
            st.session_state["_report_text"] = "\n".join(lines)
        if "_report_text" in st.session_state:
            st.download_button("💾 Download Report", st.session_state["_report_text"],
                               file_name=f"wellness_report_{date.today()}.txt", mime="text/plain")


# ===============================
# JOURNAL PAGE
# ===============================

elif page == "📔 Journal":
    st.title("📔 Daily Journal")
    today_str = str(date.today())

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"✍️ **Writing Streak:** {st.session_state.writing_streak} days")
    with c2:
        if st.button("💡 Get a Prompt"):
            with st.spinner("Thinking..."):
                st.session_state["_journal_prompt"] = generate_journal_prompt()

    if "_journal_prompt" in st.session_state:
        st.info(f"✨ **Prompt:** {st.session_state['_journal_prompt']}")

    journal_text = st.text_area("Write your thoughts here...", height=200,
                                placeholder="Start writing freely — this is your safe space...")
    word_count = len(journal_text.split()) if journal_text.strip() else 0
    st.caption(f"📝 {word_count} words")

    if st.button("💾 Save Entry", type="primary"):
        if journal_text.strip():
            sentiment, s_score = analyze_journal_sentiment(journal_text)
            dt = datetime.now()
            st.session_state.journal_entries.append({
                "date": dt.strftime("%Y-%m-%d %H:%M"),
                "text": journal_text,
                "sentiment": sentiment,
                "word_count": word_count
            })
            st.session_state.mood_scores.append(s_score)
            st.session_state.mood_labels.append(sentiment if sentiment in ["Positive", "Negative"] else "Neutral")
            st.session_state.mood_dates.append(dt.strftime("%Y-%m-%d %H:%M"))

            # Writing streak — only increment once per day
            if st.session_state.last_journal_date != today_str:
                last_j = st.session_state.last_journal_date
                if last_j:
                    try:
                        if date.fromisoformat(last_j) == date.today() - timedelta(days=1):
                            st.session_state.writing_streak += 1
                        else:
                            st.session_state.writing_streak = 1
                    except ValueError:
                        st.session_state.writing_streak = 1
                else:
                    st.session_state.writing_streak = 1
                st.session_state.last_journal_date = today_str

            if "_journal_prompt" in st.session_state:
                del st.session_state["_journal_prompt"]

            st.success(f"✅ Entry saved! Sentiment: **{sentiment}** | Words: **{word_count}**")
            flush()
        else:
            st.warning("Please write something before saving.")

    st.markdown("---")
    if st.session_state.journal_entries:
        st.subheader("📚 Your Entries")
        search_q = st.text_input("🔍 Search entries...", placeholder="Search by keyword...")
        filter_sentiment = st.selectbox("Filter by sentiment", ["All", "Positive", "Negative", "Neutral"])

        filtered = st.session_state.journal_entries
        if search_q.strip():
            filtered = [e for e in filtered if search_q.lower() in e["text"].lower()]
        if filter_sentiment != "All":
            filtered = [e for e in filtered if e.get("sentiment") == filter_sentiment]

        st.caption(f"Showing {len(filtered)} of {len(st.session_state.journal_entries)} entries")
        emoji_map = {"Positive": "😊", "Negative": "😔", "Neutral": "😐"}
        for entry in reversed(filtered):
            with st.expander(
                    f"📅 {entry['date']} — {emoji_map.get(entry.get('sentiment', ''), '📝')} {entry.get('sentiment', '')}"):
                st.write(entry["text"])
                st.caption(f"Words: {entry.get('word_count', '—')}")

        full_text = "\n\n".join(
            [f"[{e['date']}] ({e.get('sentiment', '')})\n{e['text']}" for e in st.session_state.journal_entries])
        st.download_button("📥 Download All Entries", full_text, file_name="journal.txt")


# ===============================
# GRATITUDE PAGE
# ===============================

elif page == "🙏 Gratitude":
    st.title("🙏 Gratitude Log")
    st.markdown("*Research shows that noting 3 things you're grateful for daily boosts well-being.*")

    today_str = str(date.today())
    already_today = any(e["date"] == today_str for e in st.session_state.gratitude_entries)

    if already_today:
        st.success("✅ You've already logged your gratitude today. Come back tomorrow!")
        today_entry = next(e for e in reversed(st.session_state.gratitude_entries) if e["date"] == today_str)
        st.markdown("**Today you were grateful for:**")
        for i, item in enumerate(today_entry["items"], 1):
            if item.strip():
                st.markdown(f"{i}. 🌟 {item}")
    else:
        st.markdown("### What are 3 things you're grateful for today?")
        g1 = st.text_input("1️⃣", placeholder="e.g. A good cup of coffee this morning")
        g2 = st.text_input("2️⃣", placeholder="e.g. A friend who checked on me")
        g3 = st.text_input("3️⃣", placeholder="e.g. A moment of peace today")

        if st.button("🙏 Save Gratitude", type="primary"):
            items = [g1, g2, g3]
            if any(i.strip() for i in items):
                st.session_state.gratitude_entries.append({"date": today_str, "items": items})
                st.success("🌟 Gratitude logged! Every bit of appreciation counts.")
                flush()
            else:
                st.warning("Please add at least one thing you're grateful for.")

    if st.session_state.gratitude_entries:
        st.markdown("---")
        st.subheader("📚 Your Gratitude History")
        for entry in reversed(st.session_state.gratitude_entries[-10:]):
            with st.expander(f"📅 {entry['date']}"):
                for i, item in enumerate(entry["items"], 1):
                    if item.strip():
                        st.write(f"{i}. {item}")


# ===============================
# WELLNESS TOOLS PAGE
# ===============================

elif page == "🧘 Wellness Tools":
    st.title("🧘 Wellness Tools")

    tool = st.radio("Choose a tool:", [
        "🫁 Guided Breathing",
        "🌍 Grounding Technique (5-4-3-2-1)",
        "📦 Box Breathing",
        "✨ Daily Affirmation"
    ], horizontal=True)

    st.markdown("---")

    if tool == "🫁 Guided Breathing":
        st.subheader("🫁 Guided Breathing Exercise")
        st.markdown("*This simple breathing exercise can help reduce anxiety and stress in just a few minutes.*")
        c1, c2 = st.columns([1, 2])
        with c1:
            inhale_t = st.slider("Inhale (seconds)", 2, 8, 4)
            hold_t = st.slider("Hold (seconds)", 0, 8, 4)
            exhale_t = st.slider("Exhale (seconds)", 2, 10, 6)
            cycles = st.slider("Cycles", 1, 10, 4)
        with c2:
            if st.button("▶️ Start Breathing Exercise", type="primary"):
                phase_ph = st.empty()
                prog_ph = st.empty()
                status_ph = st.empty()
                for cycle in range(cycles):
                    status_ph.markdown(f"**Cycle {cycle + 1} of {cycles}**")
                    for i in range(inhale_t):
                        phase_ph.markdown(f"### 🌬️ Inhale... ({inhale_t - i}s)")
                        prog_ph.progress((i + 1) / inhale_t)
                        time.sleep(1)
                    if hold_t > 0:
                        for i in range(hold_t):
                            phase_ph.markdown(f"### ⏸️ Hold... ({hold_t - i}s)")
                            prog_ph.progress((i + 1) / hold_t)
                            time.sleep(1)
                    for i in range(exhale_t):
                        phase_ph.markdown(f"### 💨 Exhale... ({exhale_t - i}s)")
                        prog_ph.progress((i + 1) / exhale_t)
                        time.sleep(1)
                phase_ph.markdown("### ✅ Great job! Exercise complete.")
                prog_ph.empty()
                status_ph.markdown("*Notice how your body feels right now. 💙*")

    elif tool == "🌍 Grounding Technique (5-4-3-2-1)":
        st.subheader("🌍 5-4-3-2-1 Grounding Technique")
        st.markdown("*Anchors you to the present moment when feeling overwhelmed.*\n\nTake a slow breath, then notice:")
        steps = [
            ("5", "👁️", "THINGS YOU CAN SEE", "Look around and name 5 things you can see right now.",
             ["A clock on the wall", "Trees outside", "Your hands", "A cup", "The ceiling"]),
            ("4", "🤚", "THINGS YOU CAN TOUCH", "Notice 4 things you can physically feel.",
             ["The chair beneath you", "Your feet on the floor", "The texture of your clothes", "Air on your skin"]),
            ("3", "👂", "THINGS YOU CAN HEAR", "Listen carefully for 3 sounds.",
             ["Your own breathing", "Background noise", "A distant sound"]),
            ("2", "👃", "THINGS YOU CAN SMELL", "Find 2 scents around you.", ["Fresh air", "Something nearby"]),
            ("1", "👅", "THING YOU CAN TASTE", "Notice 1 taste in your mouth.",
             ["The current taste in your mouth"]),
        ]
        for num, emoji, title, instruction, examples in steps:
            st.markdown(
                f'<div class="grounding-card"><strong>{emoji} {num} {title}</strong><br>{instruction}<br>'
                f'<small>Examples: {", ".join(examples)}</small></div>',
                unsafe_allow_html=True)
        st.markdown("---")
        st.success("🌟 Well done. You are here. You are safe. Take one more deep breath. 💙")

    elif tool == "📦 Box Breathing":
        st.subheader("📦 Box Breathing (4-4-4-4)")
        st.markdown("*Quickly calms the nervous system. Each phase is **4 seconds**.*")
        if st.button("▶️ Start Box Breathing", type="primary"):
            phase_ph = st.empty()
            prog_ph = st.empty()
            for cycle in range(4):
                for phase, icon in [("Inhale", "⬆️"), ("Hold", "➡️"), ("Exhale", "⬇️"), ("Hold", "⬅️")]:
                    for i in range(4):
                        phase_ph.markdown(f"### {icon} {phase}... ({4 - i}s) — Cycle {cycle + 1}/4")
                        prog_ph.progress((i + 1) / 4)
                        time.sleep(1)
            phase_ph.markdown("### ✅ Box Breathing Complete!")
            prog_ph.empty()
            st.balloons()

    elif tool == "✨ Daily Affirmation":
        st.subheader("✨ Daily Affirmation")
        affirmation = get_daily_affirmation()
        st.markdown(
            f'<div class="affirmation-box"><br>✨<br><br>'
            f'<strong style="font-size:1.3em;">"{affirmation}"</strong><br><br></div>',
            unsafe_allow_html=True)
        st.markdown("*Repeat this to yourself 3 times. Let it sink in. You deserve to believe it.*")
        if st.button("🔄 Generate a New Affirmation"):
            st.session_state.affirmation_of_day = None
            st.rerun()
        st.markdown("---")
        st.markdown("### 💭 Affirmation Journal")
        reflection = st.text_area("How does this affirmation resonate with you today?", height=100)
        if st.button("Save Reflection") and reflection.strip():
            st.session_state.journal_entries.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "text": f"[Affirmation: {affirmation}]\n\nReflection: {reflection}",
                "sentiment": "Positive",
                "word_count": len(reflection.split())
            })
            flush()
            st.success("Reflection saved to your journal! 🌟")


# ===============================
# ABOUT PAGE
# ===============================

elif page == "ℹ About":
    st.title("ℹ️ About This Project")
    st.markdown("""
    ### 🧠 AI Mental Wellness Companion

    This app integrates **Llama 3.1** via **Groq's free API** to provide empathetic, context-aware mental health support.
    All your data is saved on the server under your name and restored automatically each time you log in.

    **Features:**
    - 🏠 **Home** — Daily check-in, affirmations, quotes, stats
    - 💬 **Chat** — Context-aware AI chat with emotion detection
    - 📊 **Analytics** — Mood trend, emotion pie, day-of-week patterns, AI summaries
    - 📔 **Journal** — AI prompts, sentiment analysis, search & filter, writing streak
    - 🙏 **Gratitude** — Daily 3-item gratitude log
    - 🧘 **Wellness Tools** — Guided breathing, 5-4-3-2-1 grounding, box breathing, affirmations

    **APIs & Libraries:**
    - [Groq](https://groq.com) — LLM inference (Llama 3.1)
    - [Quotable API](https://api.quotable.io) — Inspirational quotes
    - [Streamlit](https://streamlit.io) — App framework
    - [Matplotlib](https://matplotlib.org) — Charts

    ---
    > ⚠️ **Disclaimer:** This system is for supportive guidance only. It does **not** replace professional mental health care.
    > If you are in crisis, please contact your local emergency services.
    """)

# ===============================
# BROWSER NOTIFICATION (JS)
# ===============================

st.markdown("""
<script>
if ("Notification" in window && Notification.permission === "default") {
    setTimeout(() => {
        Notification.requestPermission().then(perm => {
            if (perm === "granted") {
                new Notification("🧠 Mental Wellness Reminder", {
                    body: "Don't forget to check in with yourself today! 💙",
                    icon: "🧠"
                });
            }
        });
    }, 3000);
}
</script>
""", unsafe_allow_html=True)

