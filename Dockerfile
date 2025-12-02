# Lightweight Python base
FROM python:3.10-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # Allow inbound requests by default inside container; override as needed
    ALLOWED_IPS=0.0.0.0/0 \
    FLASK_ENV=production

WORKDIR /app

# Build args: install full ML stack or minimal
ARG INSTALL_FULL=false
ENV INSTALL_FULL=${INSTALL_FULL}

# Install deps first for better layer caching
COPY requirements.txt requirements.txt
COPY requirements-min.txt requirements-min.txt
RUN pip install --upgrade pip && \
        if [ "$INSTALL_FULL" = "true" ]; then \
            pip install -r requirements.txt; \
        else \
            pip install -r requirements-min.txt; \
        fi

# Copy project
COPY . .

# Service port
EXPOSE 5000

# Ensure instance folder exists for SQLite
RUN mkdir -p /app/instance

# Healthcheck using Python (no curl needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python - << 'PY'
import urllib.request, sys
try:
        with urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3) as r:
                sys.exit(0 if r.status == 200 else 1)
except Exception:
        sys.exit(1)
PY

# Default command (Gunicorn for production)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
