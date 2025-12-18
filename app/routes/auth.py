from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db
from app.models import User
from app.forms.forms import LoginForm, RegisterForm, ForgotPasswordForm

auth_bp = Blueprint('auth', __name__)

def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


@auth_bp.route('/auth')
def auth_page():
    """Display authentication page with login/register/forgot password forms."""
    if get_current_user():
        return redirect(url_for('game.home'))
    
    login_form = LoginForm()
    register_form = RegisterForm()
    forgot_form = ForgotPasswordForm()
    
    section = request.args.get('section', 'login')
    
    return render_template('auth.html', 
                           initial_section=section,
                           login_form=login_form,
                           register_form=register_form,
                           forgot_form=forgot_form)


@auth_bp.route('/login', methods=['POST']) 
def login():
    """Handle user login."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.user_id 
            session['role'] = user.role 
            
            flash(f'Welcome, {user.username}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.admin_creatures'))
            else:
                return redirect(url_for('game.home'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.auth_page', login_failed=True))
    
    return redirect(url_for('auth.auth_page'))


@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration."""
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.auth_page', section='register'))
        
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data, 
            password_hash=hashed_password,
            role='user'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.auth_page'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{error}", 'error')
            
    return redirect(url_for('auth.auth_page', section='register'))


@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    """Handle password reset."""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully. Please log in.', 'success')
            return redirect(url_for('auth.auth_page'))
        else:
            flash('Username not found.', 'error')
            
    return redirect(url_for('auth.auth_page', section='forgot'))


@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user_id', None)
    session.pop('role', None) 
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.auth_page'))