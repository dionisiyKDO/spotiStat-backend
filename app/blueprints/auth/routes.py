from flask import redirect, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.utils.utils import *
from app.config import Config
from . import auth_bp


@auth_bp.route('/session')
def session_status():
    user_id = session.get('user_id', None)
    username = session.get('username', None)
    logged_in = username is not None
    
    return jsonify({
        'logged_in': logged_in, 
        'user_id': user_id,
        'username': username
    })


# Registration route
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new user
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
    )
    
    db_session.add(user)
    db_session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

# Login route
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Find user by username
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Store user info in session
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user.id,
        'username': user.username
    }), 200

# Logout route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect("http://localhost:5173/login")

# Helper function to get current user (replaces get_spotify_client)
def get_current_user():
    user_id = session.get('username')
    if not user_id:
        return None
    
    user = User.query.get(user_id)
    return user

# Check if user is authenticated (decorator function)
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function




