# Deployment (Streamlit Community Cloud)

**Status: NOT DEPLOYED.** Config is prepared; deploying needs your accounts.

## Before you deploy
1. In Google AI Studio, set a quota or budget alert on the API key. A public app with a shared key can be exhausted.

## Steps
1. Push the repo to GitHub (you do this; nothing here pushes for you):
   ```
   git remote add origin https://github.com/<you>/<repo>.git
   git branch -M main
   git push -u origin main
   ```
2. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**, choose the repo, branch `main`, main file `app.py`.
3. Open **Advanced settings**: pick Python 3.12, and paste into **Secrets**:
   ```
   GEMINI_API_KEY = "your-key-here"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```
   Streamlit exposes top-level secrets as environment variables, which is what `config.py` reads.
4. Deploy, open the URL, run a real photo through it, and confirm there is **no** red "DEMONSTRATION FALLBACK" banner (if the key is missing the app shows an error and offers the labeled fallback).
5. Put the live URL into the README and checklist only after you have loaded it.

## Existing config
`.streamlit/config.toml` (theme, 10 MB upload limit, usage stats off). `requirements.txt` has runtime dependencies only.

## Mitigations in the app
10 MB upload cap; soft cap of 10 real-model analyses per browser session; visible fallback banner. Not built: bring-your-own-key, global rate limiting.
