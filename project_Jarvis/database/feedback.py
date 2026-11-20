import json
from typing import Dict, List, Optional

from sqlalchemy import func, select, cast, String

from database.connection import session_scope
from database.models import Feedback, Conversation


class FeedbackManager:
    """Gerencia feedback persistido no MySQL."""

    def init_feedback_table(self):
        from database.db import Database
        Database().init_database()

    def save_feedback(self, session_id: str, user_question: str, assistant_response: str,
                      rating: int, feedback_text: Optional[str] = None,
                      intent: Optional[str] = None, model_used: Optional[str] = None,
                      response_time: Optional[float] = None, metadata: Optional[Dict] = None):
        if not 1 <= rating <= 5:
            raise ValueError("rating deve estar entre 1 e 5")
        with session_scope() as session:
            session.add(Feedback(session_id=session_id, user_question=user_question,
                                 assistant_response=assistant_response, rating=rating,
                                 feedback_text=feedback_text, intent=intent, model_used=model_used,
                                 response_time=response_time,
                                 metadata_json=json.dumps(metadata or {}, ensure_ascii=False)))

    def get_feedback_stats(self, user_id: Optional[int] = None) -> Dict:
        with session_scope() as session:
            query = select(Feedback)
            if user_id is not None:
                query = query.join(Conversation, Feedback.session_id == cast(Conversation.id, String)).where(
                    Conversation.user_id == user_id)
            rows = session.scalars(query).all()
            ratings = [row.rating for row in rows]
            distribution = {rating: ratings.count(rating) for rating in sorted(set(ratings))}
            return {"general": {"total_feedback": len(rows),
                                "avg_rating": sum(ratings) / len(ratings) if ratings else None,
                                "min_rating": min(ratings) if ratings else None,
                                "max_rating": max(ratings) if ratings else None},
                    "rating_distribution": distribution}

    def get_recent_feedback(self, limit: int = 20) -> List[Dict]:
        with session_scope() as session:
            rows = session.scalars(select(Feedback).order_by(Feedback.timestamp.desc()).limit(limit)).all()
            return [self._dict(row) for row in rows]

    def get_low_rated_feedback(self, min_rating: int = 2) -> List[Dict]:
        with session_scope() as session:
            rows = session.scalars(select(Feedback).where(Feedback.rating <= min_rating)
                                   .order_by(Feedback.timestamp.desc())).all()
            return [self._dict(row) for row in rows]

    @staticmethod
    def _dict(row: Feedback) -> Dict:
        return {"id": row.id, "session_id": row.session_id, "user_question": row.user_question,
                "assistant_response": row.assistant_response, "rating": row.rating,
                "feedback_text": row.feedback_text, "intent": row.intent,
                "model_used": row.model_used, "response_time": row.response_time,
                "timestamp": row.timestamp,
                "metadata": json.loads(row.metadata_json or "{}")}
