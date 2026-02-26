🧠 Overview

This guide walks you through setting up Google OAuth 2.0 credentials for the Mental Wellness Companion web app. The app uses Google login for authentication via Streamlit’s OAuth support, so you’ll need to configure a project in the Google Cloud Console and obtain a Client ID and Client Secret.

You’ll store these credentials in a secrets.toml file used by Streamlit at runtime.

📌 1. Create a Google Cloud Project

Go to the Google Cloud Console:
https://console.cloud.google.com

If prompted, sign in with your Google account.

Click Select a project > New Project.

Give it a name (e.g., mental-wellness-app-auth) and click Create.

🔐 2. Enable the OAuth Consent Screen

Before creating credentials, you must configure the consent screen:

In the sidebar, navigate to APIs & Services > OAuth consent screen.

Choose External and click Create.

Fill in the required fields:

App name

User support email

Developer contact email

Scroll to the bottom and click Save and Continue.

You don’t need to configure scopes now (basic profile + email are added by default).

🔑 3. Create OAuth Credentials

Go to APIs & Services > Credentials.

Click Create Credentials > OAuth client ID.

Choose Web application.

Set a name:
Name: Streamlit OAuth Client

Add Authorized redirect URIs:

For local testing:

http://localhost:8501/oauth2callback

If deploying (e.g., Streamlit Cloud), add your deployed app URL + /oauth2callback

Example:

https://<your-deployment>.streamlit.app/oauth2callback

Click Create.

You’ll now see your Client ID and Client Secret.

📝 4. Prepare Streamlit Secrets File

You’ll need to create a file named:

.streamlit/secrets.toml

Inside it, add:

GROQ_API_KEY = "gsk_your_groq_key_here"

[auth]
redirect_uri        = "http://localhost:8501/oauth2callback"
cookie_secret       = "your_64_char_hex_string"
client_id           = "your_client_id.apps.googleusercontent.com"
client_secret       = "your_google_client_secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
🔐 Notes:

Replace your_client_id and your_google_client_secret with values from Google Cloud.

Use a strong random string (at least 64 characters) for cookie_secret. This ensures secure session cookies.

If deploying, update redirect_uri to match your deployed URL.

🚀 5. Run the App

With the secrets file configured:

streamlit run app.py

When the app opens in your browser:

Click “Sign in with Google”

Complete the OAuth prompt

You’ll be authenticated and redirected back into the app

🧪 6. Deploying to Streamlit Cloud

Push your code to GitHub.

Go to https://share.streamlit.io
 and connect your repo.

In Secrets settings, paste the secrets.toml content (but do not commit it).

Make sure your redirect URI in Google Cloud includes your deployed domain.

⚠️ Troubleshooting
❌ Unauthorized Redirect URI

If you see this, ensure the URI in Google Cloud exactly matches what your app uses (including protocol and trailing slash).

❌ Invalid Client Secret

Re-check that you copied the Client Secret correctly from Google Cloud.

🛡️ Security Tips

Never commit your secrets to GitHub.

Always use environment secrets on deployment platforms.

Use HTTPS in production.
