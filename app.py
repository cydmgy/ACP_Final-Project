from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sea_life_gacha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Changed: Replaced session_id with username and password_hash
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    clicks = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)
    pulls = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory = db.relationship('UserCreature', backref='user', lazy=True, cascade='all, delete-orphan')
    completed_missions = db.relationship('UserMission', backref='user', lazy=True, cascade='all, delete-orphan')

class Creature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    image = db.Column(db.String(100))
    probability = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    target = db.Column(db.Integer, nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)

class UserCreature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creature_id = db.Column(db.Integer, db.ForeignKey('creature.id'), nullable=False)
    obtained_at = db.Column(db.DateTime, default=datetime.utcnow)
    creature = db.relationship('Creature', backref='user_creatures')

class UserMission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('mission.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    mission = db.relationship('Mission', backref='user_missions')

# --- Helper Functions ---

def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def get_user_data(user):
    """Get all user data formatted for the frontend"""
    completed_missions = UserMission.query.filter_by(user_id=user.id, completed=True).all()
    completed_mission_ids = [mission.mission_id for mission in completed_missions]
    
    inventory_creatures = UserCreature.query.filter_by(user_id=user.id).join(Creature).all()
    inventory = [
        {
            'id': uc.id,
            'name': uc.creature.name,
            'rarity': uc.creature.rarity,
            'image': uc.creature.image
        }
        for uc in inventory_creatures
    ]
    
    return {
        'clicks': user.clicks,
        'coins': user.coins,
        'pulls': user.pulls,
        'completed_missions': completed_mission_ids,
        'inventory': inventory
    }

def get_active_missions():
    return Mission.query.filter_by(is_active=True).order_by(Mission.order).all()

# --- Authentication Routes ---

@app.route('/auth')
def auth():
    """Displays the login/register/forgot password forms."""
    if get_current_user():
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password.', 'error')
        return redirect(url_for('auth'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('auth'))
        
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('auth'))
    
    # Create new user
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    
    # Log them in automatically
    session['user_id'] = new_user.id
    flash('Account created! Welcome!', 'success')
    return redirect(url_for('home'))

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    
    user = User.query.filter_by(username=username).first()
    
    if user:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully. Please log in.', 'success')
        return redirect(url_for('auth'))
    else:
        flash('Username not found.', 'error')
        return redirect(url_for('auth'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth'))

# --- Game Routes (Protected) ---

@app.route('/')
def home():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth'))
        
    user_data = get_user_data(user)
    missions = get_active_missions()
    
    return render_template('home.html', 
                         username=user.username, # Passed for display
                         clicks=user_data['clicks'], 
                         coins=user_data['coins'],
                         missions=missions,
                         completed_missions=user_data['completed_missions'],
                         pulls=user_data['pulls'])

@app.route('/click', methods=['POST'])
def handle_click():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user.clicks += 1
        if user.clicks % 5 == 0:
            user.coins += 1
            
        # Mission Logic
        current_clicks = user.clicks
        coins_earned = 0
        missions = get_active_missions()
        
        for mission in missions:
            # Check if mission already completed
            completed = UserMission.query.filter_by(user_id=user.id, mission_id=mission.id).first()
            if not completed and current_clicks >= mission.target:
                new_completion = UserMission(
                    user_id=user.id,
                    mission_id=mission.id,
                    completed=True,
                    completed_at=datetime.utcnow()
                )
                db.session.add(new_completion)
                coins_earned += mission.reward
                
        if coins_earned > 0:
            user.coins += coins_earned
            
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'clicks': user.clicks,
            'coins': user.coins,
            'coins_earned': coins_earned
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/gacha')
def gacha():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth'))
    return render_template('gacha.html', coins=user.coins)

@app.route('/inventory')
def inventory():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth'))
    user_data = get_user_data(user)
    return render_template('inventory.html', inventory=user_data['inventory'])

@app.route('/pull_gacha', methods=['POST'])
def pull_gacha():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    try:
        data = request.get_json()
        pull_type = data.get('type', 'single')
        cost = 50 if pull_type == 'multi' else 5
        
        if user.coins < cost:
            return jsonify({'success': False, 'message': 'Not enough coins!'})
            
        user.coins -= cost
        user.pulls += (10 if pull_type == 'multi' else 1)
        
        # Pull Logic
        creatures = Creature.query.filter_by(is_active=True).all()
        if not creatures: 
            return jsonify({'success': False, 'message': 'No creatures in database'})

        results = []
        loops = 10 if pull_type == 'multi' else 1
        
        total_prob = sum(c.probability for c in creatures)
        
        for _ in range(loops):
            rand = random.uniform(0, total_prob)
            curr = 0
            selected = None
            for c in creatures:
                curr += c.probability
                if rand <= curr:
                    selected = c
                    break
            if not selected: selected = creatures[-1] # Fallback
            
            # Add to DB
            uc = UserCreature(user_id=user.id, creature_id=selected.id)
            db.session.add(uc)
            results.append({
                'name': selected.name,
                'rarity': selected.rarity,
                'image': selected.image
            })
            
        db.session.commit()
        
        if pull_type == 'single':
            return jsonify({'success': True, 'creature': results[0], 'coins': user.coins})
        else:
            return jsonify({'success': True, 'creatures': results, 'coins': user.coins})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Admin routes remain mostly same but should technically be protected (skipped for brevity)
@app.route('/admin/creatures')
def admin_creatures():
    creatures = Creature.query.all()
    return render_template('admin_creatures.html', creatures=creatures)

@app.route('/admin/missions')
def admin_missions():
    missions = Mission.query.all()
    return render_template('admin_missions.html', missions=missions)

# Initialization
def initialize_default_data():
    # Only initialize if tables are empty
    if not Creature.query.first():
        print("Initializing default creatures...")
        defaults = [
        # Common
        {"name": "Common 1", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 2", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 3", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 4", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 5", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 6", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 7", "rarity": "common", "image": ".png", "probability": 0.53},
        {"name": "Common 8", "rarity": "common", "image": ".png", "probability": 0.53},
    
        # Rare 
        {"name": "Rare 1", "rarity": "rare", "image": ".png", "probability": 0.30},
        {"name": "Rare 2", "rarity": "rare", "image": ".png", "probability": 0.30},
        {"name": "Rare 3", "rarity": "rare", "image": ".png", "probability": 0.30},
        {"name": "Rare 4", "rarity": "rare", "image": ".png", "probability": 0.30},
        {"name": "Rare 5", "rarity": "rare", "image": ".png", "probability": 0.30},
        {"name": "Rare 6", "rarity": "rare", "image": ".png", "probability": 0.30},
    
        # Epic 
        {"name": "Epic 1", "rarity": "epic", "image": ".png", "probability": 0.12},
        {"name": "Epic 2", "rarity": "epic", "image": ".png", "probability": 0.12},
        {"name": "Epic 3", "rarity": "epic", "image": ".png", "probability": 0.12},
        {"name": "Epic 4", "rarity": "epic", "image": ".png", "probability": 0.12},
    
        # Legendary 
        {"name": "Legendary 1", "rarity": "legendary", "image": ".png", "probability": 0.05}, 
        {"name": "Legendary 2", "rarity": "legendary", "image": ".png", "probability": 0.05},
        ]
        for c in defaults:
            db.session.add(Creature(**c))
    
    if not Mission.query.first():
        print("Initializing default missions...")
        defaults = [
            {"name": "First Steps", "description": "Click 10 times", "target": 10, "reward": 10},
            {"name": "Getting Started", "description": "Click 50 times", "target": 50, "reward": 25},
        ]
        for m in defaults:
            db.session.add(Mission(**m))
            
    db.session.commit()

with app.app_context():
    db.create_all()
    initialize_default_data()

if __name__ == '__main__':
    app.run(debug=True)