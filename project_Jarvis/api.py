"""API local do Jarvis, com identidade por credencial e conversas persistentes."""
from contextlib import asynccontextmanager
from hashlib import sha256
from pathlib import Path
import logging
import secrets
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.assistant import Assistant
from database.connection import ensure_database_exists
from database.db import Database
from database.feedback import FeedbackManager

logger = logging.getLogger(__name__)
WEB_DIR = Path(__file__).resolve().parent / 'web'
jarvis = None


@asynccontextmanager
async def lifespan(app):
    global jarvis
    try:
        ensure_database_exists()
        Database().init_database()
        jarvis = Assistant()
    except Exception:
        logger.exception('Falha ao inicializar Jarvis')
        jarvis = None
    yield
    if jarvis is not None:
        jarvis.shutdown()


app = FastAPI(title='Jarvis Assistant API', version='2.1.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=WEB_DIR), name='static')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8080', 'http://127.0.0.1:8080'],
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'Authorization'],
)
bearer = HTTPBearer(auto_error=False)


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', protected_namespaces=())


class Message(StrictRequest):
    text: str = Field(min_length=1, max_length=20000)
    conversation_id: int | None = Field(default=None, gt=0)

    @field_validator('text')
    @classmethod
    def nonempty(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Informe uma mensagem')
        return value


class FeedbackRequest(StrictRequest):
    session_id: str = Field(pattern=r'^[1-9][0-9]*$', max_length=20)
    user_question: str = Field(default='', max_length=20000)
    assistant_response: str = Field(default='', max_length=50000)
    rating: int = Field(ge=1, le=5)
    feedback_text: str = Field(default='', max_length=5000)
    intent: str = Field(default='', max_length=100)
    model_used: str = Field(default='', max_length=191)
    response_time: float = Field(default=0, ge=0)


def credential_name(token):
    return 'web_' + sha256(token.encode()).hexdigest()


def current_user(auth: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if auth is None or len(auth.credentials) > 200:
        raise HTTPException(401, 'Credencial necessária', headers={'WWW-Authenticate': 'Bearer'})
    try:
        user_id = Database().find_user(credential_name(auth.credentials))
    except Exception as exc:
        logger.exception('Falha ao consultar identidade')
        raise HTTPException(503, 'Banco de dados indisponível') from exc
    if user_id is None:
        raise HTTPException(401, 'Credencial inválida', headers={'WWW-Authenticate': 'Bearer'})
    return user_id


def conversation_for(user_id, conversation_id=None):
    try:
        return Database().ensure_conversation(user_id, conversation_id)
    except ValueError as exc:
        raise HTTPException(404, 'Conversa não encontrada') from exc
    except Exception as exc:
        logger.exception('Falha ao acessar conversa')
        raise HTTPException(503, 'Banco de dados indisponível') from exc


def require_assistant():
    if jarvis is None:
        raise HTTPException(503, 'Assistente indisponível; verifique MySQL e Ollama')
    return jarvis


@app.get('/')
def root():
    return RedirectResponse('/static/index.html')


@app.get('/health')
def health():
    if jarvis is None:
        raise HTTPException(503, 'Assistente não inicializado')
    return {'status': 'online', 'assistant': 'Jarvis', 'version': '2.1.0'}


@app.post('/session')
def create_session():
    token = secrets.token_urlsafe(32)
    try:
        Database().ensure_user(credential_name(token))
    except Exception as exc:
        logger.exception('Falha ao criar identidade')
        raise HTTPException(503, 'Banco de dados indisponível') from exc
    return {'token': token}


@app.post('/chat')
def chat(msg: Message, user_id: int = Depends(current_user)):
    assistant = require_assistant()
    conversation_id = conversation_for(user_id, msg.conversation_id)
    request_id = str(uuid4())
    try:
        response = assistant.process_message(msg.text, user_id=user_id, conversation_id=conversation_id)
    except Exception as exc:
        logger.exception('Falha no chat request_id=%s', request_id)
        raise HTTPException(500, 'Não foi possível processar a mensagem') from exc
    return {'response': response, 'session_id': str(conversation_id),
            'conversation_id': conversation_id, 'request_id': request_id}


@app.post('/feedback')
def submit_feedback(feedback: FeedbackRequest, user_id: int = Depends(current_user)):
    conversation_for(user_id, int(feedback.session_id))
    try:
        FeedbackManager().save_feedback(**feedback.model_dump())
    except Exception as exc:
        logger.exception('Falha ao salvar feedback')
        raise HTTPException(503, 'Não foi possível salvar o feedback') from exc
    return {'message': 'Obrigado pelo feedback!'}


@app.get('/feedback/stats')
def feedback_stats(user_id: int = Depends(current_user)):
    return FeedbackManager().get_feedback_stats(user_id)


@app.post('/remember')
def remember(key: str, value: str, user_id: int = Depends(current_user)):
    assistant = require_assistant()
    # Memórias permanentes pertencem ao usuário, sem criar conversas vazias.
    assistant.memory.long.bind(user_id).remember(key, value)
    return {'status': 'success', 'message': f"Memória '{key}' salva"}


@app.get('/recall/{key}')
def recall(key: str, user_id: int = Depends(current_user)):
    value = require_assistant().memory.long.bind(user_id).recall(key)
    return {'status': 'success' if value is not None else 'not_found', 'key': key, 'value': value}


@app.get('/stats')
def stats(user_id: int = Depends(current_user)):
    memory = Database().get_stats(user_id)
    feedback = FeedbackManager().get_feedback_stats(user_id)['general']
    return {**memory, 'total_feedbacks': feedback['total_feedback'],
            'average_rating': feedback['avg_rating'] or 0}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
