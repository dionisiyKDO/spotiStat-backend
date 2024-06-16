from flask import Flask
from app.config import Config
from app.auth.routes import auth_bp
from app.main.routes import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app