from flask import Flask

from app.config import Config

from app.blueprints.db import db_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(db_bp)

    return app