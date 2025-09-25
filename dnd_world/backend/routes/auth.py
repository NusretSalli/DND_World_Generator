"""Authentication routes for user management."""

from flask import request, jsonify, session
from dnd_world.models import User
from dnd_world.database import db
from . import bp


@bp.route('/api/register', methods=['POST'])
def register():
    """Register a new user account."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Create user
        user, message = User.create_user(username, password)
        
        if user:
            # Automatically log in the new user
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({
                'success': True,
                'message': message,
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            }), 201
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@bp.route('/api/login', methods=['POST'])
def login():
    """Authenticate user login."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Authenticate user
        user = User.authenticate(username, password)
        
        if user:
            # Set session
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@bp.route('/api/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500


@bp.route('/api/user', methods=['GET'])
def get_current_user():
    """Get information about the currently logged-in user."""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not logged in'}), 401
        
        user = User.query.get(user_id)
        if not user:
            session.clear()  # Clear invalid session
            return jsonify({'error': 'User not found'}), 401
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user info: {str(e)}'}), 500


@bp.route('/api/check_auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated."""
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        
        if user_id and username:
            # Verify user still exists
            user = User.query.get(user_id)
            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'username': user.username
                    }
                }), 200
            else:
                session.clear()
        
        return jsonify({'authenticated': False}), 200
        
    except Exception as e:
        return jsonify({'error': f'Auth check failed: {str(e)}'}), 500