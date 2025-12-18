from flask import Flask
from app.database import db
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration directly here (no config.py needed)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'secret_key'
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'data', 'sea_life_gacha.db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.game import game_bp
    from app.routes.admin import admin_bp
    from app.routes.profile import profile_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profile_bp)
    
    return app