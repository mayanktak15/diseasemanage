# Docify (Bernin)

A Flask-based web app for simple medical consultation workflows with login/registration, a dashboard to submit/update consultation forms, a FAQ page, and a chatbot endpoint with graceful fallbacks (no ML dependencies required to get started).

## Features

- User register/login (SQLite)
- Dashboard: submit and update consultation forms
- FAQ page
- Chatbot endpoint with multiple backends; defaults to a safe, no-ML fallback
- IP allowlist for incoming requests (secure by default)
- Health check endpoint at `/health`

## Endpoints

- `GET /` — Home page
- `GET /login` — Login form
- `GET /register` — Registration form
- `GET, POST /dashboard` — Submit consultation (POST), view your consultations (GET)
- `GET, POST /update_consultation/<id>` — Edit an existing consultation you own
- `POST /delete_consultation/<id>` — Delete a consultation you own (returns JSON)
- `GET, POST /profile` — View/update profile details
- `GET /faq` — FAQ page
- `POST /chatbot` — Chatbot API (JSON)
- `GET /health` — Health probe (JSON: {"status":"ok"})

Chatbot API example (JSON):

Request body:
```json
{
	"message": "What is Docify Online?",
	"symptoms": "Fever and headache for 2 days"
}
```

Response body (example):
```json
{
	"reply": "Docify Online is a platform for filling out medical certificates and consultation forms, with support from our chatbot."
}
```

## Requirements

- Windows (tested) or any OS with Python 3.10+
- Python 3.10+ recommended

## Quick start (no ML/AI dependencies)

This path runs the app using the simple chatbot fallback. It’s fastest to set up and works on any machine.

1) Open a terminal in the project folder

2) Create and activate a virtual environment

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

3) Install minimal packages

```powershell
python -m pip install -U pip
python -m pip install Flask==3.0.3 Flask-SQLAlchemy requests
```

4) Run the app

```powershell
python app.py
```

- App starts on http://127.0.0.1:5000
- Health: http://127.0.0.1:5000/health
- Default IP allowlist only permits 127.0.0.1; see “IP allowlist” below if you need external access.

5) Run tests (optional)

```powershell
python testsprite.py
```

All tests should pass without ML/AI libraries installed.

## Tests

Single consolidated test file using Flask’s test client:

```powershell
python testsprite.py
```

Notes:
- Tests don’t require ML dependencies; the app falls back to simple FAQ responses.

## Full setup (ML/AI features)

To enable RAG and model-backed chat variants you can install the full dependency set:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

Some optional chatbot services (run in separate terminals):

- `chatbot.py` (port 5001): FAISS + Flan-T5 small via Transformers/HF Pipeline
- `chatbot2.py` (port 5002): FAISS + LoRA fine-tuned Flan-T5 (requires model files at `fine_tuning/lora_flan_t5_small/finetuned`)
- `chatbot3usingllama2formollama.py` (port 5003): FAISS + Ollama model `docify` on localhost:11434

To proxy the web app to a chatbot microservice (on 5003), run `app2.py` instead of `app.py`:

```powershell
python app2.py
```

Notes:
- These ML options are heavier and may require GPU/large downloads.
- The main `app.py` does not require them to function; it falls back safely.

## Docker

Build a minimal, fast image (no ML dependencies; the app falls back to simple FAQ):

```powershell
docker build -t docify:mini --build-arg INSTALL_FULL=false .
docker run --rm -p 5000:5000 -e SECRET_KEY=change-me -e ALLOWED_IPS="0.0.0.0/0" docify:mini
```

Build with full ML stack (heavier image due to transformers/torch/langchain):

```powershell
docker build -t docify:full --build-arg INSTALL_FULL=true .
docker run --rm -p 5000:5000 -e SECRET_KEY=change-me -e ALLOWED_IPS="0.0.0.0/0" docify:full
```

