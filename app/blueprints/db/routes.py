from flask import jsonify, session, current_app
import pandas as pd

from app.utils.utils import *
from . import db_bp


@db_bp.route('/import_history')
def import_history():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    tmp = read_json_and_store_data(json_directory='./app/data/dionisiy')

    return jsonify(tmp.to_dict())

@db_bp.route('/get_record/<id>')
def get_record(id):
    # TODO: check if id is valid, there is an entry with that id
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    tmp = db_session.query(StreamingHistory).get(id)
    
    return jsonify(tmp.to_dict())

