"""
High scores / leaderboard for AETHER HARVEST.
Persisted locally in data/scores.json.
"""
import json, os, time

SCORES_FILE = "data/scores.json"
MAX_SCORES  = 10

class HighScoreSystem:
    def __init__(self):
        self.scores = {}   
        self._load()

    def _load(self):
        try:
            if os.path.exists(SCORES_FILE):
                with open(SCORES_FILE) as f:
                    self.scores = json.load(f)
        except Exception:
            self.scores = {}

    def save(self):
        os.makedirs("data", exist_ok=True)
        with open(SCORES_FILE, "w") as f:
            json.dump(self.scores, f, indent=2)

    def submit(self, mode, difficulty, resources, wave, play_time):
        entry = {
            "score":      int(resources),
            "wave":       wave,
            "time":       round(play_time, 1),
            "difficulty": difficulty,
            "date":       time.strftime("%d/%m/%Y"),
        }
        if mode not in self.scores:
            self.scores[mode] = []
        self.scores[mode].append(entry)
        self.scores[mode].sort(key=lambda x: x["score"], reverse=True)
        self.scores[mode] = self.scores[mode][:MAX_SCORES]
        self.save()
       
        for i, e in enumerate(self.scores[mode]):
            if e is entry:
                return i + 1
        return None

    def get_best(self, mode):
        entries = self.scores.get(mode, [])
        return entries[0] if entries else None

    def is_new_record(self, mode, score):
        best = self.get_best(mode)
        return best is None or score > best["score"]

    def get_top(self, mode, n=5):
        return self.scores.get(mode, [])[:n]

