class SessionState:
    def __init__(self):
        self.ingested_content = None
        self.current_concept = None
        self.concept_understood = False
        self.last_agent = None
        self.history = []
        
        # Tutor state
        self.confusion_level = 0.0
        self.last_explanation_style = None
        self.clarification_requests = 0
        self.understood = False
        
        # Game tracking state
        self.generated_games = {}  # {concept: {game_type: [game1, game2, ...]}}
        self.game_index = {}  # {concept: {game_type: current_index}}

        # Game performance stats (persisted)
        # {concept: {game_type: {streak, best_streak, correct, total}}}
        self.game_stats = {}

    def log(self, entry: dict):
        self.history.append(entry)

    def to_dict(self) -> dict:
        def safe(v):
            if v is None or isinstance(v, (str, int, float, bool)):
                return v
            if isinstance(v, list):
                return [safe(x) for x in v]
            if isinstance(v, dict):
                return {str(k): safe(val) for k, val in v.items()}
            return str(v)

        return {
            "ingested_content": safe(self.ingested_content),
            "current_concept": safe(self.current_concept),
            "concept_understood": bool(self.concept_understood),
            "last_agent": safe(self.last_agent),
            "history": safe(self.history),
            "confusion_level": float(self.confusion_level or 0.0),
            "last_explanation_style": safe(self.last_explanation_style),
            "clarification_requests": int(self.clarification_requests or 0),
            "understood": bool(self.understood),
            "generated_games": safe(getattr(self, "generated_games", {})),
            "game_index": safe(getattr(self, "game_index", {})),
            "game_stats": safe(getattr(self, "game_stats", {})),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        s = cls()
        if not isinstance(data, dict):
            return s

        s.ingested_content = data.get("ingested_content")
        s.current_concept = data.get("current_concept")
        s.concept_understood = bool(data.get("concept_understood", False))
        s.last_agent = data.get("last_agent")
        s.history = data.get("history") or []

        s.confusion_level = float(data.get("confusion_level", 0.0) or 0.0)
        s.last_explanation_style = data.get("last_explanation_style")
        s.clarification_requests = int(data.get("clarification_requests", 0) or 0)
        s.understood = bool(data.get("understood", False))

        # Game tracking state (persist across reloads)
        s.generated_games = data.get("generated_games") or {}
        s.game_index = data.get("game_index") or {}
        s.game_stats = data.get("game_stats") or {}
        return s
