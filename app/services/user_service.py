from app.models import User, UserCreature, UserMission, Creature

class UserService:
    @staticmethod
    def get_user_data(user):
        """Get all user data formatted for the frontend"""
        completed_missions = UserMission.query.filter_by(
            user_id=user.user_id,
            completed=True
        ).all()
        completed_mission_ids = [m.mission_id for m in completed_missions]
        
        inventory_creatures = UserCreature.query.filter_by(
            user_id=user.user_id
        ).join(Creature).all()
        
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