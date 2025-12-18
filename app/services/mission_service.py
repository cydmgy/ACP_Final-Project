from datetime import datetime
from app.database import db
from app.models import Mission, UserMission

class MissionService:
    @staticmethod
    def get_all_missions():
        return Mission.query.order_by(Mission.order).all()
    
    @staticmethod
    def check_and_complete_missions(user, current_clicks):
        """Check if any missions should be completed"""
        coins_earned = 0
        
        for mission in MissionService.get_all_missions():
            completed = UserMission.query.filter_by(
                user_id=user.user_id,
                mission_id=mission.mission_id,
                completed=True
            ).first()
            
            if not completed and current_clicks >= mission.target:
                new_completion = UserMission(
                    user_id=user.user_id,
                    mission_id=mission.mission_id,
                    completed=True,
                    completed_at=datetime.utcnow()
                )
                db.session.add(new_completion)
                coins_earned += mission.reward
        
        return coins_earned