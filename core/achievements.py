"""

Achievements system fo Aether Harvest.
Tracks stats  and unclocks badges.
"""

import json, os 
from utils.constants import C_ACCENT, C_SUCCESS, C_DANGER, C_SECONDARY

ACHIEVEMENT_FILE  = "data/achievements.json"


ACHIEVEMENTS = [
    # Harvesting
    {"id":"first_blood",   "name":"First Strike",     "desc":"Collect your first crystal",       "icon":"✦", "color":C_SUCCESS,  "condition":("crystals_collected",1)},
    {"id":"century",       "name":"Centurion",        "desc":"Collect 100 crystals",             "icon":"💎","color":C_SUCCESS,  "condition":("crystals_collected",100)},
    {"id":"millionaire",   "name":"Millionaire",      "desc":"Accumulate 1,000,000 resources",   "icon":"★", "color":C_ACCENT,   "condition":("total_resources",1_000_000)},
    {"id":"combo_king",    "name":"Combo King",       "desc":"Reach a ×8 combo multiplier",      "icon":"⚡","color":C_ACCENT,   "condition":("max_combo",8)},
    {"id":"voidite_first", "name":"Void Touched",     "desc":"Collect a Voidite crystal",        "icon":"🔮","color":(255,70,90),"condition":("voidite_collected",1)},
    {"id":"voidite_10",    "name":"Void Hunter",      "desc":"Collect 10 Voidite crystals",      "icon":"🔮","color":(255,70,90),"condition":("voidite_collected",10)},
    # Combat
    {"id":"first_kill",    "name":"Exterminator",     "desc":"Defeat your first enemy",          "icon":"☠", "color":C_DANGER,   "condition":("kills",1)},
    {"id":"kill_50",       "name":"Void Slayer",      "desc":"Defeat 50 enemies",                "icon":"☠", "color":C_DANGER,   "condition":("kills",50)},
    {"id":"kill_500",      "name":"Void Reaper",      "desc":"Defeat 500 enemies",               "icon":"☠", "color":C_DANGER,   "condition":("kills",500)},
    {"id":"first_boss",    "name":"Boss Buster",      "desc":"Defeat your first boss",           "icon":"👑","color":(200,100,255),"condition":("bosses_killed",1)},
    {"id":"boss_5",        "name":"Boss Hunter",      "desc":"Defeat 5 bosses",                  "icon":"👑","color":(200,100,255),"condition":("bosses_killed",5)},
    # Survival
    {"id":"wave_5",        "name":"Survivor",         "desc":"Survive to wave 5",                "icon":"🛡","color":C_SUCCESS,  "condition":("max_wave",5)},
    {"id":"wave_10",       "name":"Veteran",          "desc":"Survive to wave 10",               "icon":"🛡","color":C_SUCCESS,  "condition":("max_wave",10)},
    {"id":"wave_20",       "name":"Legend",           "desc":"Survive to wave 20",               "icon":"★", "color":C_ACCENT,   "condition":("max_wave",20)},
    {"id":"wave_50",       "name":"Immortal",         "desc":"Survive to wave 50",               "icon":"★", "color":(255,220,50),"condition":("max_wave",50)},
    # Upgrades
    {"id":"first_upgrade", "name":"Enhanced",         "desc":"Buy your first upgrade",           "icon":"⚙", "color":C_SECONDARY,"condition":("upgrades_bought",1)},
    {"id":"maxed_one",     "name":"Specialist",       "desc":"Max out any single upgrade",       "icon":"⚙", "color":C_SECONDARY,"condition":("upgrades_maxed",1)},
    {"id":"all_upgrades",  "name":"Omnipotent",       "desc":"Purchase every upgrade type",      "icon":"⚙", "color":(255,180,50),"condition":("unique_upgrades",10)},
    # Level
    {"id":"level_5",       "name":"Rising Star",      "desc":"Reach player level 5",             "icon":"🌟","color":C_ACCENT,   "condition":("player_level",5)},
    {"id":"level_20",      "name":"Transcendent",     "desc":"Reach player level 20",            "icon":"🌟","color":(255,220,50),"condition":("player_level",20)},
    # Modes
    {"id":"blitz_win",     "name":"Speed Demon",      "desc":"Complete a Blitz run",             "icon":"⚡","color":(255,180,50),"condition":("blitz_wins",1)},
    {"id":"rush_100k",     "name":"Rush Master",      "desc":"Score 100K in Crystal Rush",       "icon":"💎","color":C_SECONDARY,"condition":("rush_best",100_000)},
    # Secret
    {"id":"no_damage",     "name":"Untouchable",      "desc":"Survive wave 3 without taking damage","icon":"✨","color":(255,255,100),"condition":("nodmg_wave3",1)},
]

