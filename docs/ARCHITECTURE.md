# System Architecture - Docify Online

Docify Online is a secure, lightweight, production-grade medical consultation and AI chatbot assistant application. It is designed to run efficiently on CPU-only Linux systems (4-8 GB RAM) with minimal latency and instant boot times.

---

## 1. Core Structure and Blueprint Pattern

The application is structured using the **Flask Application Factory Pattern** to avoid circular imports and enable configurable, modular deployments.

```
app/
  ├── __init__.py          # create_app() factory
  ├── config.py            # Environment configurations & session cookies
  ├── extensions.py        # Shared extensions (SQLAlchemy, Migrate, WTF, Limiter, Cache)
  ├── models.py            # SQLite/Postgres DB tables & Audit Hooks
  ├── middleware/          # IP filtering & security headers
  ├── routes/              # Modular blueprints (auth, dashboard, chatbot, main, errors)
  ├── services/            # High-level business logic
  └── utils/               # CSV exports, auth checks, database session wrappers
```

---

## 2. Chatbot RAG Provider Architecture

The chatbot is built as an independent, lazy-loaded package in `chatbot/`. It operates under a **four-stage provider abstraction** with a hierarchical, graceful failover system:

```
                  ┌──────────────────────────────┐
                  │      User Chat Request       │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │    Rule-Based Matcher        ├─► [Response Matched]
                  └──────────────┬───────────────┘
                                 │ [No Match]
                                 ▼
                  ┌──────────────────────────────┐
                  │  Hybrid Context Retriever    │
                  │  (Keyword + Vector search)   │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │     1. Google Gemini Mode    ├─► [Success]
                  └──────────────┬───────────────┘
                                 │ [Fail / Offline]
                                 ▼
                  ┌──────────────────────────────┐
                  │       2. Ollama Mode         ├─► [Success]
                  └──────────────┬───────────────┘
                                 │ [Fail / Offline]
                                 ▼
                  ┌──────────────────────────────┐
                  │   3. HuggingFace CPU Mode    ├─► [Success]
                  └──────────────┬───────────────┘
                                 │ [Fail / Offline]
                                 ▼
                  ┌──────────────────────────────┐
                  │     4. Zero-Dependency       │
                  │        Local FAQ Mode        │
                  └──────────────────────────────┘
```

### Retrieval Rank Fusion
* **FAISS CPU Semantic Search**: Query is embedded via a lazy-loaded `sentence-transformers/all-MiniLM-L6-v2` model and searched against a local FAISS index.
* **TF-IDF Keyword Overlap**: Resolves keyword scores using `scikit-learn` vectorizers or falls back to standard word tokens overlap.
* **Rank Fusion**: Combines scores using configurable keyword and embedding weights.

### Performance Caching
To resolve excessive RAM usage and slow cold starts:
1. The FAISS index is generated once and persisted to `instance/faq_faiss.idx` alongside an MD5/SHA256 hash of `faq.txt`.
2. On startup, the vector store reads the index directly from disk in less than 5 milliseconds, avoiding the need to re-encode all FAQ items.
3. If FAISS/PyTorch is missing, the retriever falls back to standard NumPy matrix multiplication or pure Python cosine similarity.

---

## 3. Database Audit Logging & Soft Deletes

### Soft Deletes
The `Consultation` table has an `is_deleted` boolean flag. In order to protect records:
* Deletes are logical (`is_deleted = True`) instead of physical database purges.
* Dashboard queries automatically filter records to retrieve only active items (`is_deleted=False`).

### Dynamic Audit Hook
An active session hook (`after_flush`) is registered directly in `app/models.py`. It monitors SQLAlchemy sessions at runtime:
1. **Inserts**: Logs creation parameters for `User` and `Consultation` tables.
2. **Updates**: Audits modified column fields on any records.
3. **Deletes**: Tracks logical soft deletes and any hard deletions from admin layers.

---

## 4. Security Hardening

* **Hardened IP Filtering**: Validates `X-Forwarded-For` proxy chains securely (resolves client IP and blocks spoofed requests). Allows CIDR formats (e.g. `127.0.0.1/32`, `10.0.0.0/8`).
* **Secure Cookie Flags**: Session cookies are configured with `HTTPOnly`, `SameSite=Lax`, and `Secure` (dynamic for SSL production instances).
* **CSRF Validation**: Flask-WTF protects all POST requests, including AJAX chatbot inputs, using `X-CSRFToken` request headers.
