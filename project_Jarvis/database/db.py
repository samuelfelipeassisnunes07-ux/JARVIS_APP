import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Iterator, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.connection import engine, session_scope
from database.models import Base, Conversation, Memory, Message, User


class Database:
    """Acesso MySQL via SQLAlchemy, com sessões independentes por operação."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def init_database(self) -> None:
        Base.metadata.create_all(bind=engine)

    @contextmanager
    def get_connection(self) -> Iterator[Session]:
        with session_scope() as session:
            yield session

    def ensure_user(self, username: str) -> int:
        with session_scope() as session:
            user = session.scalar(select(User).where(User.username == username))
            if user is None:
                user = User(username=username)
                session.add(user)
                session.flush()
            return user.id

    def find_user(self, username: str) -> Optional[int]:
        with session_scope() as session:
            return session.scalar(select(User.id).where(User.username == username))

    def ensure_conversation(self, user_id: int, conversation_id: Optional[int] = None, title: Optional[str] = None) -> int:
        with session_scope() as session:
            conversation = None
            if conversation_id is not None:
                conversation = session.scalar(select(Conversation).where(
                    Conversation.id == conversation_id, Conversation.user_id == user_id
                ))
                if conversation is None:
                    raise ValueError("A conversa não pertence ao usuário informado")
            if conversation is None:
                conversation = Conversation(user_id=user_id, title=title)
                session.add(conversation)
                session.flush()
            return conversation.id

    def save_message(self, user_id: int, conversation_id: int, role: str, content: str,
                     metadata: Optional[Dict] = None, intent: Optional[str] = None) -> int:
        with session_scope() as session:
            self._assert_conversation_owner(session, user_id, conversation_id)
            message = Message(user_id=user_id, conversation_id=conversation_id, role=role,
                              content=content, metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
                              intent=intent)
            session.add(message)
            session.flush()
            return message.id

    def get_conversation_history(self, user_id: int, conversation_id: int, limit: int = 50) -> List[Dict]:
        with session_scope() as session:
            self._assert_conversation_owner(session, user_id, conversation_id)
            rows = session.scalars(select(Message).where(
                Message.user_id == user_id, Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)).all()
            return [self._message_dict(row) for row in reversed(rows)]

    def search_conversations(self, user_id: int, query: str, limit: int = 10) -> List[Dict]:
        with session_scope() as session:
            rows = session.scalars(select(Message).where(
                Message.user_id == user_id, Message.content.contains(query)
            ).order_by(Message.created_at.desc()).limit(limit)).all()
            return [self._message_dict(row) for row in rows]

    def save_memory(self, user_id: int, key: str, content: str, memory_type: str = "general",
                    importance: float = 1.0, metadata: Optional[Dict] = None) -> bool:
        from database.models import Memory
        with session_scope() as session:
            memory = session.scalar(select(Memory).where(
                Memory.user_id == user_id, Memory.memory_key == key
            ))
            encoded = json.dumps(metadata or {}, ensure_ascii=False)
            if memory is None:
                session.add(Memory(user_id=user_id, memory_key=key, content=content,
                                   memory_type=memory_type, importance=importance, metadata_json=encoded))
            else:
                memory.content = content
                memory.memory_type = memory_type
                memory.importance = importance
                memory.metadata_json = encoded
                memory.updated_at = datetime.utcnow()
            return True

    def get_memory(self, user_id: int, key: str) -> Optional[Dict]:
        with session_scope() as session:
            memory = session.scalar(select(Memory).where(
                Memory.user_id == user_id, Memory.memory_key == key
            ))
            if memory is None:
                return None
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1
            return self._memory_dict(memory)

    def search_memories(self, user_id: int, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        with session_scope() as session:
            statement = select(Memory).where(Memory.user_id == user_id, Memory.content.contains(query))
            if memory_type:
                statement = statement.where(Memory.memory_type == memory_type)
            rows = session.scalars(statement.order_by(Memory.importance.desc(), Memory.updated_at.desc()).limit(limit)).all()
            return [self._memory_dict(row) for row in rows]

    def get_important_memories(self, user_id: int, min_importance: float = 0.7, limit: int = 20) -> List[Dict]:
        with session_scope() as session:
            rows = session.scalars(select(Memory).where(
                Memory.user_id == user_id, Memory.importance >= min_importance
            ).order_by(Memory.importance.desc(), Memory.updated_at.desc()).limit(limit)).all()
            return [self._memory_dict(row) for row in rows]

    def clear_old_conversations(self, days: int = 30, user_id: Optional[int] = None) -> int:
        with session_scope() as session:
            statement = select(Message).where(Message.created_at < datetime.utcnow() - timedelta(days=days))
            if user_id is not None:
                statement = statement.where(Message.user_id == user_id)
            rows = session.scalars(statement).all()
            for row in rows:
                session.delete(row)
            return len(rows)

    def get_stats(self, user_id: Optional[int] = None) -> Dict:
        with session_scope() as session:
            message_query = select(func.count(Message.id))
            memory_query = select(func.count(Memory.id))
            if user_id is not None:
                message_query = message_query.where(Message.user_id == user_id)
                memory_query = memory_query.where(Memory.user_id == user_id)
            return {"total_messages": session.scalar(message_query) or 0,
                    "total_memories": session.scalar(memory_query) or 0,
                    "total_conversations": session.scalar(select(func.count(Conversation.id)).where(
                        Conversation.user_id == user_id)) if user_id is not None else session.scalar(
                            select(func.count(Conversation.id))), "database": "mysql"}

    def vacuum(self):
        return None

    @staticmethod
    def _assert_conversation_owner(session: Session, user_id: int, conversation_id: int) -> None:
        if session.scalar(select(Conversation.id).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )) is None:
            raise ValueError("A conversa não pertence ao usuário informado")

    @staticmethod
    def _message_dict(message: Message) -> Dict:
        return {"id": message.id, "role": message.role, "content": message.content,
                "timestamp": message.created_at,
                "metadata": json.loads(message.metadata_json or "{}"), "intent": message.intent}

    @staticmethod
    def _memory_dict(memory: Memory) -> Dict:
        return {"id": memory.id, "key": memory.memory_key, "content": memory.content,
                "memory_type": memory.memory_type, "importance": memory.importance,
                "created_at": memory.created_at, "updated_at": memory.updated_at,
                "metadata": json.loads(memory.metadata_json or "{}")}
