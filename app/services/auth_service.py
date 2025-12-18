from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db
from app.models import User


class AuthService:
    """Service for authentication-related operations."""
    
    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate a user with username and password.
        Returns (user, success, message)
        """
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return None, False, 'Invalid username or password.'
        
        if not check_password_hash(user.password_hash, password):
            return None, False, 'Invalid username or password.'
        
        return user, True, 'Login successful'
    
    @staticmethod
    def create_user(username, password, role='user'):
        """
        Create a new user account.
        Returns (user, success, message)
        """
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return None, False, 'Username already exists.'
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password_hash=hashed_password,
            role=role
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user, True, 'Account created successfully'
        except Exception as e:
            db.session.rollback()
            return None, False, f'Error creating account: {str(e)}'
    
    @staticmethod
    def reset_password(username, new_password):
        """
        Reset a user's password.
        Returns (success, message)
        """
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return False, 'Username not found.'
        
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return True, 'Password updated successfully'
        except Exception as e:
            db.session.rollback()
            return False, f'Error updating password: {str(e)}'
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        return db.session.get(User, user_id)