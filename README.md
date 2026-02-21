# 🧠 AI Mental Wellness Companion

A Streamlit-based mental wellness web app powered by **Llama 3.1** via **Groq's API**. It provides empathetic AI chat support, mood tracking, journaling, gratitude logging, and guided wellness exercises — all in one place.

> ⚠️ **Disclaimer:** This app is for supportive guidance only and is **not** a replacement for licensed mental health care. If you are in crisis, please contact your local emergency services or a mental health professional.

---

## ✨ Features

- **🏠 Home** — Daily mood check-in, AI-generated affirmations, inspirational quotes, and stats overview (streak, chats, journals, gratitude logs)
- **💬 AI Chat** — Context-aware, empathetic conversation powered by Llama 3.1; includes crisis detection and suggested starter prompts
- **📊 Analytics** — Mood trend chart, emotion distribution pie chart, day-of-week mood patterns, AI-generated weekly summary and mood insight, and downloadable text report
- **📔 Journal** — AI-generated journaling prompts, sentiment analysis on entries, writing streak tracker, search & filter, and download
- **🙏 Gratitude Log** — Daily 3-item gratitude logger with history view
- **🧘 Wellness Tools** — Guided breathing (customizable), 5-4-3-2-1 grounding technique, box breathing, and daily affirmation with reflection journal

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web app framework |
| [Groq](https://groq.com) | LLM inference (Llama 3.1 8B Instant) |
| [Matplotlib](https://matplotlib.org) | Mood analytics charts |
| [Quotable API](https://api.quotable.io) | Inspirational quotes |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-mental-wellness-companion.git
cd ai-mental-wellness-companion
```

### 2. Install Dependencies

```bash
pip install streamlit groq matplotlib requests
```

### 3. Set Up Your Groq API Key

Create a `.streamlit/secrets.toml` file in the project root:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

You can get a free API key at [console.groq.com](https://console.groq.com).

### 4. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
ai-mental-wellness-companion/
│
├── app.py                  # Main application file
├── .streamlit/
│   └── secrets.toml        # API keys (do not commit this file)
└── README.md
```

---

## 🔒 Privacy & Data

All data (mood scores, journal entries, chat history, gratitude logs) is stored in **Streamlit's session state** and exists only for the duration of your browser session. No data is persisted to a database or sent anywhere other than the Groq API for AI responses.

---

## 🚨 Crisis Detection

The chat feature includes basic keyword detection for crisis-related language. If triggered, the app displays emergency resource information and encourages the user to seek professional help. This is **not** a substitute for professional crisis intervention.

---

## 🙌 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
