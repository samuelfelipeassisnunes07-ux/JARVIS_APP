#!/usr/bin/env python3
# scripts/setup_database.py

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import ensure_database_exists
from database.db import Database
from config.settings import settings

def setup_database():
    """Configura e inicializa o banco de dados."""
    print("=" * 50)
    print("Configurando banco de dados do Jarvis")
    print("=" * 50)
    
    print("📁 Banco de dados: MySQL configurado pelo .env")
    
    # Inicializa o banco (cria tabelas se não existirem)
    ensure_database_exists()
    db = Database()
    db.init_database()
    
    print("✅ Tabelas criadas/verificadas com sucesso!")
    
    # Mostra estatísticas iniciais
    stats = db.get_stats()
    print(f"\n📊 Estatísticas:")
    print(f"   - Mensagens: {stats['total_messages']}")
    print(f"   - Memórias: {stats['total_memories']}")
    
    # Teste básico
    print("\n🧪 Testando inserção...")
    user_id = db.ensure_user("setup")
    conversation_id = db.ensure_conversation(user_id, title="Setup")
    test_id = db.save_message(user_id, conversation_id, "system",
                              "Banco de dados inicializado com sucesso!", {"setup": True})
    print(f"   ✅ Mensagem de teste inserida (ID: {test_id})")
    
    print("\n✨ Banco de dados pronto para uso!")
    
    return db

def add_sample_memories(db):
    """Adiciona algumas memórias de exemplo."""
    print("\n📝 Adicionando memórias de exemplo...")
    
    examples = [
        ("pref_user_name", "Usuário", "preference", 0.9),
        ("fact_jarvis", "Jarvis é um assistente pessoal", "fact", 1.0),
        ("info_language", "Idioma principal: Português", "info", 0.8),
    ]
    
    for key, content, mtype, importance in examples:
        db.save_memory(db.ensure_user("setup"), key, content, mtype, importance)
        print(f"   ✅ {key}")
    
    print("   Memórias de exemplo adicionadas!")

def main():
    """Função principal."""
    try:
        db = setup_database()
        
        # Pergunta se quer adicionar exemplos
        response = input("\nDeseja adicionar memórias de exemplo? (s/N): ").lower()
        if response == 's':
            add_sample_memories(db)
        
        print("\n" + "=" * 50)
        print("✅ Configuração concluída com sucesso!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Erro durante a configuração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()