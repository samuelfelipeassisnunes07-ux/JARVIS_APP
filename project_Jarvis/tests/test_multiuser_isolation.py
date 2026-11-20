from concurrent.futures import ThreadPoolExecutor
import os

import pytest
from sqlalchemy import text

from database.connection import engine
from database.db import Database

pytestmark = pytest.mark.skipif(
    os.getenv('JARVIS_TEST_MYSQL') != '1',
    reason='Integração MySQL requer JARVIS_TEST_MYSQL=1 e banco de testes dedicado',
)


@pytest.fixture(scope="module")
def database():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"MySQL indisponível para teste de integração: {exc}")
    db = Database()
    db.init_database()
    return db


def test_users_do_not_see_each_others_memories(database):
    user_a = database.ensure_user("test_joao")
    user_b = database.ensure_user("test_pedro")
    conversation_a = database.ensure_conversation(user_a, title="A")
    conversation_b = database.ensure_conversation(user_b, title="B")

    def write_user(user_id, conversation_id, name):
        database.save_memory(user_id, "pref_user_name", name, "preference", 0.9)
        database.save_message(user_id, conversation_id, "user", f"Meu nome é {name}")
        return database.get_conversation_history(user_id, conversation_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(
            lambda values: write_user(*values),
            [(user_a, conversation_a, "João"), (user_b, conversation_b, "Pedro")],
        ))

    assert database.get_memory(user_a, "pref_user_name")["content"] == "João"
    assert database.get_memory(user_b, "pref_user_name")["content"] == "Pedro"
    assert all(row["content"] != "Meu nome é Pedro" for row in first)
    assert all(row["content"] != "Meu nome é João" for row in second)
