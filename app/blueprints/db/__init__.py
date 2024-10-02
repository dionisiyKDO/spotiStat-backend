from flask import Blueprint

db_bp = Blueprint('database', __name__, url_prefix='/db')

from . import routes, utils