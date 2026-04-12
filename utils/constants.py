"""
AETHER HARVEST - Constants & Configuration
"""


WIDTH, HEIGHT = 1280, 720
TITLE = "AETHER HARVEST"
FPS = 60
TILE_SIZE = 64


LAYER_WORLD      = 0
LAYER_ENTITIES   = 1
LAYER_PARTICLES  = 2
LAYER_UI         = 3
LAYER_OVERLAY    = 4


FRICTION         = 0.82
PLAYER_SPEED     = 220
PLAYER_DASH_SPEED = 700
DASH_DURATION    = 0.15
DASH_COOLDOWN    = 0.8



C_BG             = (8,   6,  18)
C_BG2            = (14,  11, 32)
C_PANEL          = (18,  14, 42)
C_PANEL_BORDER   = (55,  40, 120)

C_PRIMARY        = (120,  60, 255)  
C_SECONDARY      = (60,  220, 200)  
C_ACCENT         = (255, 180,  50)   
C_DANGER         = (255,  70,  90)   
C_SUCCESS        = (80,  255, 140)   

C_WHITE          = (240, 235, 255)
C_GRAY           = (100,  90, 130)
C_DARK_GRAY      = (40,   35,  60)


ORE_TYPES = {
    "aether":   {"color": (120, 60, 255), "glow": (180, 100, 255), "value": 1,  "rarity": 60},
    "lumite":   {"color": (60, 220, 200), "glow": (100, 255, 240), "value": 3,  "rarity": 25},
    "solaris":  {"color": (255, 180, 50),  "glow": (255, 220, 120), "value": 8,  "rarity": 12},
    "voidite":  {"color": (255, 70,  90),  "glow": (255, 130, 150), "value": 25, "rarity": 3},
}


UPGRADES = [
    {
        "id":    "pick_power",
        "name":  "Resonance Pick",
        "desc":  "Amplifies crystal extraction per strike",
        "icon":  "⚡",
        "base_cost": 15,
        "cost_scale": 1.6,
        "max_level": 20,
        "effect": "click_power +1 per level",
    },
    {
        "id":    "auto_harvest",
        "name":  "Drone Swarm",
        "desc":  "Autonomous aether collectors orbit the field",
        "icon":  "🤖",
        "base_cost": 40,
        "cost_scale": 1.8,
        "max_level": 15,
        "effect": "auto_income +2/sec per level",
    },
    {
        "id":    "ore_magnet",
        "name":  "Void Magnet",
        "desc":  "Rare ores spawn more frequently",
        "icon":  "🧲",
        "base_cost": 80,
        "cost_scale": 2.0,
        "max_level": 5,
        "effect": "rare_boost +15% per level",
    },
    {
        "id":    "warp_field",
        "name":  "Warp Field",
        "desc":  "Collect ores at extreme range",
        "icon":  "🌀",
        "base_cost": 120,
        "cost_scale": 2.2,
        "max_level": 5,
        "effect": "collect_range +40px per level",
    },
    {
        "id":    "crystal_echo",
        "name":  "Crystal Echo",
        "desc":  "Chain reactions multiply your harvest",
        "icon":  "💎",
        "base_cost": 200,
        "cost_scale": 2.5,
        "max_level": 8,
        "effect": "chain_chance +10% per level",
    },
    {
        "id":    "temporal_surge",
        "name":  "Temporal Surge",
        "desc":  "Slows time briefly after collecting voidite",
        "icon":  "⏱",
        "base_cost": 350,
        "cost_scale": 3.0,
        "max_level": 3,
        "effect": "time_slow on voidite collect",
    },
    {
        "id":    "aether_bolt",
        "name":  "Aether Bolt",
        "desc":  "Right-click to fire piercing energy bolts",
        "icon":  "✦",
        "base_cost": 50,
        "cost_scale": 1.8,
        "max_level": 10,
        "effect": "bolt dmg +5, speed +5% per level",
    },
    {
        "id":    "void_shield",
        "name":  "Void Shield",
        "desc":  "Regenerates HP slowly over time",
        "icon":  "🛡",
        "base_cost": 60,
        "cost_scale": 1.9,
        "max_level": 5,
        "effect": "regen +1 HP/sec per level",
    },
    {
        "id":    "phase_drive",
        "name":  "Phase Drive",
        "desc":  "Boosts movement and dash speed",
        "icon":  "🚀",
        "base_cost": 90,
        "cost_scale": 2.1,
        "max_level": 5,
        "effect": "speed +15% per level",
    },
    {
        "id":    "aether_lens",
        "name":  "Aether Lens",
        "desc":  "Vacuums nearby ores while moving",
        "icon":  "🔮",
        "base_cost": 180,
        "cost_scale": 2.3,
        "max_level": 4,
        "effect": "vacuum radius +50px per level",
    },
]


ENEMY_SPAWN_INTERVAL = 18.0  
ENEMY_TYPES = {
    "void_wisp": {
        "color":  (180, 80, 255),
        "speed":  90,
        "hp":     20,
        "damage": 5,
        "reward": 5,
        "size":   14,
    },
    "crystal_golem": {
        "color":  (100, 200, 180),
        "speed":  45,
        "hp":     80,
        "damage": 15,
        "reward": 20,
        "size":   22,
    },
    "void_hunter": {
        "color":  (255, 80, 100),
        "speed":  130,
        "hp":     35,
        "damage": 10,
        "reward": 12,
        "size":   16,
    },
}

SAVE_PATH = "data/save.json"
