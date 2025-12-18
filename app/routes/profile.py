from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.database import db
from app.models import User
from app.forms.forms import ProfileForm
from app.services.user_service import UserService

profile_bp = Blueprint('profile', __name__)


def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Display and update user profile."""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.auth_page'))
    
    form = ProfileForm(obj=user)
    
    if form.validate_on_submit():
        user.avatar = form.avatar.data
        user.bio = form.bio.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.profile'))
    
    user_data = UserService.get_user_data(user)
    
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