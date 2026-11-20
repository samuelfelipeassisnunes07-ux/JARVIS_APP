#!/usr/bin/env python3
# scripts/demo_aprendizado.py
"""
Demonstração do sistema de aprendizado do Jarvis.
Mostra como usar todas as 5 etapas implementadas.
"""

import sys
import os
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_banco_dados():
    """Demonstra o uso do banco de dados."""
    print("🔹 Etapa 1: BANCO DE DADOS")
    print("=" * 50)

    try:
        from database.feedback import FeedbackManager

        feedback_manager = FeedbackManager()
        feedback_manager.init_feedback_table()

        # Simula alguns feedbacks
        feedbacks = [
            {
                "session_id": "demo_001",
                "user_question": "Como instalar Python?",
                "assistant_response": "Para instalar Python, vá para python.org e baixe a versão mais recente.",
                "rating": 5,
                "intent": "tutorial_instalacao"
            },
            {
                "session_id": "demo_002",
                "user_question": "Explique POO",
                "assistant_response": "POO significa Programação Orientada a Objetos...",
                "rating": 4,
                "intent": "explicacao_conceito"
            }
        ]

        for fb in feedbacks:
            feedback_manager.save_feedback(**fb)
            print(f"✅ Feedback salvo: {fb['rating']}⭐ - {fb['intent']}")

        # Mostra estatísticas
        stats = feedback_manager.get_feedback_stats()
        print(f"📊 Estatísticas: {stats['general']['total_feedback']} feedbacks")
        print(f"⭐ Média: {stats['general']['avg_rating']:.1f}")

    except Exception as e:
        print(f"❌ Erro no banco: {e}")
    print()

def demo_rag():
    """Demonstra o sistema RAG básico."""
    print("🔍 Etapa 2: RAG (BUSCA SEMÂNTICA)")
    print("=" * 50)

    try:
        from memory.vector_memory import VectorMemory

        vm = VectorMemory()

        # Adiciona alguns conhecimentos
        conhecimentos = [
            "Python é uma linguagem de programação de alto nível",
            "O usuário prefere respostas em português brasileiro",
            "Para instalar pacotes use pip install"
        ]

        print("Adicionando conhecimento...")
        for conhecimento in conhecimentos:
            vm.save_embedding(conhecimento, {"tipo": "conhecimento"})
            print(f"✅ Embedding salvo: {conhecimento[:30]}...")

        # Testa busca
        query = "linguagem de programação"
        print(f"\n🔎 Buscando: '{query}'")
        results = vm.search_similar(query, limit=2)
        for result in results:
            print(f"   📄 Similaridade: {result['similarity']:.3f}")
            print(f"      \"{result['content'][:50]}...\"")

    except Exception as e:
        print(f"❌ Erro no RAG: {e}")
        print("💡 Para RAG avançado, instale: pip install chromadb sentence-transformers")

    # Tenta demonstrar RAG avançado se disponível
    try:
        from memory.advanced_rag import AdvancedRAG
        print("\n🔄 Testando RAG Avançado...")
        rag = AdvancedRAG()
        stats = rag.get_stats()
        print(f"✅ RAG Avançado ativo: {stats['total_documents']} documentos")
    except ImportError as ie:
        print(f"\n⚠️  RAG Avançado não disponível: {ie}")
    except Exception as e:
        print(f"\n❌ Erro no RAG avançado: {e}")

    print()

def demo_roteamento():
    """Demonstra o roteamento inteligente."""
    print("🧠 Etapa 3: ROTEAMENTO INTELIGENTE")
    print("=" * 50)

    try:
        from brain.llm import OllamaLLM

        llm = OllamaLLM()

        print("📋 Modelos configurados:")
        print(f"   Chat: {llm.chat_model}")
        print(f"   Código: {llm.code_model}")
        print(f"   Temperatura: {llm.temperature}")

        # Testa roteamento
        tarefas = [
            ("conversa normal", False),
            ("escrever código", True)
        ]

        for tarefa, is_code in tarefas:
            modelo = llm._get_model_for_task(code_mode=is_code)
            print(f"📝 Tarefa '{tarefa}' → Modelo: {modelo}")

    except Exception as e:
        print(f"❌ Erro no roteamento: {e}")
    print()

def demo_feedback():
    """Demonstra o sistema de feedback."""
    print("👍 Etapa 4: SISTEMA DE FEEDBACK")
    print("=" * 50)

    try:
        from database.feedback import FeedbackManager

        feedback_manager = FeedbackManager()

        # Mostra estatísticas
        stats = feedback_manager.get_feedback_stats()
        print("📊 Estatísticas:")
        print(f"   Total: {stats['general']['total_feedback']}")
        print(f"   Média: {stats['general']['avg_rating']:.1f}")

        if stats['rating_distribution']:
            print("   Por estrelas:")
            for rating, count in sorted(stats['rating_distribution'].items()):
                print(f"   {rating}⭐: {count}")

    except Exception as e:
        print(f"❌ Erro no feedback: {e}")
    print()

