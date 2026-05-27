# Troubleshooting

## CSRF errors
- Ensure forms include `csrf_token()` and JS sends `X-CSRFToken`.
- Set `WTF_CSRF_ENABLED=false` for local debug only.

## Rate limit responses
- Reduce traffic or raise `RATELIMIT_DEFAULT`.
- Set `RATELIMIT_ENABLED=false` in tests.

## Chatbot empty response
- Confirm `faq.txt` exists and `FAQ_FILE_PATH` is correct.
- Install AI deps from requirements-ai.txt for embeddings.
