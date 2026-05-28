import logging
import os
import warnings

from flask import Flask

from .config import BaseConfig
from .extensions import cache, csrf, db, limiter, migrate
from .middleware.ip_filter import register_ip_filter
from .middleware.security_headers import register_security_headers
from .routes.auth import auth_bp
from .routes.chatbot import chatbot_bp
from .routes.dashboard import dashboard_bp
from .routes.errors import register_error_handlers
from .routes.main import main_bp
from .utils.sqlite import ensure_sqlite


warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*MINGW-W64.*')
os.environ['PYTHONWARNINGS'] = 'ignore::RuntimeWarning'


def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _build_db_uri(app: Flask) -> str:
    db_uri_env = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL')
    if db_uri_env:
        return db_uri_env

    is_render = bool(os.getenv('RENDER')) or bool(os.getenv('RENDER_SERVICE_NAME')) or bool(os.getenv('RENDER_INSTANCE_ID'))
    sqlite_path_env = os.getenv('SQLITE_PATH')

    if is_render and not sqlite_path_env:
        default_render_path = '/var/data/docify.db' if os.path.isdir('/var/data') else None
        sqlite_path = default_render_path or os.path.join(app.instance_path, 'docify.db')
    else:
        sqlite_path = sqlite_path_env or os.path.join(app.instance_path, 'docify.db')
    return f'sqlite:///{sqlite_path}'


def create_app(config_object: type[BaseConfig] = BaseConfig) -> Flask:
    ensure_sqlite()
    _load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    app.config['SQLALCHEMY_DATABASE_URI'] = _build_db_uri(app)
    app.config['ALLOWED_IPS'] = os.getenv('ALLOWED_IPS', '127.0.0.1/32').split(',')
    app.config['DISABLE_IP_FILTER'] = os.getenv('DISABLE_IP_FILTER', 'false').lower() in {'1', 'true', 'yes'}

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chatbot_bp)

    register_ip_filter(app)
    register_security_headers(app)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
