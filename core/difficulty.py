"""
Difficulty / progression scaler for AETHER HARVEST.
Adjusts enemy stats and ore spawn rates as game time progresses.
"""


class DifficultyScaler:
    """
    Drives gradual difficulty increase.
    Call tick() every frame, read properties to get current modifiers.
    """

    def __init__(self):
        self.elapsed    = 0.0    
        self.wave       = 0

    def tick(self, dt, wave):
        self.elapsed += dt
        self.wave     = wave

    
    @property
    def enemy_hp_mult(self):
        """Enemy HP multiplier — grows with waves."""
        return 1.0 + self.wave * 0.12

    @property
    def enemy_speed_mult(self):
        return 1.0 + self.wave * 0.04

    @property
    def enemy_damage_mult(self):
        return 1.0 + self.wave * 0.08

    @property
    def ore_value_mult(self):
        """Ores become slightly more valuable over time."""
        return 1.0 + self.wave * 0.05

    @property
    def spawn_count_bonus(self):
        """Extra enemies per wave beyond base."""
        return self.wave // 3

    @property
    def danger_level(self):
        """0-5 tier for UI colour coding."""
        return min(5, self.wave // 4)

    @property
    def danger_label(self):
        labels = ["SAFE", "CAUTION", "DANGER", "EXTREME", "CHAOS", "VOID"]
        return labels[self.danger_level]

    @property
    def danger_color(self):
        from utils.constants import C_SUCCESS, C_ACCENT, C_DANGER
        colours = [
            C_SUCCESS,
            (180, 220, 80),
            C_ACCENT,
            (255, 140, 60),
            C_DANGER,
            (200, 50, 255),
        ]
        return colours[self.danger_level]