Details:
- The image serves via Gunicorn on port 5000 and includes a healthcheck at `/health`.
- SQLite database is created inside the container at `/app/instance/docify.db`.
- Adjust `ALLOWED_IPS` as needed; the Docker default is permissive.

### Compose (optional)

If you want persistence across container restarts, mount a volume for the instance folder. Example `docker-compose.yml` sketch:

```yaml
services:
	docify:
		build:
			context: .
			args:
				INSTALL_FULL: "false"
		image: docify:mini
		container_name: docify
		ports:
			- "5000:5000"
		environment:
			SECRET_KEY: change-me
			ALLOWED_IPS: 0.0.0.0/0
		volumes:
			- ./data/instance:/app/instance
```

## IP allowlist

The app blocks requests by default except localhost (127.0.0.1/32). Configure allowed IPs using an environment variable before starting the app:

```powershell
$env:ALLOWED_IPS = "127.0.0.1/32,192.168.1.0/24"
python app.py
```

To expose publicly (not recommended for production without hardening), you can use `0.0.0.0/0`:

```powershell
$env:ALLOWED_IPS = "0.0.0.0/0"
python app.py
```

Health endpoint `/health` is exempt from IP checks for probes/monitoring.

## Environment variables (.env supported)

- `SECRET_KEY` — Flask secret key (the app uses a fallback if not set)
- `ALLOWED_IPS` — Comma-separated CIDRs; default `127.0.0.1/32`
- `GOOGLE_API_KEY` — Optional for Gemini usage in `evaluate_different_modules.py`

You can create a `.env` file (if you install `python-dotenv`) with:

```
SECRET_KEY=change-me
ALLOWED_IPS=127.0.0.1/32
GOOGLE_API_KEY=your_key_here
```

## Data & files

- SQLite DB auto-creates at first run (`docify.db`)
- `users.csv` is exported after registration
- `query_dataset.csv` collects user messages from the chatbot
- FAISS index is stored under `faiss_index/` if you generate vectors locally

These are ignored by `.gitignore`.

## Project layout (key files)

- `app.py` — main Flask app with login, dashboard, FAQ, `/chatbot`, `/health`
- `app2.py` — same UI; proxies `/chatbot` to `http://127.0.0.1:5003/chatbot`
- `evaluate_different_modules.py` — chatbot helpers with safe fallbacks
- `vector_creator.py` — build/load FAISS index from `faq.txt`
- `chatbot*.py` — optional chatbot microservices (ports 5001/5002/5003)
- `templates/` — Jinja templates (index, dashboard, login, register, etc.)
- `testsprite.py` — endpoint tests using Flask test client
- `requirements.txt` — full dependency list (ML/AI heavy)

## Troubleshooting

- 403 on routes: your IP is not allowed; set `ALLOWED_IPS` to include your client.
- Import errors for ML libs: they are optional unless you run the ML chatbots; install via `requirements.txt`.
- Port already in use: stop the conflicting service or change `app.run(..., port=5000)`.
- Ollama model not found: ensure Ollama is running and the `docify` model is available for the Llama-based chatbot.
- Chatbot service ports: the optional microservices listen on their own ports (T5 ~5001, LoRA T5 ~5002, Ollama ~5003). The main app `app.py` uses an internal fallback unless you run and proxy to them.
 - Old helper test files (`test_chatbot.py`, `test_fixes.py`, `test_import.py`) are deprecated and kept as stubs. Use `testsprite.py`.

## Development tips

- The app writes user messages to `query_dataset.csv` for later analysis. You can disable that in `app.py` if needed.
- The SQLite database and other runtime files are kept out of the source tree in the `instance/` folder for safety. In Docker, this is `/app/instance`.
- For advanced chatbot features, see `chatbot.py`, `chatbot2.py`, and `chatbot3usingllama2formollama.py`. They’ve been cleaned up to avoid hardcoded paths and duplicated initializations.

## License

This project is for assessment/educational purposes.
