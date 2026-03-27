class SessionStore:
    def __init__(self):
        self.sessions = {}
    
    def create(self, session_id):
        self.sessions[session_id] = {
            "step": 0,
            "data": {}
        }

    def get(self, session_id):
        return self.sessions.get(session_id)
    
    def update(self, session_id, key, value):
        if session_id in self.sessions:
            self.sessions[session_id]["data"][key] = value

    def increment_step(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["step"] += 1

session_store = SessionStore()