"""Regressões executadas com SQLite temporário e LLM simulado."""
from unittest.mock import Mock

import pytest
import asyncio
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import api
import database.connection as connection
import database.db as db_module
from database.db import Database
from database.models import Base
from core.assistant import Assistant
from core.intent_detector import IntentDetector
from memory.memory_manager import MemoryManager


@pytest.fixture
def database(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    monkeypatch.setattr(connection, 'SessionLocal', sessionmaker(bind=engine, expire_on_commit=False))
    monkeypatch.setattr(db_module, 'engine', engine)
    yield Database()
    engine.dispose()


@pytest.fixture
def assistant(database):
    instance = object.__new__(Assistant)
    instance.memory = MemoryManager()
    instance.intent_detector = IntentDetector()
    instance.llm = Mock()
    instance.llm.chat.return_value = 'Resposta simulada'
    instance.system_prompt = 'Você é Jarvis.'
    return instance


@pytest.fixture
def client(database, assistant, monkeypatch):
    monkeypatch.setattr(api, 'jarvis', assistant)
    # ASGITransport evita a incompatibilidade do TestClient antigo com httpx 0.28.
    class Client:
        def request(self, method, path, **kwargs):
            async def send():
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app),
                                             base_url='http://testserver', follow_redirects=True) as client:
                    return await client.request(method, path, **kwargs)
            return asyncio.run(send())

        def get(self, path, **kwargs):
            return self.request('GET', path, **kwargs)

        def post(self, path, **kwargs):
            return self.request('POST', path, **kwargs)
    return Client()


def identity(client):
    result = client.post('/session')
    assert result.status_code == 200
    return {'Authorization': 'Bearer ' + result.json()['token']}


def test_chat_continues_and_uses_persistent_memory(client, assistant):
    headers = identity(client)
    first = client.post('/chat', headers=headers, json={'text': 'Meu nome é Samuel'})
    assert first.status_code == 200
    cid = first.json()['conversation_id']
    second = client.post('/chat', headers=headers, json={'text': 'Qual é meu nome?', 'conversation_id': cid})
    assert second.status_code == 200
    assert second.json()['conversation_id'] == cid
    kwargs = assistant.llm.chat.call_args.kwargs
    assert 'Samuel' in kwargs['system_prompt']
    assert kwargs['context'][0]['content'] == 'Meu nome é Samuel'
    assert all(row['content'] != 'Qual é meu nome?' for row in kwargs['context'])


@pytest.mark.parametrize('text', ['Quanto é dois mais dois?', 'O que foi isso?', 'Me ajuda com esse problema', 'Oi, explique gravidade'])
def test_questions_are_not_swallowed(assistant, database, text):
    uid = database.ensure_user('test')
    cid = database.ensure_conversation(uid)
    assert assistant.process_message(text, user_id=uid, conversation_id=cid) == 'Resposta simulada'
    assistant.llm.chat.assert_called_once()


def test_greeting_is_saved(assistant, database):
    uid = database.ensure_user('test')
    cid = database.ensure_conversation(uid)
    assert 'Olá!' in assistant.process_message('Oi!', user_id=uid, conversation_id=cid)
    assert len(database.get_conversation_history(uid, cid)) == 2
    assistant.llm.chat.assert_not_called()


def test_cannot_access_other_identity(client):
    a, b = identity(client), identity(client)
    cid = client.post('/chat', headers=a, json={'text': 'Oi'}).json()['conversation_id']
    assert client.post('/chat', headers=b, json={'text': 'continue', 'conversation_id': cid}).status_code == 404
    assert client.post('/chat', headers=b, json={'text': 'continue', 'user_id': 1}).status_code == 422
    assert client.post('/remember', headers=a, params={'key': 'secret', 'value': 'only A'}).status_code == 200
    assert client.get('/recall/secret', headers=b).json()['status'] == 'not_found'
    assert client.get('/recall/secret', headers=a).json()['value'] == 'only A'
    assert client.post('/feedback', headers=b, json={'session_id': str(cid), 'rating': 5}).status_code == 404


@pytest.mark.parametrize('path', ['/stats', '/recall/secret', '/feedback/stats'])
def test_private_endpoints_require_identity(client, path):
    assert client.get(path).status_code == 401
    assert client.get(path, headers={'Authorization': 'Bearer invented'}).status_code == 401


def test_feedback_validation_and_isolated_stats(client):
    a, b = identity(client), identity(client)
    cid = client.post('/chat', headers=a, json={'text': 'Oi'}).json()['conversation_id']
    assert client.post('/feedback', headers=a, json={'session_id': str(cid), 'rating': 6}).status_code == 422
    assert client.post('/feedback', headers=a, json={'session_id': str(cid), 'rating': 5}).status_code == 200
    assert client.get('/stats', headers=a).json()['total_feedbacks'] == 1
    assert client.get('/stats', headers=b).json()['total_feedbacks'] == 0
    assert client.get('/stats', headers=a).json()['total_conversations'] == 1


def test_empty_message_does_not_create_conversation(client):
    headers = identity(client)
    assert client.post('/chat', headers=headers, json={'text': '   '}).status_code == 422
    assert client.get('/stats', headers=headers).json()['total_conversations'] == 0


def test_assistant_claims_are_not_saved_as_user_preferences(assistant, database):
    uid = database.ensure_user('test')
    cid = database.ensure_conversation(uid)
    memory = assistant.memory.bind(uid, cid)
    memory.add_message('assistant', 'Meu nome é Jarvis e gosto de café')
    assert database.get_stats(uid)['total_memories'] == 0


def test_frontend_assets_and_health(client, monkeypatch):
    assert client.get('/').status_code == 200
    assert client.get('/static/script.js').status_code == 200
    monkeypatch.setattr(api, 'jarvis', None)
    assert client.get('/health').status_code == 503