def demo_fine_tuning():
    """Demonstra o sistema de fine-tuning."""
    print("🧪 Etapa 5: FINE-TUNING")
    print("=" * 50)

    print("📚 Pipeline de fine-tuning disponível em: tools/fine_tuning.py")
    print("⚙️  Requer bibliotecas adicionais:")
    print("   pip install torch transformers peft datasets")
    print()
    print("🚀 Para executar:")
    print("   from tools.fine_tuning import run_fine_tuning_pipeline")
    print("   run_fine_tuning_pipeline(min_rating=4)")
    print()

def main():
    """Executa todas as demonstrações."""
    print("🤖 JARVIS - DEMONSTRAÇÃO DO SISTEMA DE APRENDIZADO")
    print("=" * 60)
    print()

    # Executa demonstrações
    demo_banco_dados()
    time.sleep(1)

    demo_rag()
    time.sleep(1)

    demo_roteamento()
    time.sleep(1)

    demo_feedback()
    time.sleep(1)

    demo_fine_tuning()

    print("🎉 Demonstração concluída!")
    print()
    print("💡 Para usar o Jarvis completo:")
    print("1. Instale dependências: pip install -r requirements.txt")
    print("2. Execute: python api.py")
    print("3. Abra: http://localhost:8080")
    print("4. Teste e dê feedback para melhorar!")

if __name__ == "__main__":
    main()

def demo_banco_dados():
    """Demonstra o uso do banco de dados."""
    print("🔹 Etapa 1: BANCO DE DADOS")
    print("=" * 50)

    try:
        from database.feedback import FeedbackManager

        feedback_manager = FeedbackManager()
        feedback_manager.init_feedback_table()

        # Simula alguns feedbacks
        feedbacks = [
            {
                "session_id": "demo_001",
                "user_question": "Como instalar Python?",
                "assistant_response": "Para instalar Python, vá para python.org e baixe a versão mais recente.",
                "rating": 5,
                "intent": "tutorial_instalacao"
            },
            {
                "session_id": "demo_002",
                "user_question": "Explique POO",
                "assistant_response": "POO significa Programação Orientada a Objetos...",
                "rating": 4,
                "intent": "explicacao_conceito"
            }
        ]

        for fb in feedbacks:
            feedback_manager.save_feedback(**fb)
            print(f"✅ Feedback salvo: {fb['rating']}⭐ - {fb['intent']}")

        # Mostra estatísticas
        stats = feedback_manager.get_feedback_stats()
        print(f"📊 Estatísticas: {stats['general']['total_feedback']} feedbacks")
        print(f"⭐ Média: {stats['general']['avg_rating']:.1f}")

    except Exception as e:
        print(f"❌ Erro no banco: {e}")
    print()
    feedbacks = [
        {
            "session_id": "demo_001",
            "user_question": "Como instalar Python?",
            "assistant_response": "Para instalar Python, vá para python.org e baixe a versão mais recente.",
            "rating": 5,
            "intent": "tutorial_instalacao"
        },
        {
            "session_id": "demo_002",
            "user_question": "Explique POO",
            "assistant_response": "POO significa Programação Orientada a Objetos...",
            "rating": 4,
            "intent": "explicacao_conceito"
        }
    ]

    for fb in feedbacks:
        feedback_manager.save_feedback(**fb)
        print(f"✅ Feedback salvo: {fb['rating']}⭐ - {fb['intent']}")

    # Mostra estatísticas
    stats = feedback_manager.get_feedback_stats()
    print(f"📊 Estatísticas: {stats['general']['total_feedback']} feedbacks")
    print(f"⭐ Média: {stats['general']['avg_rating']:.1f}")
    print()

