import random
from app.database import db
from app.models import Creature, UserCreature

class GachaService:
    @staticmethod
    def apply_pity_system(user, creatures):
        """Apply pity system logic to guarantee drops"""
        if user.legendary_pity >= 79:
            legendaries = [c for c in creatures if c.rarity == 'legendary']
            if legendaries:
                user.legendary_pity = 0
                user.pity_counter = 0
                return random.choice(legendaries)
        
        if user.pity_counter >= 9:
            epics = [c for c in creatures if c.rarity == 'epic']
            if epics:
                user.pity_counter = 0
                return random.choice(epics)
        
        return None
    
    @staticmethod
    def pull_creature(user, pull_type='single'):
        """Execute a gacha pull"""
        cost = 50 if pull_type == 'multi' else 5
        if user.coins < cost:
            return {'success': False, 'message': 'Not enough coins!'}
        
        user.coins -= cost
        user.pulls += (10 if pull_type == 'multi' else 1)
        
        creatures = Creature.query.all()
        if not creatures:
            return {'success': False, 'message': 'No creatures in database'}
        
        results = []
        loops = 10 if pull_type == 'multi' else 1
        total_prob = sum(c.probability for c in creatures)
        
        if total_prob <= 0:
            return {'success': False, 'message': 'All creatures have zero probability'}
        
        for i in range(loops):
            pity_creature = GachaService.apply_pity_system(user, creatures)
            
            if pity_creature:
                selected = pity_creature
            else:
                rand = random.uniform(0, total_prob)
                curr, selected = 0, None
                for c in creatures:
                    curr += c.probability
                    if rand <= curr:
                        selected = c
                        break
                if not selected:
                    selected = creatures[-1]
                
                user.pity_counter += 1
                user.legendary_pity += 1
                
                if selected.rarity in ['epic', 'legendary']:
                    user.pity_counter = 0
                if selected.rarity == 'legendary':
                    user.legendary_pity = 0
            
            db.session.add(UserCreature(
                user_id=user.user_id,
                creature_id=selected.creature_id
            ))
            
            results.append({
                'name': selected.name,
                'rarity': selected.rarity,
                'image': selected.image,
                'pity': pity_creature is not None
            })
        
        db.session.commit()
        
        return {
            'success': True,
            'creature': results[0] if pull_type == 'single' else None,
            'creatures': results,
            'coins': user.coins,
            'pity_counter': user.pity_counter,
            'legendary_pity': user.legendary_pity
        }