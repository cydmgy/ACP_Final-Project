from app.models import User, Creature, Mission
from app.database import db
from werkzeug.security import generate_password_hash

def initialize_default_data():
    """Initialize default creatures and missions if they don't exist."""
    if not Creature.query.first(): 
        print("Initializing default creatures...")
        
        defaults = [
        # Common - 60% total (0.075 each = 8 creatures)
        {"name": "Pebbleback Shrimp", "rarity": "common", "image": "images/Pebbleback_Shrimp.png", "probability": 0.075, "description": "A timid shrimp whose shell is covered in pebble-like lumps, blending perfectly with the seafloor. It hops between rock beds and coral rubble, making it nearly invisible unless it moves."},
        {"name": "Lantern Dartfish", "rarity": "common", "image": "images/Lantern_Dartfish.png", "probability": 0.075, "description": "A small, quick fish with a luminous tail used to communicate with its school. It darts around like a tiny underwater firefly, leaving faint trails of golden light behind it."},
        {"name": "Shellscale Urchin", "rarity": "common", "image": "images/Shellscale_Urchin.png", "probability": 0.075, "description": "A rotund urchin with patterned armor plates resembling seashell mosaics. Its spines are soft enough to be harmless but tough enough to deter predators."},
        {"name": "Duskreef Snapper", "rarity": "common", "image": "images/Duskreef_Snapper.png", "probability": 0.075, "description": "A dull grey fish that feeds on algae and small reef organisms. Its muted colors help it blend into underwater cliffs, making it a common but essential species in deep reef ecosystems."},
        {"name": "Driftcurrent Jelly", "rarity": "common", "image": "images/Driftcurrent_Jelly.png", "probability": 0.075, "description": "A small, delicate jellyfish carried by deep-sea currents. Its soft glow gently flickers, and it provides light for tiny creatures that travel with it."},
        {"name": "Crumbleclaw Hermit", "rarity": "common", "image": "images/Crumbleclaw_Hermit.png", "probability": 0.075, "description": "A hermit crab known for occupying cracked, broken shells or even small pieces of debris. Its mismatched armor gives it a clumsy but charming appearance."},
        {"name": "Spotted Gloom Guppy", "rarity": "common", "image": "images/Spotted_Gloom_Guppy.png", "probability": 0.075, "description": "A tiny, cave-dwelling fish with murky spots along its body. It moves in tight schools and often disappears into shadowy clusters of algae."},
        {"name": "Murkfin Skate", "rarity": "common", "image": "images/Murkfin_Skate.png", "probability": 0.075, "description": "A flat, wide skate with muddy grey coloration. It glides gently across the seafloor, kicking up little clouds of sediment wherever it goes."},
    
        # Rare - 30% total (0.05 each = 6 creatures)
        {"name": "Ironclaw Crustadon", "rarity": "rare", "image": "images/Ironclaw_Crustadon.png", "probability": 0.05, "description": "A heavily armored crab-beast with steely claws forged through natural mineral absorption. Its shell is patterned with metallic ridges and dents from years of territorial duels. Ironclaw Crustadon uses its brute strength to shatter coral formations and carve out dens."},
        {"name": "Glowfin Archerfish", "rarity": "rare", "image": "images/Glowfin_Archerfish.png", "probability": 0.05, "description": "A sleek, turquoise fish with glowing vein-like patterns running along its fins. It fires pressurized streams of luminous water with sniper accuracy, often used to blind predators or signal allies in the dark. Its light patterns pulse in rhythmic signals only its species can decode."},
        {"name": "Obsidian Fang Moray", "rarity": "rare", "image": "images/Obsidian_Fang_Moray.png", "probability": 0.05, "description": "A pitch-black eel with glistening, transparent fangs sharper than surgical blades. Its body is dotted with faint violet bioluminescence, making it look like a shadow streaking through the abyss. It strikes from tight caves, dragging prey into unseen tunnels."},
        {"name": "Deepwater Jelly Harrow", "rarity": "rare", "image": "images/Deepwater_Jelly_Harrow.png", "probability": 0.05, "description": "A floating, translucent jellyfish with tendrils that flicker like dying candle flames. Its stingers produce ghostly blue sparks which scramble the senses of nearby creatures. Many divers report hallucinations after encounters, believing it to be a spirit of the deep."},
        {"name": "Stormback Anemone Worm", "rarity": "rare", "image": "images/Stormback_Anemone_Worm.png", "probability": 0.05, "description": "A segmented worm covered in tiny electric anemones that discharge bolts of bioelectric energy when threatened. Its back glows with green lightning patterns, and its movements send crackling sparks through the water. It often coils itself into rock crevices, turning into a living taser trap."},
        {"name": "Echo Shriek Ray", "rarity": "rare", "image": "images/Echo_Shriek_Ray.png", "probability": 0.05, "description": "A disc-shaped ray with two glowing sound-pulse organs on its sides. It emits sonic bursts that distort water, stunning prey or sending warning blasts across long distances. When gliding, the patterns on its wings ripple like sound waves."},
    
        # Epic - 9% total (0.0225 each = 4 creatures)
        {"name": "Titan Lanternjaw", "rarity": "epic", "image": "images/Titan_Lanternjaw.png", "probability": 0.0225, "description": "A monstrous anglerfish with a molten-core lantern protruding from its forehead. Its jaw splits impossibly wide, lined with serrated metallic fangs that vibrate when hunting. Titan Lanternjaw lights up deep trenches with a fiery glow, luring prey into its shadowy maw. Entire ecosystems flee at the sight of its burning beacon."},
        {"name": "Abyssal Goreback Turtle", "rarity": "epic", "image": "images/Abyssal_Goreback_Turtle.png", "probability": 0.0225, "description": "A massive turtle armored with volcanic obsidian plates. Cracks between its shell glow like flowing magma, releasing bursts of steam with every movement. Despite its slow gait, its bite can shear through reinforced submersible hulls. Its shell is often mistaken for underwater mountains, leading explorers dangerously close."},
        {"name": "Subzero Siren Eel", "rarity": "epic", "image": "images/Subzero_Siren_Eel.png", "probability": 0.0225, "description": "A long, serpentine eel coated in crystalline frost. It hums haunting melodies that travel through freezing currents, luring creatures closer before encasing them in ice. Its glowing blue fins resemble drifting icicles. When it swims, trails of cold mist spiral around it, instantly chilling the water."},
        {"name": "Riftshadow Krakenling", "rarity": "epic", "image": "images/Riftshadow_Krakenling.png", "probability": 0.0225, "description": "A young kraken born from the dark cracks of oceanic rifts. Its tentacles are surrounded by clouds of smoke-like ink that it shapes into phantom arms to confuse predators. Though smaller than a true kraken, the Krakenling can stretch its limbs unnaturally far and squeeze into tight crevices, ambushing anything that wanders too close."},
    
        # Legendary - 1% total (0.005 each = 2 creatures) 
        {"name": "Abyssal Varonis Coraliath", "rarity": "legendary", "image": "images/Abyssal_Varonis_Coraliath.png", "probability": 0.005, "description": "A titanic serpent draped in crystalline coral clusters that pulse with neon blues and purples. Its scales refract light like deep-sea gemstones, creating dazzling auroras in pitch-black waters. Old sailors claim the Leviacoral forms coral crowns from the ruins of sunken cities, marking its territory. When threatened, it emits a blinding flash that paralyzes anything nearby."},
        {"name": "Caelorynth Voidshroud", "rarity": "legendary", "image": "images/Caelorynth_Voidshroud.png", "probability": 0.005, "description": "A majestic manta ray with wings that appear half-ethereal and half-liquid. Its body fades into transparency, as if slipping between dimensions. The Void Phantom Ray glides silently, leaving trails of shimmering dust like tiny stars. It absorbs surrounding energy to cloak itself, and legends say it can appear beside lost divers as a final guide home."},
        ]
        
        for c in defaults:
            db.session.add(Creature(**c))
    
    if not Mission.query.first(): 
        print("Initializing default missions...")
        
        defaults = [
            {"name": "First Steps", "description": "Click 10 times", "target": 10, "reward": 10},
            {"name": "Getting Started", "description": "Click 50 times", "target": 50, "reward": 25},
        ]
        
        for m in defaults:
             db.session.add(Mission(order=defaults.index(m)+1, **m))
            
    db.session.commit()
    
def create_default_admin():
    """Create default admin user if it doesn't exist."""
    if not User.query.filter_by(username='admin').first():
        print("Creating default admin...")
        admin = User(
            username='admin',
            password_hash=generate_password_hash("admin123"),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()