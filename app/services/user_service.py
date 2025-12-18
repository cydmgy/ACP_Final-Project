from app.models import User, UserCreature, UserMission, Creature, Announcement, UserAnnouncement
from app.database import db  

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
        
        # Check for unread announcements
        active_announcements_count = Announcement.query.filter_by(
            is_active=True
        ).count()
        
        read_announcements_count = UserAnnouncement.query.filter_by(
            user_id=user.user_id
        ).count()
        
        has_unread_announcements = active_announcements_count > read_announcements_count
        
        return {
            'clicks': user.clicks,
            'coins': user.coins,
            'pulls': user.pulls,
            'completed_missions': completed_mission_ids,
            'inventory': inventory,
            'has_unread_announcements': has_unread_announcements
        }
    
    @staticmethod
    def get_active_announcements(user_id):
        """Get all active announcements with read status"""
        active_announcements = Announcement.query.filter_by(
            is_active=True
        ).order_by(Announcement.created_at.desc()).all()
        
        read_announcements = UserAnnouncement.query.filter_by(
            user_id=user_id
        ).all()
        read_announcement_ids = [ra.announcement_id for ra in read_announcements]
        
        announcements = []
        for announcement in active_announcements:
            announcements.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'created_at': announcement.created_at.isoformat() if announcement.created_at else None,
                'is_read': announcement.id in read_announcement_ids
            })
        
        return announcements
    
    @staticmethod
    def mark_announcement_read(user_id, announcement_id):
        """Mark an announcement as read for a user"""
        # Check if already marked as read
        existing = UserAnnouncement.query.filter_by(
            user_id=user_id,
            announcement_id=announcement_id
        ).first()
        
        if not existing:
            user_announcement = UserAnnouncement(
                user_id=user_id,
                announcement_id=announcement_id
            )
            db.session.add(user_announcement)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_announcements_read(user_id):
        """Mark all active announcements as read for a user"""
        active_announcements = Announcement.query.filter_by(
            is_active=True
        ).all()
        
        count = 0
        for announcement in active_announcements:
            existing = UserAnnouncement.query.filter_by(
                user_id=user_id,
                announcement_id=announcement.id
            ).first()
            
            if not existing:
                user_announcement = UserAnnouncement(
                    user_id=user_id,
                    announcement_id=announcement.id
                )
                db.session.add(user_announcement)
                count += 1
        
        if count > 0:
            db.session.commit()
        
        return count
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread announcements"""
        active_announcements_count = Announcement.query.filter_by(
            is_active=True
        ).count()
        
        read_announcements_count = UserAnnouncement.query.filter_by(
            user_id=user_id
        ).count()
        
        return max(0, active_announcements_count - read_announcements_count)