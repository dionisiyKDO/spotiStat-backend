from flask import Blueprint

db_bp = Blueprint('database', __name__, url_prefix='/db')
# TODO: rethink database logic. Not store everything in one table, split it up by years?, or half years?
# Queries on specific dates take too long

from . import routes, utils