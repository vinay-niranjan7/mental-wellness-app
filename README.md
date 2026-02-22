# 🧠 AI Mental Wellness Companion

A personal mental health support web app powered by **Llama 3.1** via **Groq**, built with **Streamlit**. It provides empathetic AI chat, mood tracking, journaling, gratitude logging, and guided wellness exercises — all in one place.

> ⚠️ **Disclaimer:** This app is for supportive guidance only. It is **not** a replacement for licensed mental health care. If you are in crisis, please contact your local emergency services or call **988** (Suicide & Crisis Lifeline).

---

## 🌐 Live Demo

[https://mental-wellness-app-3pggsbgy6xx2ivuozvaiuw.streamlit.app](https://mental-wellness-app-3pggsbgy6xx2ivuozvaiuw.streamlit.app)

---

## ✨ Features

### 🏠 Home
- Daily mood check-in with a simple slider
- Streak tracker to reward consistent check-ins
- AI-generated daily affirmation (refreshes every day)
- Inspirational quote from the Quotable API
- Live stats: chats, journal entries, gratitude logs

### 💬 AI Chat
- Context-aware, empathetic AI responses (Llama 3.1 via Groq)
- Restricted strictly to **mental health topics** — won't answer off-topic questions
- Crisis detection: detects self-harm keywords and shows emergency resources
- Suggested conversation starters for when you're not sure what to say
- Full chat history saved per user

### 📊 Emotion Analytics
- Mood trend line chart over all sessions
- Emotion distribution pie chart (Anxiety, Sadness, Anger, Burnout, Positive, Neutral)
- Day-of-week mood pattern bar chart
- AI-generated weekly mood summary report
- AI mood insight based on recent history
- Downloadable plain-text wellness report

### 📔 Journal
- Free-form journaling with AI-generated prompts
- Automatic sentiment analysis on each entry (Positive / Negative / Neutral)
- Writing streak tracker
- Search and filter past entries by keyword or sentiment
- Download all entries as a `.txt` file

### 🙏 Gratitude Log
- Daily 3-item gratitude log
- Prevents duplicate entries on the same day
- Full gratitude history with date-organized entries

### 🧘 Wellness Tools
- **Guided Breathing** — customizable inhale / hold / exhale cycles with real-time progress
- **Box Breathing (4-4-4-4)** — animated Navy SEAL technique
- **5-4-3-2-1 Grounding** — step-by-step anxiety grounding exercise
- **Daily Affirmation** — with an affirmation reflection journal

---

## 🔐 Authentication

Login is handled via **Google OAuth** using Streamlit's built-in `st.login()`. No passwords stored anywhere.

- Sign in with your Google account
- Session persists across browser refreshes via secure cookie
- Each user's data is stored separately using their Google email as the unique key
- Log out anytime from the sidebar

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) |
| AI / LLM | [Llama 3.1 8B](https://groq.com) via Groq API |
| Auth | Google OAuth via `st.login()` + Authlib |
| Charts | Matplotlib |
| Quotes | [Quotable API](https://api.quotable.io) |
| Storage | JSON files per user (server filesystem) |

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/mental-wellness-app.git
cd mental-wellness-app
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure secrets
Create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_groq_key_here"

[auth]
redirect_uri        = "http://localhost:8501/oauth2callback"
cookie_secret       = "your_64_char_hex_string"
client_id           = "your_client_id.apps.googleusercontent.com"
client_secret       = "your_google_client_secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

See **[GOOGLE_AUTH_SETUP.md](GOOGLE_AUTH_SETUP.md)** for step-by-step instructions on getting Google OAuth credentials.

### 4. Run the app
```bash
streamlit run app.py
```

---

## 📦 Requirements

```
streamlit>=1.35.0
groq
matplotlib
requests
Authlib>=1.3.2
```

---

## ☁️ Deploying to Streamlit Cloud

1. Push your code to a **public or private GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → connect your repo
3. Set **Main file path** to `app.py`
4. Go to **Settings → Secrets** and paste your secrets (use the Cloud redirect URI, not localhost)
5. Click **Deploy**

> Make sure `.streamlit/secrets.toml` is listed in `.gitignore` — never commit it.

---

## 📁 Project Structure

```
mental-wellness-app/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── .gitignore                # Excludes secrets and user data
├── README.md                 # This file
├── GOOGLE_AUTH_SETUP.md      # Step-by-step OAuth setup guide
├── secrets.toml.template     # Secrets template (safe to commit)
└── user_data/                # Auto-created at runtime, gitignored
    └── useremailcom.json     # Per-user data (mood, journal, chat)
```

---

## 🔒 Privacy & Data

- User data is stored as **JSON files on the server**, named by a sanitized version of the user's email
- Data includes: mood scores, chat history, journal entries, gratitude logs
- No data is shared with third parties
- The Groq API receives chat messages for AI processing — see [Groq's privacy policy](https://groq.com/privacy-policy/)
- **For production use**, consider migrating `user_data/` to a proper database (Supabase, Firebase, etc.)

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
