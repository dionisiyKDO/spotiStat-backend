from flask import Blueprint

db_bp = Blueprint('database', __name__)

from . import routes