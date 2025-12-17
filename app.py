from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
import random, json
from functools import wraps
from datetime import datetime

from models import db, User, Creature, Mission, UserCreature, UserMission
from forms import LoginForm, RegisterForm, ForgotPasswordForm, CreatureForm, MissionForm, ProfileForm

app = Flask(__name__)
app.secret_key = 'secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sea_life_gacha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
        if not user or user.role != 'admin':
            flash("Access denied. Admin privileges required.", 'error')
            return redirect(url_for('home')) 
        return f(*args, **kwargs)
    return decorated_function

def get_all_missions():
    return Mission.query.order_by(Mission.order).all()

def apply_pity_system(user, creatures):
    """Apply pity system logic to guarantee drops"""
    # Guaranteed legendary every 80 pulls
    if user.legendary_pity >= 79:
        legendaries = [c for c in creatures if c.rarity == 'legendary']
        if legendaries:
            user.legendary_pity = 0
            user.pity_counter = 0
            return random.choice(legendaries)
    
    # Guaranteed epic every 10 pulls
    if user.pity_counter >= 9:
        epics = [c for c in creatures if c.rarity == 'epic']
        if epics:
            user.pity_counter = 0
            return random.choice(epics)
    
    return None

# --- Authentication Routes ---

@app.route('/auth')
def auth():
    if get_current_user():
        return redirect(url_for('home'))
    
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

# --- Profile Routes ---

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth'))
    
    form = ProfileForm(obj=user)
    
    if form.validate_on_submit():
        user.avatar = form.avatar.data
        user.bio = form.bio.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    user_data = get_user_data(user)
    
    # Calculate achievements
    total_creatures = len(user_data['inventory'])
    rare_count = len([c for c in user_data['inventory'] if c['rarity'] == 'rare'])
    epic_count = len([c for c in user_data['inventory'] if c['rarity'] == 'epic'])
    legendary_count = len([c for c in user_data['inventory'] if c['rarity'] == 'legendary'])
    
    return render_template('profile.html',
                         form=form,
                         user=user,
                         total_creatures=total_creatures,
                         rare_count=rare_count,
                         epic_count=epic_count,
                         legendary_count=legendary_count,
                         completed_missions=len(user_data['completed_missions']))

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
    return render_template('gacha.html', 
                         coins=user.coins,
                         pity_counter=user.pity_counter,
                         legendary_pity=user.legendary_pity)

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
        
        for i in range(loops):
            # Check pity system first
            pity_creature = apply_pity_system(user, creatures)
            
            if pity_creature:
                selected = pity_creature
            else:
                # Normal random selection
                rand = random.uniform(0, total_prob)
                curr, selected = 0, None
                for c in creatures:
                    curr += c.probability
                    if rand <= curr: selected = c; break
                if not selected: selected = creatures[-1]
                
                # Update pity counters
                user.pity_counter += 1
                user.legendary_pity += 1
                
                # Reset counters if epic or legendary pulled
                if selected.rarity in ['epic', 'legendary']:
                    user.pity_counter = 0
                if selected.rarity == 'legendary':
                    user.legendary_pity = 0
            
            db.session.add(UserCreature(user_id=user.user_id, creature_id=selected.creature_id))
            results.append({
                'name': selected.name, 
                'rarity': selected.rarity, 
                'image': selected.image,
                'pity': pity_creature is not None
            })
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'creature': results[0] if pull_type=='single' else None, 
            'creatures': results, 
            'coins': user.coins,
            'pity_counter': user.pity_counter,
            'legendary_pity': user.legendary_pity
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/inventory')
def inventory():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth'))

    filter_value = request.args.get("filter", "all")

    full_inventory = get_user_data(user)['inventory']
    
    filtered_inventory = full_inventory
    if filter_value != "all":
        filtered_inventory = list(filter(lambda c: c["rarity"].lower() == filter_value.lower(), full_inventory))

    total_count = len(full_inventory)
    common_count = len([c for c in full_inventory if c["rarity"].lower() == "common"])
    rare_count = len([c for c in full_inventory if c["rarity"].lower() == "rare"])
    epic_count = len([c for c in full_inventory if c["rarity"].lower() == "epic"])
    legendary_count = len([c for c in full_inventory if c["rarity"].lower() == "legendary"])

    return render_template(
        'inventory.html',
        inventory=filtered_inventory,
        full_inventory=full_inventory,
        selected_filter=filter_value,
        total_count=total_count,
        common_count=common_count,
        rare_count=rare_count,
        epic_count=epic_count,
        legendary_count=legendary_count
    )
    
# --- Admin Routes ---

@app.route('/admin/creatures')
@admin_required
def admin_creatures():
    creatures = Creature.query.order_by(Creature.rarity, Creature.name).all()
    return render_template('admin_creatures.html', creatures=creatures)

@app.route('/admin/missions')
@admin_required
def admin_missions():
    return render_template('admin_missions.html', missions=Mission.query.order_by(Mission.order).all())

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
        form.populate_obj(creature)
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

@app.route("/missions/export")
@admin_required
def export_missions():
    missions = Mission.query.order_by(Mission.order).all()
    data = []
    for m in missions:
        data.append({
            "name": m.name,
            "description": m.description,
            "target": m.target,
            "reward": m.reward,
            "order": m.order
        })
    json_data = json.dumps(data, indent=4)
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=missions.json"}
    )

@app.route("/missions/import", methods=["POST"])
@admin_required
def import_missions():
    file = request.files.get("json_file")
    if not file:
        flash("No file uploaded", "error")
        return redirect(url_for("admin_missions"))
    data = json.load(file)
    for item in data:
        mission = Mission(
            name=item.get("name"),
            description=item.get("description"),
            target=item.get("target"),
            reward=item.get("reward"),
            order=item.get("order")
        )
        db.session.add(mission)
    db.session.commit()
    flash("Missions imported successfully!", "success")
    return redirect(url_for("admin_missions"))

if __name__ == '__main__':
    from seeds import initialize_default_data, create_default_admin

    with app.app_context():
        db.create_all()
        initialize_default_data()
        create_default_admin()

    app.run(debug=True)