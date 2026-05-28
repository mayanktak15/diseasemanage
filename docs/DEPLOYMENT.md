# Deployment Guide - Docify Online

Docify Online is designed for lightweight deployment on CPU-only Ubuntu systems (4-8 GB RAM).

---

## 1. Recommended Python Version
* **Python 3.11 or 3.12** is highly recommended for production deployments.
* Python 3.13 is fully compatible.
* Python 3.14 (pre-release / dev) compatibility is maintained by keeping all dependencies standard and removing deprecated LangChain wrappers.

---

## 2. Rebuilding clean virtual environments

To rebuild a clean, secure deployment environment without GPU/CUDA packaging conflicts, run the following terminal commands:

### A. Minimal Deployment (Zero-dependency Local FAQ fallback mode)
Requires less than 100MB RAM, starts instantly, and does not install any PyTorch or ML packages.

```bash
# Remove any old virtual environment to clean state
rm -rf .venv

# Create a clean Python environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
python -m pip install -U pip

# Install minimal web & db requirements
python -m pip install -r requirements-minimal.txt
```

### B. Full Semantic Deployment (CPU-only AI-enabled mode)
Enables FAISS vector similarity and local sentence embeddings without downloading heavy CUDA/NVIDIA GPU libraries.

```bash
# Remove any old virtual environment
rm -rf .venv

# Create clean virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
python -m pip install -U pip

# Install all packages
python -m pip install -r requirements-minimal.txt -r requirements-ai.txt
```

---

## 3. Production Deployment with Gunicorn

For stable production execution on Ubuntu Linux, always execute behind a reverse proxy (like Nginx) and run using Gunicorn:

```bash
# In production, ensure key environment variables are set
export SECRET_KEY="your-long-secure-random-string"
export FLASK_ENV="production"
export SESSION_COOKIE_SECURE="true"
export ALLOWED_IPS="127.0.0.1/32,192.168.1.0/24"  # Comma-separated allowlist

# Run Gunicorn with pre-forked workers
gunicorn -b 0.0.0.0:5000 --workers 4 --threads 2 app:app
```

---

## 4. Docker Production Execution

Multi-stage builds are automated within our `Dockerfile` to create highly optimized containers.

### A. Building and running the Minimal web image:
```bash
# Build
docker build -t docify:minimal --build-arg INSTALL_FULL=false .

# Run
docker run -d \
  --name docify-web \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e ALLOWED_IPS="0.0.0.0/0" \
  -v docify_data:/app/instance \
  docify:minimal
```

### B. Building and running the Full semantic AI image:
```bash
# Build
docker build -t docify:ai --build-arg INSTALL_FULL=true .

# Run
docker run -d \
  --name docify-ai \
  -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e ALLOWED_IPS="0.0.0.0/0" \
  -v docify_data:/app/instance \
  docify:ai
```
