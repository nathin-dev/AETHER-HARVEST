"""
Save / Load for Infinite Harvest
"""

import json
import os
from utils.constants import SAVE_PATH

def save_game(resources, upgrades, wave):
    data = {
        "resources":   resources,
        "upgrade_levels":   upgrades.levels,
        "upgrade_costs": upgrades.costs,
        "wave":   wave,

    }
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_game(upgrades):
    if not os.path.dirname(SAVE_PATH):
        return 0, 0
    try:
        with open(SAVE_PATH) as f:
            data = json.load(f)
        resources = data.get("resources", 0)
        wave = data.get("wave", 0)
        for k, v in data.get("upgrade_levels", {}).items():
            if k in upgrades.levels:
                upgrades.levels[k] = v 
        for k, v in data.get("upgrade_costs", {}).items():
            if k in upgrades.costs:
                upgrades.costs[k] = v 
        return resources, wave
    except Exception:
        return 0, 0