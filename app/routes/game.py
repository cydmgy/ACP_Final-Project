from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.database import db
from app.models import User, Banner
from app.services.user_service import UserService
from app.services.gacha_service import GachaService
from app.services.mission_service import MissionService

game_bp = Blueprint('game', __name__)


def get_current_user():
    """Retrieves the currently logged-in user object."""
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


@game_bp.route('/')
def home():
    """Main home page with click button and missions."""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.auth_page'))
    
    user_data = UserService.get_user_data(user)
    
    return render_template('home.html',
        username=user.username,
        clicks=user_data['clicks'],
        coins=user.coins,
        missions=MissionService.get_all_missions(),
        completed_missions=user_data['completed_missions'],
        pulls=user.pulls,
        has_unread_announcements=user_data['has_unread_announcements'])


@game_bp.route('/click', methods=['POST'])
def handle_click():
    """Handle click button action."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user.clicks += 1
        
        # Every 5 clicks gives 1 coin
        if user.clicks % 5 == 0:
            user.coins += 1000
        
        # Check and complete missions
        coins_earned = MissionService.check_and_complete_missions(user, user.clicks)
        
        if coins_earned > 0:
            user.coins += coins_earned
        
        db.session.commit()
        
        return jsonify({
            'clicks': user.clicks,
            'coins': user.coins,
            'coins_earned': coins_earned
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@game_bp.route('/gacha')
def gacha():
    """Gacha pull page."""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.auth_page'))
    
    active_banners = Banner.query.filter_by(active=True).all()
    
    # Get standard banner pity stats by default
    pity_record = GachaService.get_user_pity(user.user_id, None)
    
    return render_template('gacha.html',
        coins=user.coins,
        pity_counter=pity_record.pity_counter,
        legendary_pity=pity_record.legendary_pity,
        banners=active_banners)


@game_bp.route('/pull_gacha', methods=['POST'])
def pull_gacha():
    """Handle gacha pull (single or multi)."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        pull_type = data.get('type', 'single')
        banner_id = data.get('banner_id')
        
        # Validate banner_id (empty string -> None)
        if not banner_id:
            banner_id = None
        
        result = GachaService.pull_creature(user, pull_type, banner_id)
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        # Log the error for debugging (print to console)
        print(f"Gacha Error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@game_bp.route('/inventory')
def inventory():
    """Display user's creature inventory."""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.auth_page'))
    
    filter_value = request.args.get("filter", "all")
    full_inventory = UserService.get_user_data(user)['inventory']
    
    # Filter inventory
    filtered_inventory = full_inventory
    if filter_value != "all":
        filtered_inventory = [
            c for c in full_inventory 
            if c["rarity"].lower() == filter_value.lower()
        ]
    
    # Calculate counts
    counts = {
        'total_count': len(full_inventory),
        'common_count': len([c for c in full_inventory if c["rarity"].lower() == "common"]),
        'rare_count': len([c for c in full_inventory if c["rarity"].lower() == "rare"]),
        'epic_count': len([c for c in full_inventory if c["rarity"].lower() == "epic"]),
        'legendary_count': len([c for c in full_inventory if c["rarity"].lower() == "legendary"])
    }
    
    return render_template('inventory.html',
        inventory=filtered_inventory,
        full_inventory=full_inventory,
        selected_filter=filter_value,
        **counts)


@game_bp.route('/update_time', methods=['POST'])
def update_time():
    """Update user's time spent playing."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        seconds = data.get('seconds', 0)
        user.time_spent += seconds
        db.session.commit()
        return jsonify({'success': True, 'total_time': user.time_spent})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@game_bp.route('/get_pity')
def get_pity():
    """Get pity stats for a specific banner (or standard)"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    banner_id = request.args.get('banner_id')
    # Treat empty string as None
    if not banner_id:
        banner_id = None
    
    pity_record = GachaService.get_user_pity(user.user_id, banner_id)
    
    return jsonify({
        'success': True,
        'pity_counter': pity_record.pity_counter,
        'legendary_pity': pity_record.legendary_pity
    })