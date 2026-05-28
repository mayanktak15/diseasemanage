# Troubleshooting Guide - Docify Online

This guide explains how to troubleshoot common issues when setting up and running Docify Online.

---

## 1. AI Dependencies and PyTorch Imports

### Issue: `No module named 'langchain_huggingface'` or `No module named 'langchain_community'`
* **Resolution**: Docify Online has been refactored to remove LangChain completely! We now use an optimized native-Python TF-IDF & FAISS hybrid retriever.
  * Delete your virtual environment and rebuild clean dependencies using `requirements-minimal.txt` and `requirements-ai.txt`.

### Issue: Torch is attempting to download CUDA/NVIDIA libraries
* **Resolution**: Ensure you specify the PyTorch CPU wheels repository index before installing `requirements-ai.txt`.
  ```bash
  python -m pip install -r requirements-minimal.txt -r requirements-ai.txt
  ```

### Issue: Installation of AI packages hangs or consumes extreme CPU usage
* **Resolution**: On Python 3.14, older versions of PyTorch (`<2.9.0`), scikit-learn (`<1.7.2`), and numpy (`<2.0.0`) lack precompiled wheels. This forces pip to compile them from source, utilizing C++ compilers and maxing out all CPU cores.
  - To fix this, use Python 3.14 wheel-compatible version pins in `requirements-ai.txt`: `torch==2.9.0+cpu`, `scikit-learn>=1.7.2`, and `numpy>=2.0.0`. These versions download precompiled binaries instantly in seconds.

---

## 2. Database Migrations and SQLite

### Issue: Column `is_deleted` or `updated_at` does not exist in SQLite
* **Resolution**: The database schema evolved to support soft deletes. If you are starting fresh, delete the old database file `instance/docify.db` to allow Flask to create all tables from scratch:
  ```bash
  # Delete DB
  rm instance/docify.db
  # Start app (it will auto-create database)
  python app.py
  ```
  For existing production databases, use Flask-Migrate to run schema migrations:
  ```bash
  flask db init
  flask db migrate -m "Add soft delete and timestamps"
  flask db upgrade
  ```

---

## 3. Security and CSRF Errors

### Issue: `400 Bad Request: The CSRF token is missing.`
* **Resolution**: Make sure your POST forms include the CSRF token:
  ```html
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ```
  If this error occurs during AJAX chatbot inputs:
  1. Ensure `csrf_token()` is outputted into a JavaScript variable inside the template.
  2. Send the token in the `X-CSRFToken` request header:
     ```javascript
     headers: { 
         'Content-Type': 'application/json', 
         'X-CSRFToken': csrfToken 
     }
     ```

---

## 4. IP Whitelist Blocking

### Issue: `403 Forbidden` response on accessing dashboard
* **Resolution**: The IP allowlist middleware is active.
  * For local debugging, configure `DISABLE_IP_FILTER=true` in your `.env` file, or add your local IP range to `ALLOWED_IPS` (e.g. `127.0.0.1/32` or `::1/128`).
  * In production reverse proxy environments, make sure Nginx/Apache sends correct `X-Forwarded-For` header.
