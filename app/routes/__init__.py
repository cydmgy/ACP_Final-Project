from app.routes.auth import auth_bp
from app.routes.game import game_bp
from app.routes.admin import admin_bp
from app.routes.profile import profile_bp
from app.routes.api import api_bp

__all__ = ['auth_bp', 'game_bp', 'admin_bp', 'profile_bp', 'api_bp']