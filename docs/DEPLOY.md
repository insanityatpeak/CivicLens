# Deployment

**Status: DEPLOYED on Render (free tier) at https://civiclens-prns.onrender.com/ , verified 2026-11-05 with a real-provider run (Groq answered).** The app is a plain ASGI service (FastAPI + static files), so any host that runs
Python 3.12 and a start command can run it. Verified only on a local Windows machine.

## Before you deploy
1. Free tiers are rate-limited and a public app with shared keys can be exhausted (the Gemini free quota already ran out once during development, HTTP 429); that is why a second provider is chained as a fallback.

## Run command
```
pip install -r requirements.txt
uvicorn civiclens.web.server:app --app-dir src --host 0.0.0.0 --port $PORT
```
Environment variables (set as host secrets, never commit): `GROQ_API_KEY` (primary), `OPENROUTER_API_KEY` (first fallback), `GEMINI_API_KEY` (second fallback, optional), optional `GROQ_MODEL`, `OPENROUTER_MODEL`, `GEMINI_MODEL`, `CIVICLENS_PROVIDER` (default `groq,openrouter,gemini`; providers without a key are skipped). On Render, add `GEMINI_API_KEY` under Environment and set `CIVICLENS_PROVIDER` to `groq,openrouter,gemini` (an existing service keeps its old value until you change it). Model ids in `.env.example` are UNVERIFIED defaults: confirm each is vision-capable in the provider's catalogue.
Python 3.12 recommended. The two CC0 example photos in `data/samples/` (`pothole.jpg`, `garbage.jpg`) are exempted from the ignore rule so they ship with the repo; the three user-supplied images stay local.

## One-click files
- `render.yaml`: Render Blueprint (New > Blueprint, pick the repo; Render asks for `GROQ_API_KEY` and `OPENROUTER_API_KEY`). Free instances sleep when idle, so the first request can take about a minute.
- `Dockerfile`: for Hugging Face Spaces (Docker SDK, default port 7860), Fly.io, Railway. Set the two keys as secrets on the host.
Both are UNTESTED: Docker was not available locally and nothing has been deployed.

## After deploying
Open the URL, run an example photo, and confirm there is **no** red "DEMONSTRATION FALLBACK" banner. If the key is missing the app says so and offers the labeled fallback. Put the live URL in the README only after you have loaded it.

## Free-tier limits you will hit
- Groq (qwen/qwen3.8-27b): 1,000 output tokens per minute. A few simultaneous users will be throttled (HTTP 429) and fall through to OpenRouter.
- OpenRouter free models: 50 requests per day in total (1,000 with $10 credit). When it is used up there is no fallback and users see a "busy" message.

## Mitigations in the app
10 MB upload cap; soft cap of 10 real-model analyses per browser session (in-memory, resets on server restart, per-cookie so it is easy to evade: NOT a rate limit); visible fallback banner; provider errors shown in plain language, details only in server logs.
Not built: global rate limiting, bring-your-own-key, persistent storage (nothing is stored by design).
