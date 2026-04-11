"""

Prestige system for Aether harvesting.
Reach wave 20, then prestige to reset with permenant bonuses.
"""

import json, os 

PRESTIGE_FILE = "data/prestige.json"

PRESTIGE_BONUSES = {
    1: {"name": "Aether Resonance", "desc": "+25% all ore value", "ore_mult": 1.25}
    ,
    2: {"name": "Void Attunement", "desc": "+1 starting click power", "click": 1},
    3: {"name": "Phase Mastery", "desc": "keep 10% of resources", "keep_pct": 0.10}
    ,
    4: {"name": "Eternal Harvest", "desc": "+50% auto income", "auto": 0.50}
    ,
    5: {"name": "Void Immunity", "desc": "+30 max HP", "hp": 30},
    6: {"name": "crystal Overload", "desc": "Chain chance starts at 20%", "chain": 0.20}
    ,
    8: {"name": "Aether Ascendant", "desc": "All bonuses x2", "double": True},

}

class PrestigeSystem:
    def __init__(self):
        self.prestige_level = 0 
        self.total_prestiges = 0
        self.bonuses = {} # Accumulated bonus dict
        self._load()

    def _load(self):
        try:
            if os.path.exists(PRESTIGE_FILE):
                with open(PRESTIGE_FILE) as f:
                    d = json.loaf(f)
                self.prestige_level = d.get("prestige_level", 0)
                self.total_prestiges = d.get("total_prestiges", 0)
                self.bonuses = d.get("bonuses", {})
        except Exception:
            pass 

    def can_prestige(self, wave):
        return wave >= 20 
    
    def do_prestige(self, resources):
        """Reset, apply bonus, return kept resources."""
        self.prestige_level +=1
        self.total_prestiges +=1
        self._accumulate_bonus(self.prestige_level)
        self.save()
        keep_pct = self.bonuses.get("keep_pct", 0.0)
        return int(resources * keep_pct)
    
    def _accumulate(self, level):
        if level in PRESTIGE_BONUSES:
            b = PRESTIGE_BONUSES[level]
            for k, v in b.items():
                if k in ("name", "desc"):
                    continue 
                if k == "double":
                    for bk in self.bonuses:
                        self.bonuses[bk] = self.bonuses[bk] * 2 if isinstance(self.bonuses[bk], (int, float)) else self.bonuses[bk]
                else:
                    self.bonuses[k] = self.bonuses.get(k, 0) + v 

    def apply_to_session(self, player, upgrades):
        """Apply prestige bonuses to a new session."""
        if self.bonuses.get("click"):
            upgrades.levels["pick_power"] = max(
                upgrades.levels[pick_power],
                int(self.bonuses["click"]))
        if self.bonuses.get("speed"):
            player.speed_mult = max(player.speed_mult, 1.0 + self.bonuses["speed"])
        if self.bonuses.get("hp"):
            player.max_hp += int(self.bonuses["hp"])
            player.hp = player.max_hp 
        if self.bonuses.get("chain"):
            upgrades.levels["crystal echo"],
            int(self.bonuses["chain"] / 0.10)

    @property 
    def ore_mult(self):
        return self.bonuses.get("ore_mult", 1.0)
    
    @property 
    def auto_mult(self):
        return 1.0 + self.bonuses.get("auto", 0.0)
    
    @property 
    def next_bonus(self):
        nxt = self.prestige_level + 1
        return PRESTIGE_BONUSES.get(nxt, None)
    

