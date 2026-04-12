"""
Save / Load for AETHER HARVEST v3
Saves: resources, upgrades, wave, xp_state, mode, difficulty
"""
import json
import os


def get_save_path():
    if os.name == "nt":  # Windows
        base = os.getenv("APPDATA")
    else:  # Linux / Mac
        base = os.path.expanduser("~/.local/share")

    save_dir = os.path.join(base, "AetherHarvest")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    return os.path.join(save_dir, "save.json")


SAVE_PATH = get_save_path()


def save_game(resources, upgrades, wave, xp_sys=None,
              mode_id="classic", difficulty_id="normal"):
    data = {
        "resources":      resources,
        "upgrade_levels": upgrades.levels,
        "upgrade_costs":  upgrades.costs,
        "wave":           wave,
        "mode_id":        mode_id,
        "difficulty_id":  difficulty_id,
    }

    if xp_sys:
        data["xp"] = {
            "xp":          xp_sys.xp,
            "level":       xp_sys.level,
            "xp_to_next":  xp_sys.xp_to_next,
            "total_xp":    xp_sys.total_xp,
            "kills":       xp_sys.kills,
            "bonus_click": xp_sys.bonus_click,
            "bonus_hp":    xp_sys.bonus_hp,
            "bonus_range": xp_sys.bonus_range,
            "income_mult": xp_sys.income_mult,
        }

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def load_game(upgrades):
    if not os.path.exists(SAVE_PATH):
        return 0, 0, "classic", "normal", None

    try:
        with open(SAVE_PATH) as f:
            data = json.load(f)

        resources     = data.get("resources", 0)
        wave          = data.get("wave", 0)
        mode_id       = data.get("mode_id", "classic")
        difficulty_id = data.get("difficulty_id", "normal")
        xp_data       = data.get("xp", None)

        for k, v in data.get("upgrade_levels", {}).items():
            if k in upgrades.levels:
                upgrades.levels[k] = v

        for k, v in data.get("upgrade_costs", {}).items():
            if k in upgrades.costs:
                upgrades.costs[k] = v

        return resources, wave, mode_id, difficulty_id, xp_data

    except Exception:
        return 0, 0, "classic", "normal", None