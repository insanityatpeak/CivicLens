# Contributing

## Setup
```
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.lock -r requirements-dev.txt
cp .env.example .env                           # optional; the mock provider needs no keys
```

## Checks (CI runs the same)
```
ruff check .
mypy
pytest -q --cov        # fails under 90% coverage
pip-audit -r requirements.lock
```

## Dependencies
Edit `requirements.txt`, then regenerate the lockfile:
`pip-compile --strip-extras -o requirements.lock requirements.txt`

## Ground rules
- The validator (`safety.py`) and provider fallback (`providers/chain.py`) are the trust core: every change needs a test.
- Never log or store photos or user-typed text.
- Contact details, departments and links must come from curated data files, never from model output.
