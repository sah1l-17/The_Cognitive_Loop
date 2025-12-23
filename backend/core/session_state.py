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

    def log(self, entry: dict):
        self.history.append(entry)
