import random
from app.database import db
from app.models import Creature, UserCreature, Banner, UserBannerPity

class GachaService:
    @staticmethod
    def get_user_pity(user_id, banner_id=None):
        """Get or create pity record for a specific banner (None = standard)"""
        pity_record = UserBannerPity.query.filter_by(
            user_id=user_id, 
            banner_id=banner_id
        ).first()
        
        if not pity_record:
            pity_record = UserBannerPity(
                user_id=user_id, 
                banner_id=banner_id,
                pity_counter=0,
                legendary_pity=0
            )
            db.session.add(pity_record)
            # We don't commit here, it will be committed with the main transaction
        
        return pity_record

    @staticmethod
    def apply_pity_system(pity_record, creatures):
        """Apply pity system logic to guarantee drops using banner-specific pity"""
        if pity_record.legendary_pity >= 79:
            legendaries = [c for c in creatures if c.rarity == 'legendary']
            if legendaries:
                pity_record.legendary_pity = 0
                pity_record.pity_counter = 0
                return random.choice(legendaries)
        
        if pity_record.pity_counter >= 9:
            epics = [c for c in creatures if c.rarity == 'epic']
            if epics:
                pity_record.pity_counter = 0
                return random.choice(epics)
        
        return None
    
    @staticmethod
    def pull_creature(user, pull_type='single', banner_id=None):
        """Execute a gacha pull with banner logic"""
        cost = 50 if pull_type == 'multi' else 5
        if user.coins < cost:
            return {'success': False, 'message': 'Not enough coins!'}
        
        user.coins -= cost
        user.pulls += (10 if pull_type == 'multi' else 1)
        
        # 1. Base Pool: Active + Not Limited
        base_creatures = Creature.query.filter_by(active=True, is_limited=False).all()
        
        # 2. Add Featured/Limited Creatures if Banner is selected
        featured_creatures = []
        featured_multipliers = {}
        
        if banner_id:
            banner = db.session.get(Banner, banner_id)
            if banner and banner.active:
                for fc in banner.featured_creatures:
                     # Add to pool even if it's already there (will be deduplicated or handled via probs)
                     # But mostly we want to ensure limited creatures are ADDED.
                     # However, a cleaner way is:
                     # If fc.creature is limited, add it.
                     # If fc.creature is standard, it's already in base_creatures.
                     # We track multipliers.
                     featured_multipliers[fc.creature_id] = fc.rate_multiplier
                     if fc.creature not in base_creatures:
                         featured_creatures.append(fc.creature)
        
        # Combine pools
        # Use a dictionary to handle uniqueness
        pool_dict = {c.creature_id: c for c in base_creatures}
        for c in featured_creatures:
            pool_dict[c.creature_id] = c
            
        creatures = list(pool_dict.values())
        
        if not creatures:
            return {'success': False, 'message': 'No creatures available'}
            
        # Calculate probabilities
        creature_probs = {}
        for c in creatures:
            base_prob = c.probability
            mult = featured_multipliers.get(c.creature_id, 1.0)
            creature_probs[c.creature_id] = base_prob * mult
        
        # Get Pity Record
        pity_record = GachaService.get_user_pity(user.user_id, banner_id)
        
        results = []
        loops = 10 if pull_type == 'multi' else 1
        total_prob = sum(creature_probs.values())
        
        if total_prob <= 0:
            return {'success': False, 'message': 'All creatures have zero probability'}
        
        for i in range(loops):
            pity_creature = GachaService.apply_pity_system(pity_record, creatures)
            
            if pity_creature:
                selected = pity_creature
            else:
                rand = random.uniform(0, total_prob)
                curr, selected = 0, None
                for c in creatures:
                    curr += creature_probs[c.creature_id]
                    if rand <= curr:
                        selected = c
                        break
                if not selected:
                    selected = creatures[-1]
                
                pity_record.pity_counter += 1
                pity_record.legendary_pity += 1
                
                if selected.rarity in ['epic', 'legendary']:
                    pity_record.pity_counter = 0
                if selected.rarity == 'legendary':
                    pity_record.legendary_pity = 0
            
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
            'pity_counter': pity_record.pity_counter,
            'legendary_pity': pity_record.legendary_pity
        }