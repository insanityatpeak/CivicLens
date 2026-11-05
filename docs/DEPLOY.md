# Deployment

**Status: NOT DEPLOYED, and not tested on any host.** The app is a plain ASGI service (FastAPI + static files), so any host that runs
Python 3.12 and a start command can run it. Verified only on a local Windows machine.

## Before you deploy
1. Free tiers are rate-limited and a public app with shared keys can be exhausted (the Gemini free quota already ran out once during development, HTTP 429); that is why a second provider is chained as a fallback.

## Run command
```
pip install -r requirements.txt
uvicorn civiclens.web.server:app --app-dir src --host 0.0.0.0 --port $PORT
```
Environment variables (set as host secrets, never commit): `GROQ_API_KEY` (primary), `OPENROUTER_API_KEY` (fallback), optional `GROQ_MODEL`, `OPENROUTER_MODEL`, `CIVICLENS_PROVIDER` (default `groq,openrouter`). Model ids in `.env.example` are UNVERIFIED defaults: confirm each is vision-capable in the provider's catalogue.
Python 3.12 recommended. The two CC0 example photos in `data/samples/` (`pothole.jpg`, `garbage.jpg`) are exempted from the ignore rule so they ship with the repo; the three user-supplied images stay local.

## After deploying
Open the URL, run an example photo, and confirm there is **no** red "DEMONSTRATION FALLBACK" banner. If the key is missing the app says so and offers the labeled fallback. Put the live URL in the README only after you have loaded it.

## Mitigations in the app
10 MB upload cap; soft cap of 10 real-model analyses per browser session (in-memory, resets on server restart, per-cookie so it is easy to evade: NOT a rate limit); visible fallback banner; provider errors shown in plain language, details only in server logs.
Not built: global rate limiting, bring-your-own-key, persistent storage (nothing is stored by design).
