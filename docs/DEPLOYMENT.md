# Deployment

## Local
- Install minimal deps: `python -m pip install -r requirements-minimal.txt`
- Run: `python app.py`

## Production
- Use Gunicorn: `gunicorn -b 0.0.0.0:5000 app:app`
- Set `SECRET_KEY` and `ALLOWED_IPS`.

## Docker
- Minimal image: `docker build -t docify:mini --build-arg INSTALL_FULL=false .`
- Full image: `docker build -t docify:full --build-arg INSTALL_FULL=true .`

## Environment Variables
- SECRET_KEY (required)
- ALLOWED_IPS (CIDR list)
- DISABLE_IP_FILTER (optional)
- SQLITE_PATH or DATABASE_URL
- FAQ_FILE_PATH, EMBEDDING_MODEL, CHATBOT_TOP_K
