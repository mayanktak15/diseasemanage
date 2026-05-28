# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install compiler/headers for any C extensions (e.g. greenlet/psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements-minimal.txt .
COPY requirements-ai.txt .

ARG INSTALL_FULL=false

# Install into a local prefix path inside builder stage
RUN pip install --upgrade pip && \
    if [ "$INSTALL_FULL" = "true" ]; then \
        pip install --prefix=/install -r requirements-minimal.txt -r requirements-ai.txt; \
    else \
        pip install --prefix=/install -r requirements-minimal.txt; \
    fi

# ==========================================
# STAGE 2: Pristine Runner
# ==========================================
FROM python:3.11-slim as runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ALLOWED_IPS=0.0.0.0/0 \
    FLASK_ENV=production \
    PATH="/home/appuser/.local/bin:/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.11/site-packages:${PYTHONPATH}"

WORKDIR /app

# Copy installed libraries from builder stage
COPY --from=builder /install /install

# Copy project files
COPY . .

# Security hardening: Create non-root system user and adjust permissions
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser && \
    mkdir -p /app/instance && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

# Healthcheck using python native urllib inside final container
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; \
try: \
    with urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3) as r: \
        sys.exit(0 if r.status == 200 else 1) \
except Exception: \
    sys.exit(1)"

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