def demo_rag():
    """Demonstra o sistema RAG avançado."""
    print("🔍 Etapa 2: RAG (BUSCA SEMÂNTICA)")
    print("=" * 50)

    rag = AdvancedRAG()

    # Adiciona conhecimento
    conhecimentos = [
        "Python é uma linguagem de programação de alto nível, interpretada e orientada a objetos.",
        "O usuário prefere explicações em português brasileiro com exemplos práticos.",
        "Para instalar bibliotecas Python, use: pip install nome_da_biblioteca",
        "O Jarvis deve sempre responder de forma educada e útil.",
        "Quando o usuário pede código, forneça exemplos comentados e explicações."
    ]

    print("Adicionando conhecimento à base...")
    for conhecimento in conhecimentos:
        doc_id = rag.add_document(conhecimento, {"tipo": "conhecimento_base"})
        print(f"✅ Documento adicionado: {doc_id[:8]}...")

    # Testa busca
    queries = [
        "como instalar bibliotecas python",
        "linguagem de programação",
        "responder educadamente"
    ]

    for query in queries:
        print(f"\n🔎 Buscando: '{query}'")
        results = rag.search_similar(query, n_results=2)
        for result in results:
            print(f"   📄 Similaridade: {result['similarity']:.3f}")
            print(f"      \"{result['content'][:100]}...\"")
    # Recupera contexto para uma pergunta
    pergunta = "Como programar em Python?"
    contexto = rag.retrieve_context(pergunta, max_tokens=500)
    print(f"\n📝 Contexto recuperado para '{pergunta}':")
    print(f"'{contexto[:200]}...'")
    print()

def demo_feedback():
    """Demonstra o sistema de feedback."""
    print("👍 Etapa 4: SISTEMA DE FEEDBACK")
    print("=" * 50)

    feedback_manager = FeedbackManager()

    # Mostra estatísticas atuais
    stats = feedback_manager.get_feedback_stats()
    print("📊 Estatísticas atuais:")
    print(f"   Total de feedbacks: {stats['general']['total_feedback']}")
    print(f"⭐ Média: {stats['general']['avg_rating']:.1f}")
    if stats['rating_distribution']:
        print("   Distribuição por estrelas:")
        for rating, count in sorted(stats['rating_distribution'].items()):
            print(f"   {rating}⭐: {count}")

    # Mostra feedback recente
    recent = feedback_manager.get_recent_feedback(limit=3)
    if recent:
        print("\n📝 Feedbacks recentes:")
        for fb in recent:
            print(f"   {fb['rating']}⭐: {fb['user_question'][:50]}...")

    print()

def demo_fine_tuning():
    """Demonstra o sistema de fine-tuning."""
    print("🧪 Etapa 5: FINE-TUNING")
    print("=" * 50)

    print("⚠️  ATENÇÃO: Fine-tuning requer GPU e dados suficientes")
    print("Para executar o fine-tuning completo:")
    print()
    print("from tools.fine_tuning import run_fine_tuning_pipeline")
    print("run_fine_tuning_pipeline(min_rating=4)")
    print()

    # Mostra configuração
    config = FineTuningConfig()
    print("⚙️  Configuração atual:")
    print(f"   Modelo base: {config.model_name}")
    print(f"   Épocas: {config.num_epochs}")
    print(f"   Batch size: {config.batch_size}")
    print(f"   Taxa de aprendizado: {config.learning_rate}")
    print(f"   LoRA r: {config.lora_r}")
    print(f"   Usar QLoRA: {config.use_qlora}")
    print()

def demo_roteamento():
    """Demonstra o roteamento inteligente."""
    print("🧠 Etapa 3: ROTEAMENTO INTELIGENTE")
    print("=" * 50)

    try:
        llm = OllamaLLM()

        # Testa diferentes tipos de tarefa
        tarefas = [
            ("Olá, como vai?", "conversa_geral"),
            ("def fibonacci(n):", "codigo_programacao"),
            ("Instale o numpy", "comando_sistema")
        ]

        for tarefa, tipo in tarefas:
            modelo = llm._get_model_for_task(code_mode=("codigo" in tipo))
            config = llm._get_config_for_task(code_mode=("codigo" in tipo))
            print(f"📝 Tarefa: '{tarefa}'")
            print(f"   Tipo: {tipo}")
            print(f"   Modelo: {modelo}")
            print(f"   Temperatura: {config.get('temperature', 'N/A')}")
            print()

    except Exception as e:
        print(f"❌ Erro no roteamento: {e}")
        print("Certifique-se de que o Ollama está rodando")
        print()

def main():
    """Executa todas as demonstrações."""
    print("🤖 JARVIS - DEMONSTRAÇÃO DO SISTEMA DE APRENDIZADO")
    print("=" * 60)
    print()

    # Executa demonstrações
    demo_banco_dados()
    time.sleep(1)

    demo_rag()
    time.sleep(1)

    demo_roteamento()
    time.sleep(1)

    demo_feedback()
    time.sleep(1)

    demo_fine_tuning()

    print("🎉 Demonstração concluída!")
    print()
    print("Para usar na prática:")
    print("1. Execute: python api.py")
    print("2. Abra: http://localhost:8080 (interface web)")
    print("3. Teste o chatbot e dê feedback!")
    print("4. Quando tiver dados suficientes, rode o fine-tuning")

if __name__ == "__main__":
    main()