class AchievementSystem:
    def __init__(self):
        self.unlocked  = set()
        self.stats = {
            "crystals_collected": 0,
            "total_resources": 0,
            "max_combo": 0,
            "voidite_collected": 0,
            "kills": 0,
            "bosses_killed": 0,
            "max_wave": 0,
            "upgrades_bought": 0,
            "upgrades_maxed": 0,
            "unique_upgrades": 0,
            "player_level": 1,
            "blitz_wins": 0,
            "rush_best": 0,
            "nodmg_wave3": 0,
        }
        self.pending_display = [] # list of achievement dicts to show 
        self._display_timer = 0.0 
        self._load()

    def _load(self):
        try:
            if os.path.exists(ACHIEVEMENT_FILE):
                with open (ACHIEVEMENT_FILE) as f:
                    data = json.load(f)
                self.unlocked = set(data.get("unlocked", []))
                saved  =data.get("stats", {})
                for k in self.stats:
                    if k in saved:
                        self.stats[k] = saved[k]
        except Exception:
            pass 

    def save(self):
        os.makedirs("data", exist_ok=True)
        with open(ACHIEVEMENT_FILE, "w") as f:
            json.dump({"unlocked": list(self.unlocked),
                       "stats": self.stats}, f, indent=2)
    
    def update_stat(self, key, value, mode="add"):
        """mode: add | max | set"""
        if key not in self.stats:
            return 
        if mode == "add":
            self.stats[key] += value 
        elif mode == "max":
            self.stats[key] = max(self.stats[key], value)
        elif mode == "set":
            self.stats[key] = value 
    
    def _check_all(self):
        for ach in ACHIEVEMENTS:
            if ach["id"] in self.unlocked:
                continue 
            key, threshold = ach["condition"]
            if self.stats.get(key, 0) >= threshold:
                self.unloacked.add(ach["id"])
                self.pending_display.append(ach)
                self.save()

    def update(self, dt):
        self._display_timer = max(0, self._display_timer - dt)

    def draw(self, surf, font_md, font_sm, font_xs):
        import pygame 
        from utils.constants import WIDTH, HEIGHT 
        from engine.renderer import draw_panel, draw_glow_rect 
        from utils.math_utils import smooth_step 

        if not self.pending_display:
            return 
        
        ach = self.pending_display[0]
        if self._display_timer <= 0:
            self._display_timer = 3.5

        t = self._display_timer / 3.5
        alpha = int(255 * smooth_step((min(t * 4, 1.0))) * smooth_step(t * 1.5))

        panel_w, panel_h = 320, 62
        px = WIDTH - panel_w  - 16
        py = 60 

        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*ach["color"], alpha // 4),
                         (0, 0, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(s, (*ach["color"], alpha // 2),
                             (0, 0, panel_w, panel_h), width=1, border_radius=10)

        surf.bli(tag, (px + 44, py + 8))

        # icon
        icon_s = font_md.render(ach["icon"], True, ach["color"])
        icon_s.set_alpha(alpha)
        surf.blit(icon_s, (px + 12, py + panel_h/2 - icon_s.get_height()//2))

        # Text
        tag = font_xs.render("ACHIEVEMENT UNLOCKED", True, ach["color"])
        tag.set_alpha(alpha // 2)
        surf.blit(tag, (px + 44, py + 8))

        name_s = font_sm.render(ach["name"], True, (240, 235,255))
        name_s.set_alpha(alpha)
        surf.blit(name_s,(px + 44, py + 22))

        desc_s = font_xs.render(ach["desc"], True,(140,130,170))
        desc_s.set_alpha(alpha)
        surf.blit(desc_s, (px + 44, py + 40))

        if self._display_timer < 0.1:
            self.pending_display.pop(0)
            self.display_timer = 0
    
    @property 
    def total_unlocked(self):
        return len(self.unlocked)
    
    @property
    def total_count(self):
        return len(ACHIEVEMENTS)
    
    
