"""
Upgrade system for AETHER HARVEST
"""
from utils.constants import UPGRADES


class UpgradeSystem:
    def __init__(self):
        self.levels = {u["id"]: 0 for u in UPGRADES}
        self.costs  = {u["id"]: u["base_cost"] for u in UPGRADES}

    def can_afford(self, upgrade_id, resources):
        u = self._get(upgrade_id)
        if u is None:
            return False
        if self.levels[upgrade_id] >= u["max_level"]:
            return False
        return resources >= self.costs[upgrade_id]

    def purchase(self, upgrade_id, resources):
        if not self.can_afford(upgrade_id, resources):
            return resources, False
        u    = self._get(upgrade_id)
        cost = self.costs[upgrade_id]
        resources -= cost
        self.levels[upgrade_id] += 1
        self.costs[upgrade_id] = int(cost * u["cost_scale"])
        return resources, True

    def level(self, upgrade_id):
        return self.levels.get(upgrade_id, 0)

    def maxed(self, upgrade_id):
        u = self._get(upgrade_id)
        if u is None:
            return True
        return self.levels[upgrade_id] >= u["max_level"]

    def _get(self, upgrade_id):
        for u in UPGRADES:
            if u["id"] == upgrade_id:
                return u
        return None


    @property
    def click_power(self):
        return 1 + self.levels["pick_power"]

    @property
    def auto_income(self):
        return self.levels["auto_harvest"] * 2

    @property
    def rare_boost(self):
        return self.levels["ore_magnet"] * 0.15

    @property
    def collect_range_bonus(self):
        return self.levels["warp_field"] * 40

    @property
    def chain_chance(self):
        return self.levels["crystal_echo"] * 0.10

    @property
    def has_time_slow(self):
        return self.levels["temporal_surge"] > 0

    @property
    def hp_regen(self):
        return self.levels.get("void_shield", 0) * 1.0

    @property
    def speed_mult(self):
        return 1.0 + self.levels.get("phase_drive", 0) * 0.15

    @property
    def vacuum_radius(self):
        return self.levels.get("aether_lens", 0) * 50

    @property
    def bolt_level(self):
        return self.levels.get("aether_bolt", 0)
