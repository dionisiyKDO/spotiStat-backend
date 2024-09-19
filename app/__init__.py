from flask import Flask
from flask_caching import Cache
from app.config import Config
from app.blueprints.auth import auth_bp
from app.blueprints.main import main_bp
from app.blueprints.db import db_bp
from app.filters import *
from app.utils.utils import cache

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    
    cache.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(db_bp)
    
    app.jinja_env.filters['format_datetime'] = format_datetime

    # from app.database import db_session
    # @app.teardown_appcontext
    # def shutdown_session(exception=None):
    #     db_session.remove()

    return app