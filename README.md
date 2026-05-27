# Docify

A Flask-based medical consultation app with authentication, consultation forms, a FAQ page, and a unified chatbot module that degrades gracefully without AI dependencies.

## Features

- Login/register with SQLite
- Dashboard CRUD for consultations
- FAQ page and chatbot endpoint
- Hybrid FAQ-first chatbot (keyword + embeddings)
- Security hardening: IP allowlist, CSRF, rate limiting
- Health check endpoint at `/health`

## Requirements

- Python 3.11+
- Linux, macOS, or Windows

## Quick start (minimal, no AI)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements-minimal.txt
python app.py
```

- App: http://127.0.0.1:5000
- Health: http://127.0.0.1:5000/health

## Full setup (AI-enabled)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements-minimal.txt -r requirements-ai.txt
python app.py
```

## Running tests

```bash
python -m pip install -r requirements-minimal.txt -r requirements-dev.txt
python testsprite.py
pytest -q
```

## Endpoints

- `GET /` — Home page
- `GET /login` — Login form
- `GET /register` — Registration form
- `GET, POST /dashboard` — Submit/view consultations
- `GET, POST /update_consultation/<id>` — Edit consultation
- `POST /delete_consultation/<id>` — Delete consultation (JSON)
- `GET, POST /profile` — Profile update
- `GET /faq` — FAQ page
- `POST /chatbot` — Chatbot API (JSON)
- `GET /health` — Health probe (JSON)

Chatbot request example:

```json
{
  "message": "What is Docify Online?",
  "symptoms": "Fever and headache for 2 days"
}
```

Chatbot response example:

```json
{
  "reply": "Docify Online is a platform for filling out medical certificates and consultation forms, with support from our chatbot."
}
```

## Project structure

```
app/                 # Flask app package (factory, routes, middleware)
chatbot/             # Unified chatbot module (FAQ-first + hybrid retrieval)
docs/                # Architecture, deployment, troubleshooting
instance/            # SQLite DB location (runtime)
templates/           # Jinja templates
app.py               # App entrypoint (create_app)
faq.txt              # FAQ content for chatbot
requirements-*.txt   # Dependency sets
```

## Environment variables

- `SECRET_KEY` (required)
- `ALLOWED_IPS` (default `127.0.0.1/32`)
- `DISABLE_IP_FILTER` (`true` to bypass allowlist)
- `SQLITE_PATH` (optional override)
- `DATABASE_URL` / `SQLALCHEMY_DATABASE_URI`
- `FAQ_FILE_PATH`, `EMBEDDING_MODEL`, `CHATBOT_TOP_K`
- `SESSION_COOKIE_SECURE` (`true` for HTTPS)

Example `.env`:

```
SECRET_KEY=change-me
ALLOWED_IPS=127.0.0.1/32
```

## Docker

Minimal image:

```bash
docker build -t docify:mini --build-arg INSTALL_FULL=false .
docker run --rm -p 5000:5000 -e SECRET_KEY=change-me -e ALLOWED_IPS="0.0.0.0/0" docify:mini
```

Full AI image:

```bash
docker build -t docify:full --build-arg INSTALL_FULL=true .
docker run --rm -p 5000:5000 -e SECRET_KEY=change-me -e ALLOWED_IPS="0.0.0.0/0" docify:full
```

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- `docs/TROUBLESHOOTING.md`

## Notes

- The app works without AI dependencies. Chatbot falls back to FAQ and rule-based responses.
- Data files generated at runtime: `users.csv`, `query_dataset.csv`, `instance/docify.db`.
