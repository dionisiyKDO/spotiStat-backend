from flask import Flask

from app.config import Config
from app.utils.utils import cache

from app.blueprints.auth import auth_bp
from app.blueprints.spotify import spotify_bp
from app.blueprints.db import db_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cache.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(db_bp)

    return app