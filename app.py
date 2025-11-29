from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import random
from functools import wraps
from datetime import datetime

# Removed: from sqlalchemy import case

# Import data models and form definitions
from models import db, User, Creature, Mission, UserCreature, UserMission
from forms import LoginForm, RegisterForm, ForgotPasswordForm, CreatureForm, MissionForm

app = Flask(__name__)
app.secret_key = 'secret_key'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sea_life_gacha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# --- Helper Functions ---

def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def get_user_data(user):
    """Get all user data formatted for the frontend"""
    completed_missions = UserMission.query.filter_by(user_id=user.user_id, completed=True).all()
    completed_mission_ids = [mission.mission_id for mission in completed_missions]
    
    inventory_creatures = UserCreature.query.filter_by(user_id=user.user_id).join(Creature).all()
    inventory = [
        {
            'id': uc.inventory_id,
            'name': uc.creature.name,
            'rarity': uc.creature.rarity,
            'image': uc.creature.image,
            'description': uc.creature.description
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

def admin_required(f):
    """Decorator to check if the current user has the 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin': # Check for the 'admin' role
            flash("Access denied. Admin privileges required.", 'error')
            return redirect(url_for('home')) 
        return f(*args, **kwargs)
    return decorated_function

def get_all_missions():
    return Mission.query.order_by(Mission.order).all()

# --- Authentication Routes ---

@app.route('/auth')
def auth():
    if get_current_user():
        return redirect(url_for('home'))
    
    # Pass form instances to the template
    login_form = LoginForm()
    register_form = RegisterForm()
    forgot_form = ForgotPasswordForm()
    
    section = request.args.get('section', 'login')
    
    return render_template('auth.html', 
                           initial_section=section,
                           login_form=login_form,
                           register_form=register_form,
                           forgot_form=forgot_form)

@app.route('/login', methods=['POST']) 
def login():    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if the user exists and password is correct
        if user and check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.user_id 
            session['role'] = user.role 
            
            flash(f'Welcome, {user.username}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_creatures'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth', login_failed=True))
    return redirect(url_for('auth'))

@app.route('/register', methods=['POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth', section='register'))
        
        # Use sha256 method
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data, 
            password_hash=hashed_password,
            role='user')
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{error}", 'error')
            
    return redirect(url_for('auth', section='register'))

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully. Please log in.', 'success')
            return redirect(url_for('auth'))
        else:
            flash('Username not found.', 'error')
            
    return redirect(url_for('auth', section='forgot'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None) 
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth'))

# --- Game Routes ---

@app.route('/')
def home():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth'))
    user_data = get_user_data(user)
    
    return render_template('home.html', 
                           username=user.username, 
                           clicks=user_data['clicks'], 
                           coins=user.coins, 
                           missions=get_all_missions(), 
                           completed_missions=user_data['completed_missions'], 
                           pulls=user.pulls) 

@app.route('/click', methods=['POST'])
def handle_click():
    user = get_current_user()
    if not user: return jsonify({'error': 'Unauthorized'}), 401
    try:
        user.clicks += 1
        
        # Example coin logic, 1000 coins every 5 clicks for easy testing
        if user.clicks % 5 == 0: user.coins += 1000 
        
        current_clicks = user.clicks
        coins_earned = 0
        
        for mission in get_all_missions(): 
            completed = UserMission.query.filter_by(user_id=user.user_id, mission_id=mission.mission_id, completed=True).first()
            if not completed and current_clicks >= mission.target:
                new_completion = UserMission(user_id=user.user_id, mission_id=mission.mission_id, completed=True, completed_at=datetime.utcnow())
                db.session.add(new_completion)
                coins_earned += mission.reward
                
        if coins_earned > 0: user.coins += coins_earned
        db.session.commit()
        return jsonify({'clicks': user.clicks, 'coins': user.coins, 'coins_earned': coins_earned})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/gacha')
def gacha():
    user = get_current_user()
    if not user: return redirect(url_for('auth'))
    return render_template('gacha.html', coins=user.coins)

@app.route('/pull_gacha', methods=['POST'])
def pull_gacha():
    user = get_current_user()
    if not user: return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        pull_type = data.get('type', 'single')
        cost = 50 if pull_type == 'multi' else 5
        if user.coins < cost: return jsonify({'success': False, 'message': 'Not enough coins!'})
        
        user.coins -= cost
        user.pulls += (10 if pull_type == 'multi' else 1)
        creatures = Creature.query.all() 
        if not creatures: return jsonify({'success': False, 'message': 'No creatures in database'})
        
        results = []
        loops = 10 if pull_type == 'multi' else 1
        total_prob = sum(c.probability for c in creatures)
        
        if total_prob <= 0:
            return jsonify({'success': False, 'message': 'All creatures have zero or negative probability! Cannot pull.'})
        
        for _ in range(loops):
            rand = random.uniform(0, total_prob)
            curr, selected = 0, None
            for c in creatures:
                curr += c.probability
                if rand <= curr: selected = c; break
            if not selected: selected = creatures[-1] 
            db.session.add(UserCreature(user_id=user.user_id, creature_id=selected.creature_id))
            results.append({'name': selected.name, 'rarity': selected.rarity, 'image': selected.image})
        db.session.commit()
        return jsonify({'success': True, 'creature': results[0] if pull_type=='single' else None, 'creatures': results, 'coins': user.coins})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/inventory')
def inventory():
    user = get_current_user()
    if not user: return redirect(url_for('auth'))
    # Passes inventory data including the new description field
    return render_template('inventory.html', inventory=get_user_data(user)['inventory'])

# --- Admin Routes (Render) ---

@app.route('/admin/creatures')
@admin_required
def admin_creatures():
    # REVERTED: Sorting is back to default alphabetical by rarity, then name
    creatures = Creature.query.order_by(Creature.rarity, Creature.name).all()
    
    return render_template('admin_creatures.html', creatures=creatures)

@app.route('/admin/missions')
@admin_required
def admin_missions():
    return render_template('admin_missions.html', missions=Mission.query.order_by(Mission.order).all())

# --- Admin CRUD (Creatures) ---

@app.route('/admin/creatures/new', methods=['GET', 'POST'])
@admin_required
def new_creature():
    form = CreatureForm()
    if form.validate_on_submit():
        new_creature = Creature(
            name=form.name.data,
            rarity=form.rarity.data,
            description=form.description.data, 
            image=form.image.data or None,
            probability=form.probability.data,
        )
        db.session.add(new_creature)
        db.session.commit()
        flash(f'Creature "{new_creature.name}" added.', 'success')
        return redirect(url_for('admin_creatures'))
    return render_template('admin_creatures_form.html', form=form, title='Add New Creature')

@app.route('/admin/creatures/edit/<int:creature_id>', methods=['GET', 'POST'])
@admin_required
def edit_creature(creature_id):
    creature = db.session.get(Creature, creature_id)
    if not creature: 
        flash("Creature not found.", 'error')
        return redirect(url_for('admin_creatures'))
    
    form = CreatureForm(obj=creature)
    if form.validate_on_submit():
        form.populate_obj(creature) # This handles name, rarity, probability, and now description
        db.session.commit()
        flash(f'Creature updated.', 'success')
        return redirect(url_for('admin_creatures'))
    return render_template('admin_creatures_form.html', form=form, creature=creature, title='Edit Creature')

@app.route('/admin/creatures/delete/<int:creature_id>', methods=['POST'])
@admin_required
def delete_creature(creature_id):
    creature = db.session.get(Creature, creature_id)
    if creature:
        db.session.delete(creature)
        db.session.commit()
        flash(f"Creature '{creature.name}' deleted successfully.", 'success')
    return redirect(url_for('admin_creatures'))

# --- Admin CRUD (Missions) ---

@app.route('/admin/missions/new', methods=['GET', 'POST'])
@admin_required
def new_mission():
    form = MissionForm()
    if form.validate_on_submit():
        new_mission = Mission(
            name=form.name.data,
            description=form.description.data,
            target=form.target.data,
            reward=form.reward.data,
            order=form.order.data, 
        )
        db.session.add(new_mission)
        db.session.commit()
        flash(f'Mission added.', 'success')
        return redirect(url_for('admin_missions'))
    return render_template('admin_missions_form.html', form=form, title='Add New Mission')

@app.route('/admin/missions/edit/<int:mission_id>', methods=['GET', 'POST'])
@admin_required
def edit_mission(mission_id):
    mission = db.session.get(Mission, mission_id)
    if not mission: 
        flash("Mission not found.", 'error')
        return redirect(url_for('admin_missions'))
    
    form = MissionForm(obj=mission)
    if form.validate_on_submit():
        form.populate_obj(mission) 
        db.session.commit()
        flash(f'Mission updated.', 'success')
        return redirect(url_for('admin_missions'))
    return render_template('admin_missions_form.html', form=form, mission=mission, title='Edit Mission')

@app.route('/admin/missions/delete/<int:mission_id>', methods=['POST'])
@admin_required
def delete_mission(mission_id):
    mission = db.session.get(Mission, mission_id)
    if mission:
        db.session.delete(mission)
        db.session.commit()
        flash(f"Mission '{mission.name}' deleted successfully.", 'success')
    return redirect(url_for('admin_missions'))


# --- Database Initialization ---

if __name__ == '__main__':
    from seeds import initialize_default_data, create_default_admin

    with app.app_context():
        db.create_all()
        initialize_default_data()
        create_default_admin()

    app.run(debug=True)