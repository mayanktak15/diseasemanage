# Docify Online

Docify Online is a secure, production-grade medical consultation and AI chatbot assistant application built on Python and Flask. It is designed to run efficiently on CPU-only Ubuntu systems (4-8 GB RAM) with minimal latency and instant boot times.

---

## Key Refactoring Goals Achieved

1. **Removed Heavyweight Dependencies**: Completely eliminated LangChain libraries to prevent startup delays, packaging bloat, and dependency incompatibilities.
2. **CPU-only Execution**: Pin strictly CPU-based sentence embedding generators (`sentence-transformers/all-MiniLM-L6-v2`) and `faiss-cpu`, avoiding large CUDA / NVIDIA drivers download.
3. **Graceful Failover Chatbot**: The chatbot implements a hierarchical 4-stage provider abstraction (Gemini API -> local Ollama server -> local CPU HuggingFace mode -> Local zero-dependency FAQ rule-based fallback), ensuring it functions beautifully even if no AI dependencies are installed.
4. **Database Audit Logging & Soft Deletes**: Added `is_deleted` logical columns on consultations, custom database event session listeners for flush-level auditing, and proper pagination.
5. **Security Hardening**: Secure HTTPOnly/SameSite session cookies, CSRF protection, and hardened CIDR IP allowlisting middleware behind reverse proxies.
6. **Modern Bootstrap 5 UI**: Replaced Tailwind CSS with Bootstrap 5 templates, styling highly responsive glassmorphism views and solving duplicate JavaScript handlers recursively.
7. **Clean Testing**: Built an elegant `pytest` environment with fixtures and extensive CRUD/chatbot verification.
8. **Multi-Stage Docker builds**: Optimized `Dockerfile` to create highly secure containers using non-root users.

---

## 1. Quick Start (Minimal, No-AI Fallback Mode)

This mode runs using **zero extra AI dependencies** (no PyTorch, no sentence-transformers). It requires less than 100MB of RAM and boots instantly.

```bash
# Clone the repository and navigate inside
cd diseasemanage

# Recreate a clean virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install minimal base dependencies
python -m pip install -U pip
python -m pip install -r requirements-minimal.txt

# Run the server
python app.py
```

* **App Link**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
* **Health probe**: [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

---

## 2. Semantic Search Start (CPU-only AI-Enabled Mode)

Installs the local lightweight embedding index (`all-MiniLM-L6-v2`) and TF-IDF rank fusion retrievers.

```bash
# Recreate clean environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
python -m pip install -U pip

# Install minimal and AI requirements
python -m pip install -r requirements-minimal.txt -r requirements-ai.txt

# Run the server
python app.py
```

---

## 3. Running Test Suites

We support full unit testing using `pytest` and original backward-compatible tests:

```bash
# Install test dependencies
python -m pip install -r requirements-minimal.txt -r requirements-dev.txt

# Run automated tests using pytest
pytest -v

# Run backward-compatible endpoint test suite
python testsprite.py
```

---

## 4. Multi-Stage Docker Builds

Automated Gunicorn production deployment inside secure non-root containers.

### A. Minimal Web Image:
```bash
docker build -t docify:minimal --build-arg INSTALL_FULL=false .
docker run --rm -p 5000:5000 -e SECRET_KEY="change-me" -e ALLOWED_IPS="0.0.0.0/0" docify:minimal
```

### B. Full Semantic AI Image:
```bash
docker build -t docify:ai --build-arg INSTALL_FULL=true .
docker run --rm -p 5000:5000 -e SECRET_KEY="change-me" -e ALLOWED_IPS="0.0.0.0/0" docify:ai
```

---

## 5. Documentation
* Detailed Architecture: [`docs/ARCHITECTURE.md`](file:///c:/Users/Mayank%20Tak/Downloads/checker/diseasemanage/docs/ARCHITECTURE.md)
* Deployment Guide: [`docs/DEPLOYMENT.md`](file:///c:/Users/Mayank%20Tak/Downloads/checker/diseasemanage/docs/DEPLOYMENT.md)
* Troubleshooting: [`docs/TROUBLESHOOTING.md`](file:///c:/Users/Mayank%20Tak/Downloads/checker/diseasemanage/docs/TROUBLESHOOTING.md)
