from typing import Any, Dict, List, Optional
from threading import RLock

from config.settings import settings
from database.db import Database
from memory.long_memory import LongMemory
from memory.short_memory import ShortMemory


class MemoryManager:
    """Coordena memória sem compartilhar contexto entre usuários."""

    def __init__(self):
        self.db = Database()
        self.db.init_database()
        self.long = LongMemory()
        self._short_memories: Dict[tuple[int, int], ShortMemory] = {}
        self._cache: Dict[tuple[int, str], Any] = {}
        self._lock = RLock()
        self.max_size = settings.get("memory.short_term_size", 20)

    def bind(self, user_id: int, conversation_id: int) -> "MemoryManager":
        manager = object.__new__(MemoryManager)
        manager.db = self.db
        manager.long = self.long.bind(user_id, conversation_id)
        manager._user_id = user_id
        manager._conversation_id = conversation_id
        manager.max_size = self.max_size
        manager._short_memories = {}
        manager._cache = {}
        manager._lock = RLock()
        return manager

    def _scope(self) -> tuple[int, int]:
        if not hasattr(self, "_user_id") or not hasattr(self, "_conversation_id"):
            raise ValueError("MemoryManager precisa ser associado a usuário e conversa")
        return self._user_id, self._conversation_id

    @property
    def short(self) -> ShortMemory:
        scope = self._scope()
        with self._lock:
            if scope not in self._short_memories:
                memory = ShortMemory(max_size=self.max_size)
                for message in self.db.get_conversation_history(*scope, limit=self.max_size):
                    memory.add_message(message["role"], message["content"], message.get("metadata"))
                self._short_memories[scope] = memory
            return self._short_memories[scope]

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None,
                    intent: Optional[str] = None):
        user_id, conversation_id = self._scope()
        self.short.add_message(role, content, metadata)
        self.db.save_message(user_id, conversation_id, role, content, metadata, intent)
        self._check_consolidation(role, content, metadata)

    def _check_consolidation(self, role: str, content: str, metadata: Optional[Dict]):
        if role != "user":
            return
        content_lower = content.lower()
        keywords = ["meu nome é", "chamo", "me chamo", "gosto de", "prefiro", "não gosto",
                    "trabalho com", "estudo", "moro em", "importante lembrar", "nunca esqueça"]
        for keyword in keywords:
            if keyword in content_lower:
                self.long.remember(f"info_{keyword.replace(' ', '_')}", content, "important", 0.9,
                                   {"source": "conversation", "keyword": keyword})
                break

    def get_context(self, include_long_term: bool = True) -> Dict[str, Any]:
        context = {"short_term": self.short.get_conversation_context(), "stats": self.short.get_stats()}
        if include_long_term:
            last_message = self.short.get_last_message()
            context["long_term"] = self.long.search(last_message["content"], limit=5) if last_message else []
            # Preferências relevantes devem sobreviver a mudanças de assunto.
            known = {item["content"] for item in context["long_term"]}
            for item in self.long.get_important(limit=5):
                if item["content"] not in known:
                    context["long_term"].append(item)
                    known.add(item["content"])
            context["long_term"] = context["long_term"][:5]
        return context

    def remember(self, key: str, value: Any, importance: float = 1.0,
                 memory_type: str = "manual"):
        user_id, _ = self._scope()
        self.long.remember(key, value, memory_type, importance)
        self._cache[(user_id, key)] = value

    def recall(self, key: str) -> Optional[Any]:
        user_id, _ = self._scope()
        cache_key = (user_id, key)
        if cache_key not in self._cache:
            value = self.long.recall(key)
            if value is not None:
                self._cache[cache_key] = value
        return self._cache.get(cache_key)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        long_results = self.long.search(query, limit=limit)
        short_results = self.short.search_by_content(query)
        seen = {item.get("content", "") for item in long_results}
        return (long_results + [item for item in short_results if item.get("content") not in seen])[:limit]

    def get_conversation_summary(self) -> str:
        history = self.short.get_history(as_text=True)
        return history if len(history.split("\n")) <= 6 else "\n".join(history.split("\n")[-6:]) + "\n[Histórico resumido...]"

    def clear_session(self):
        scope = self._scope()
        with self._lock:
            self._short_memories.pop(scope, None)
        self._cache = {key: value for key, value in self._cache.items() if key[0] != scope[0]}

    def get_stats(self) -> Dict:
        return {"short_term": self.short.get_stats(), "long_term": self.long.get_stats()}
