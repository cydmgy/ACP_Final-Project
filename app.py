from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import random
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'secret_key'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sea_life_gacha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
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

def get_or_create_user():
    """Get current user or create new one"""
    if 'user_id' not in session:
        # Create new user without session_id
        user = User(
            session_id="temp_" + str(random.randint(1000, 9999)),  # Temporary ID
            clicks=0,
            coins=0,
            pulls=0
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return user
    
    user = User.query.get(session['user_id'])
    if not user:
        # User was deleted from DB, create new one
        user = User(
            session_id="temp_" + str(random.randint(1000, 9999)),
            clicks=0,
            coins=0,
            pulls=0
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
    
    return user

def get_user_data(user):
    """Get all user data from database"""
    # Get completed missions
    completed_missions = UserMission.query.filter_by(user_id=user.id, completed=True).all()
    completed_mission_ids = [mission.mission_id for mission in completed_missions]
    
    # Get inventory with creature details
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
    """Get all active missions from database"""
    return Mission.query.filter_by(is_active=True).order_by(Mission.order).all()

def initialize_default_data():
    """Initialize default creatures and missions if database is empty"""
    # Check if we need to initialize
    if Creature.query.first() is None:
        print("Initializing default creatures...")
        
        # Default creatures with probabilities
        default_creatures = [
        # Common 
        {"name": "Common 1", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 2", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 3", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 4", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 5", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 6", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 7", "rarity": "common", "image": ".png", "probability": 0.01},
        {"name": "Common 8", "rarity": "common", "image": ".png", "probability": 0.01},
    
        # Rare 
        {"name": "Rare 1", "rarity": "rare", "image": ".png", "probability": 0.0375},
        {"name": "Rare 2", "rarity": "rare", "image": ".png", "probability": 0.0375},
        {"name": "Rare 3", "rarity": "rare", "image": ".png", "probability": 0.0375},
        {"name": "Rare 4", "rarity": "rare", "image": ".png", "probability": 0.0375},
        {"name": "Rare 5", "rarity": "rare", "image": ".png", "probability": 0.0375},
        {"name": "Rare 6", "rarity": "rare", "image": ".png", "probability": 0.0375},
    
        # Epic 
        {"name": "Epic 1", "rarity": "epic", "image": ".png", "probability": 0.10},
        {"name": "Epic 2", "rarity": "epic", "image": ".png", "probability": 0.10},
        {"name": "Epic 3", "rarity": "epic", "image": ".png", "probability": 0.10},
        {"name": "Epic 4", "rarity": "epic", "image": ".png", "probability": 0.10},
    
        # Legendary 
        {"name": "Legendary 1", "rarity": "legendary", "image": ".png", "probability": 0.25}, 
        {"name": "Legendary 2", "rarity": "legendary", "image": ".png", "probability": 0.25},
    ]
        
        for creature_data in default_creatures:
            creature = Creature(**creature_data)
            db.session.add(creature)
    
    if Mission.query.first() is None:
        print("Initializing default missions...")
        
        # Default missions
        default_missions = [
            {"name": "First Steps", "description": "Click 10 times", "target": 10, "reward": 10, "order": 1},
            {"name": "Getting Started", "description": "Click 50 times", "target": 50, "reward": 25, "order": 2},
            {"name": "Dedicated Clicker", "description": "Click 100 times", "target": 100, "reward": 50, "order": 3},
            {"name": "Expert Clicker", "description": "Click 500 times", "target": 500, "reward": 200, "order": 4},
            {"name": "Master Clicker", "description": "Click 1000 times", "target": 1000, "reward": 400, "order": 5},
        ]
        
        for mission_data in default_missions:
            mission = Mission(**mission_data)
            db.session.add(mission)
    
    db.session.commit()

def pull_single_gacha(user):
    """Helper function for single gacha pull"""
    # Get all creatures with their probabilities
    creatures = Creature.query.filter_by(is_active=True).all()
    
    if not creatures:
        # Fallback to default creatures if none in database
        return create_fallback_creature(user)
    
    # Create a proper probability distribution
    total_probability = sum(creature.probability for creature in creatures)
    
    # Normalize probabilities to ensure they sum to 1
    normalized_creatures = []
    for creature in creatures:
        normalized_prob = creature.probability / total_probability
        normalized_creatures.append((creature, normalized_prob))
    
    # Sort by probability (descending) for debugging
    normalized_creatures.sort(key=lambda x: x[1], reverse=True)
    
    # Debug: print probabilities
    print("Gacha probabilities:")
    for creature, prob in normalized_creatures:
        print(f"  {creature.name} ({creature.rarity}): {prob:.2%}")
    
    # Select creature based on probability
    rand = random.random()
    cumulative_prob = 0
    
    for creature, prob in normalized_creatures:
        cumulative_prob += prob
        if rand <= cumulative_prob:
            # Create user creature record
            user_creature = UserCreature(
                user_id=user.id,
                creature_id=creature.id
            )
            db.session.add(user_creature)
            db.session.flush()
            
            # Return creature data for response
            return {
                'id': user_creature.id,
                'name': creature.name,
                'rarity': creature.rarity,
                'image': creature.image
            }
    
    # Fallback if no creature selected (shouldn't happen with proper probabilities)
    return create_fallback_creature(user)

def create_fallback_creature(user):
    """Create a fallback creature if database is empty"""
    fallback_creature = Creature(
        name="Clownfish",
        rarity="common",
        image="clownfish.png",
        probability=0.79
    )
    db.session.add(fallback_creature)
    db.session.flush()
    
    user_creature = UserCreature(
        user_id=user.id,
        creature_id=fallback_creature.id
    )
    db.session.add(user_creature)
    db.session.flush()
    
    return {
        'id': user_creature.id,
        'name': fallback_creature.name,
        'rarity': fallback_creature.rarity,
        'image': fallback_creature.image
    }

@app.route('/')
def home():
    user = get_or_create_user()
    user_data = get_user_data(user)
    missions = get_active_missions()
    
    return render_template('home.html', 
                         clicks=user_data['clicks'], 
                         coins=user_data['coins'],
                         missions=missions,
                         completed_missions=user_data['completed_missions'],
                         pulls=user_data['pulls'])

@app.route('/click', methods=['POST'])
def handle_click():
    try:
        user = get_or_create_user()
        
        # Increment clicks
        user.clicks += 1
        
        # Give coins every 20 clicks
        if user.clicks % 1 == 0:
            user.coins += 1000
        
        # Check missions
        current_clicks = user.clicks
        coins_earned = 0
        missions = get_active_missions()
        
        for mission in missions:
            user_mission = UserMission.query.filter_by(
                user_id=user.id, 
                mission_id=mission.id
            ).first()
            
            if not user_mission and current_clicks >= mission.target:
                # Complete mission
                user_mission = UserMission(
                    user_id=user.id,
                    mission_id=mission.id,
                    completed=True,
                    completed_at=datetime.utcnow()
                )
                db.session.add(user_mission)
                coins_earned += mission.reward
        
        if coins_earned > 0:
            user.coins += coins_earned
        
        # Update user
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'clicks': user.clicks,
            'coins': user.coins,
            'coins_earned': coins_earned,
            'new_missions_completed': coins_earned > 0
        })
    except Exception as e:
        print(f"Error in handle_click: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/gacha')
def gacha():
    user = get_or_create_user()
    user_data = get_user_data(user)
    return render_template('gacha.html', coins=user_data['coins'])

@app.route('/inventory')
def inventory():
    user = get_or_create_user()
    user_data = get_user_data(user)
    return render_template('inventory.html', inventory=user_data['inventory'])

@app.route('/pull_gacha', methods=['POST'])
def pull_gacha():
    try:
        data = request.get_json()
        pull_type = data.get('type', 'single') if data else 'single'
        
        user = get_or_create_user()
        
        if pull_type == 'single':
            cost = 20
            if user.coins < cost:
                return jsonify({
                    'success': False, 
                    'message': f'Not enough coins! Need {cost} coins for one pull. You have {user.coins} coins.'
                })
            
            user.coins -= cost
            user.pulls += 1
            creature = pull_single_gacha(user)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'creature': creature,
                'coins': user.coins,
                'type': 'single'
            })
        
        elif pull_type == 'multi':
            cost = 200
            if user.coins < cost:
                return jsonify({
                    'success': False, 
                    'message': f'Not enough coins! Need {cost} coins for a 10x pull. You have {user.coins} coins.'
                })
            
            user.coins -= cost
            user.pulls += 10
            creatures = []
            for i in range(10):
                creature = pull_single_gacha(user)
                creatures.append(creature)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'creatures': creatures,
                'coins': user.coins,
                'type': 'multi'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid pull type'})
            
    except Exception as e:
        print(f"Error in pull_gacha: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Admin routes
@app.route('/admin/creatures')
def admin_creatures():
    creatures = Creature.query.all()
    return render_template('admin_creatures.html', creatures=creatures)

@app.route('/admin/missions')
def admin_missions():
    print("Admin missions route accessed")
    missions = Mission.query.all()
    print(f"Found {len(missions)} missions")
    return render_template('admin_missions.html', missions=missions)

@app.route('/admin/creature/<int:creature_id>/toggle', methods=['POST'])
def toggle_creature(creature_id):
    try:
        creature = Creature.query.get_or_404(creature_id)
        data = request.get_json()
        creature.is_active = data.get('activate', False)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/mission/<int:mission_id>/toggle', methods=['POST'])
def toggle_mission(mission_id):
    try:
        mission = Mission.query.get_or_404(mission_id)
        data = request.get_json()
        mission.is_active = data.get('activate', False)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/reset_database', methods=['POST'])
def reset_database():
    """Completely reset the database with new creatures"""
    try:
        # Drop all tables
        db.drop_all()
        
        # Recreate tables
        db.create_all()
        
        # Reinitialize default data
        initialize_default_data()
        
        # Clear session
        session.clear()
        
        return jsonify({'success': True, 'message': 'Database reset successfully with new creatures!'})
    except Exception as e:
        print(f"Error in reset_database: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Create tables and initialize default data when the app starts
with app.app_context():
    db.create_all()
    initialize_default_data()
    print("Database tables created and initialized successfully!")

if __name__ == '__main__':
    app.run(debug=True)