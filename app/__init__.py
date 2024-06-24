from flask import Flask
from flask_caching import Cache
from app.config import Config
from app.auth.routes import auth_bp
from app.main.routes import main_bp
from app.filters import *
from app.utils.utils import cache

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    
    cache.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    app.jinja_env.filters['format_datetime'] = format_datetime

    return app