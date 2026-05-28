import os


class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-fallback-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() in {'1', 'true', 'yes'}
    WTF_CSRF_TIME_LIMIT = 60 * 60
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '60'))
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() not in {'false', '0', 'no'}
