from flask import Blueprint, jsonify, request, session
from app.services.user_service import UserService
from app.models import User
from app.database import db

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def login_required(f):
    """Custom login_required decorator using existing session system."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Please log in to access this page'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/announcements')
@login_required
def get_announcements():
    """Get all active announcements with read status"""
    user = get_current_user()
    announcements = UserService.get_active_announcements(user.user_id)
    return jsonify(announcements)

@api_bp.route('/announcements/mark-read/<int:announcement_id>', methods=['POST'])
@login_required
def mark_announcement_read(announcement_id):
    """Mark a specific announcement as read"""
    user = get_current_user()
    success = UserService.mark_announcement_read(user.user_id, announcement_id)
    return jsonify({'success': success})

@api_bp.route('/announcements/mark-all-read', methods=['POST'])
@login_required
def mark_all_announcements_read():
    """Mark all announcements as read"""
    user = get_current_user()
    count = UserService.mark_all_announcements_read(user.user_id)
    return jsonify({'success': True, 'count': count})

@api_bp.route('/announcements/unread-count')
@login_required
def get_unread_count():
    """Get count of unread announcements"""
    user = get_current_user()
    count = UserService.get_unread_count(user.user_id)
    return jsonify({'count': count})