from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from functools import wraps
import json
from app.database import db
from app.models import User, Creature, Mission
from app.forms.forms import CreatureForm, MissionForm

admin_bp = Blueprint('admin', __name__)


def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


def admin_required(f):
    """Decorator to check if the current user has the 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin':
            flash("Access denied. Admin privileges required.", 'error')
            return redirect(url_for('game.home')) 
        return f(*args, **kwargs)
    return decorated_function


# ============= CREATURE MANAGEMENT =============

@admin_bp.route('/creatures')
@admin_required
def admin_creatures():
    """Display all creatures for admin management."""
    creatures = Creature.query.order_by(Creature.rarity, Creature.name).all()
    return render_template('admin_creatures.html', creatures=creatures)


@admin_bp.route('/creatures/new', methods=['GET', 'POST'])
@admin_required
def new_creature():
    """Create a new creature."""
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
        return redirect(url_for('admin.admin_creatures'))
    
    return render_template('admin_creatures_form.html', 
                         form=form, 
                         title='Add New Creature')


@admin_bp.route('/creatures/edit/<int:creature_id>', methods=['GET', 'POST'])
@admin_required
def edit_creature(creature_id):
    """Edit an existing creature."""
    creature = db.session.get(Creature, creature_id)
    if not creature: 
        flash("Creature not found.", 'error')
        return redirect(url_for('admin.admin_creatures'))
    
    form = CreatureForm(obj=creature)
    if form.validate_on_submit():
        form.populate_obj(creature)
        db.session.commit()
        flash(f'Creature updated.', 'success')
        return redirect(url_for('admin.admin_creatures'))
    
    return render_template('admin_creatures_form.html', 
                         form=form, 
                         creature=creature, 
                         title='Edit Creature')


@admin_bp.route('/creatures/delete/<int:creature_id>', methods=['POST'])
@admin_required
def delete_creature(creature_id):
    """Delete a creature."""
    creature = db.session.get(Creature, creature_id)
    if creature:
        db.session.delete(creature)
        db.session.commit()
        flash(f"Creature '{creature.name}' deleted successfully.", 'success')
    return redirect(url_for('admin.admin_creatures'))


# ============= MISSION MANAGEMENT =============

@admin_bp.route('/missions')
@admin_required
def admin_missions():
    """Display all missions for admin management."""
    missions = Mission.query.order_by(Mission.order).all()
    return render_template('admin_missions.html', missions=missions)


@admin_bp.route('/missions/new', methods=['GET', 'POST'])
@admin_required
def new_mission():
    """Create a new mission."""
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
        return redirect(url_for('admin.admin_missions'))
    
    return render_template('admin_missions_form.html', 
                         form=form, 
                         title='Add New Mission')


@admin_bp.route('/missions/edit/<int:mission_id>', methods=['GET', 'POST'])
@admin_required
def edit_mission(mission_id):
    """Edit an existing mission."""
    mission = db.session.get(Mission, mission_id)
    if not mission: 
        flash("Mission not found.", 'error')
        return redirect(url_for('admin.admin_missions'))
    
    form = MissionForm(obj=mission)
    if form.validate_on_submit():
        form.populate_obj(mission) 
        db.session.commit()
        flash(f'Mission updated.', 'success')
        return redirect(url_for('admin.admin_missions'))
    
    return render_template('admin_missions_form.html', 
                         form=form, 
                         mission=mission, 
                         title='Edit Mission')


@admin_bp.route('/missions/delete/<int:mission_id>', methods=['POST'])
@admin_required
def delete_mission(mission_id):
    """Delete a mission."""
    mission = db.session.get(Mission, mission_id)
    if mission:
        db.session.delete(mission)
        db.session.commit()
        flash(f"Mission '{mission.name}' deleted successfully.", 'success')
    return redirect(url_for('admin.admin_missions'))


@admin_bp.route('/missions/export')
@admin_required
def export_missions():
    """Export all missions to JSON."""
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


@admin_bp.route('/missions/import', methods=["POST"])
@admin_required
def import_missions():
    """Import missions from JSON file."""
    file = request.files.get("json_file")
    if not file:
        flash("No file uploaded", "error")
        return redirect(url_for("admin.admin_missions"))
    
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
    return redirect(url_for("admin.admin_missions"))