from typing import Optional, Any


class SessionStore:
    """
    In-memory opslag voor intake sessies.

    Beheert:
    - huidige stap in de intake flow
    - verzamelde antwoorden per sessie

    Let op:
        Deze store is tijdelijk en wordt niet persistent opgeslagen.
    """

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    def create(self, session_id: str) -> None:
        """
        Initialiseert een nieuwe sessie.

        Args:
            session_id (str): Unieke identifier voor de sessie.
        """
        self.sessions[session_id] = {"step": 0, "data": {}}

    def get(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Haalt een sessie op.

        Args:
            session_id (str): Sessie ID.

        Returns:
            dict[str, Any] | None: Sessie data of None indien niet gevonden.
        """
        return self.sessions.get(session_id)

    def update(self, session_id: str, key: str, value: Any) -> None:
        """
        Update een waarde binnen de sessie data.

        Args:
            session_id (str): Sessie ID.
            key (str): Sleutel in de data.
            value (Any): Op te slaan waarde.
        """
        if session_id in self.sessions:
            self.sessions[session_id]["data"][key] = value

    def increment_step(self, session_id: str) -> None:
        """
        Verhoogt de huidige stap van de sessie.

        Args:
            session_id (str): Sessie ID.
        """
        if session_id in self.sessions:
            self.sessions[session_id]["step"] += 1


session_store = SessionStore()
