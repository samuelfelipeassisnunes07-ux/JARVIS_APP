#!/usr/bin/env python3
"""
Ponto de entrada do assistente Jarvis.
Executa a interface de linha de comando com suporte a múltiplos modelos.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from interfaces.cli_interface import CLIInterface
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


def _normalize_ollama_model_name(model_name):
    """Normaliza nomes do Ollama, tratando `nome` e `nome:latest` como o mesmo modelo."""
    if model_name is None:
        return ""
    model_name = str(model_name).strip()
    if not model_name:
        return ""
    if ":" in model_name:
        return model_name.rsplit(":", 1)[0]
    return model_name


def check_ollama_models():
    """Verifica se os modelos necessários estão disponíveis no Ollama."""
    import requests
    
    try:
        response = requests.get(f"{settings.get('llm.base_url')}/api/tags", timeout=10)
        if response.status_code == 200:
            available_models = [m["name"] for m in response.json().get("models", [])]
            available_model_names = {_normalize_ollama_model_name(name) for name in available_models}
            
            # Obtém os modelos configurados
            chat_model = settings.get("llm.chat_model", "mistral:latest")
            code_model = settings.get("llm.code_model", "jarvis-coder")
            
            missing_models = []
            normalized_chat_model = _normalize_ollama_model_name(chat_model)
            normalized_code_model = _normalize_ollama_model_name(code_model)
            
            if normalized_chat_model not in available_model_names:
                missing_models.append(chat_model)
                logger.warning(f"Modelo de chat '{chat_model}' não encontrado!")
            else:
                logger.info(f"✅ Modelo de chat '{chat_model}' disponível")
            
            if normalized_code_model not in available_model_names:
                missing_models.append(code_model)
                logger.warning(f"Modelo de código '{code_model}' não encontrado!")
            else:
                logger.info(f"✅ Modelo de código '{code_model}' disponível")
            
            if missing_models:
                print(f"\n⚠️  Modelos não encontrados: {', '.join(missing_models)}")
                print(f"Modelos disponíveis: {available_models}")
                print("\nPara instalar os modelos necessários, execute:")
                for model in missing_models:
                    print(f"  ollama pull {model}")
                
                response = input("\nDeseja continuar mesmo assim? (s/N): ").lower()
                return response == 's'
            
            return True
        else:
            logger.error(f"Erro ao conectar ao Ollama: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("Não foi possível conectar ao Ollama")
        print("\n❌ Erro: Ollama não está rodando!")
        print("Execute 'ollama serve' em outro terminal antes de iniciar.")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return False

def print_banner():
    """Exibe banner de inicialização com informações dos modelos."""
    chat_model = settings.get("llm.chat_model", "mistral:latest")
    code_model = settings.get("llm.code_model", "jarvis-coder")
    
    banner = f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                     JARVIS ASSISTANT                                 ║
    ║                         v2.0.0                                       ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  🤖 Modelo Chat:  {chat_model:<35}                                   ║
    ║  💻 Modelo Código: {code_model:<34}                                  ║
    ║  🌐 Idioma:        {settings.get('assistant.language', 'pt-BR'):<35} ║
    ║  🔧 Debug:         {str(settings.get('assistant.debug', True)):<35}  ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║  📋 Comandos: /help para lista completa                              ║
    ║  💡 Detecção automática de código ativada!                           ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Função principal."""
    logger.info("=" * 50)
    logger.info("Aplicação Jarvis iniciando...")
    
    # Mostra modelos configurados
    chat_model = settings.get("llm.chat_model", "mistral:latest")
    code_model = settings.get("llm.code_model", "jarvis-coder")
    logger.info(f"Modelo de chat configurado: {chat_model}")
    logger.info(f"Modelo de código configurado: {code_model}")
    
    # Verifica conexão com Ollama
    if not check_ollama_models():
        logger.error("Falha na verificação do Ollama. Encerrando.")
        sys.exit(1)
    
    # Exibe banner
    print_banner()
    
    # Inicia interface CLI
    try:
        cli = CLIInterface()
        logger.info("Interface CLI criada com sucesso")
        cli.start()
    except KeyboardInterrupt:
        logger.info("Interrupção pelo usuário (Ctrl+C)")
        print("\n\n👋 Até mais!")
    except Exception as e:
        logger.critical(f"Erro fatal: {e}", exc_info=True)
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
    finally:
        logger.info("Aplicação finalizada.")
        print("\n✨ Jarvis encerrado.")

if __name__ == "__main__":
    main()
