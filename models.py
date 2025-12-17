from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database instance
db = SQLAlchemy()

# --- Database Models ---

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    clicks = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)
    pulls = db.Column(db.Integer, default=0)

    avatar = db.Column(db.String(50), default='default.png')
    bio = db.Column(db.String(200), default='A marine creature collector')
    pity_counter = db.Column(db.Integer, default=0) 
    legendary_pity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inventory = db.relationship('UserCreature', backref='user', lazy=True, cascade='all, delete-orphan')
    completed_missions = db.relationship('UserMission', backref='user', lazy=True, cascade='all, delete-orphan')

class Creature(db.Model):
    creature_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(100))
    probability = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))

class Mission(db.Model):
    mission_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    target = db.Column(db.Integer, nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    order = db.Column(db.Integer, default=0)

class UserCreature(db.Model):
    inventory_id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    creature_id = db.Column(db.Integer, db.ForeignKey('creature.creature_id'), nullable=False)
    obtained_at = db.Column(db.DateTime, default=datetime.utcnow)
    creature = db.relationship('Creature', backref='user_creatures')

class UserMission(db.Model):
    mission_completion_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('mission.mission_id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    mission = db.relationship('Mission', backref='user_missions')