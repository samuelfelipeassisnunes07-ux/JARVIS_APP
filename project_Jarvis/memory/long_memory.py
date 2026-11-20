from typing import Any, Dict, List, Optional
import json

from database.db import Database


class LongMemory:
    """Memória persistente isolada por user_id."""

    def __init__(self, db_path: Optional[str] = None):
        self.db = Database(db_path)
        self.user_id: Optional[int] = None
        self.conversation_id: Optional[int] = None

    def bind(self, user_id: int, conversation_id: Optional[int] = None) -> "LongMemory":
        memory = LongMemory()
        memory.db = self.db
        memory.user_id = user_id
        memory.conversation_id = conversation_id
        return memory

    def _require_user(self) -> int:
        if self.user_id is None:
            raise ValueError("LongMemory precisa ser associada a um user_id")
        return self.user_id

    def save_message(self, role: str, content: str, metadata: Optional[Dict] = None,
                     intent: Optional[str] = None, conversation_id: Optional[int] = None) -> int:
        conversation = conversation_id or self.conversation_id
        if conversation is None:
            conversation = self.db.ensure_conversation(self._require_user())
            self.conversation_id = conversation
        return self.db.save_message(self._require_user(), conversation, role, content, metadata, intent)

    def get_conversation_history(self, limit: int = 50, conversation_id: Optional[int] = None) -> List[Dict]:
        conversation = conversation_id or self.conversation_id
        if conversation is None:
            return []
        return self.db.get_conversation_history(self._require_user(), conversation, limit)

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        return self.db.search_conversations(self._require_user(), query, limit)

    def remember(self, key: str, content: Any, memory_type: str = "general",
                 importance: float = 1.0, metadata: Optional[Dict] = None) -> bool:
        return self.db.save_memory(self._require_user(), key, str(content), memory_type, importance, metadata)

    def recall(self, key: str) -> Optional[str]:
        memory = self.db.get_memory(self._require_user(), key)
        return memory["content"] if memory else None

    def recall_with_metadata(self, key: str) -> Optional[Dict]:
        return self.db.get_memory(self._require_user(), key)

    def search(self, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        return self.db.search_memories(self._require_user(), query, memory_type, limit)

    def get_important(self, min_importance: float = 0.7, limit: int = 20) -> List[Dict]:
        return self.db.get_important_memories(self._require_user(), min_importance, limit)

    def remember_preference(self, key: str, value: Any):
        return self.remember(f"pref_{key}", value, "preference", 0.8)

    def recall_preference(self, key: str) -> Optional[str]:
        return self.recall(f"pref_{key}")

    def remember_fact(self, key: str, fact: str):
        return self.remember(f"fact_{key}", fact, "fact", 0.9)

    def remember_context(self, context_key: str, context: Dict):
        return self.remember(f"ctx_{context_key}", json.dumps(context), "context", 0.6)

    def clear_old(self, days: int = 30) -> int:
        return self.db.clear_old_conversations(days, self._require_user())

    def get_stats(self) -> Dict:
        return self.db.get_stats(self._require_user())

    def optimize(self):
        return self.db.vacuum()
