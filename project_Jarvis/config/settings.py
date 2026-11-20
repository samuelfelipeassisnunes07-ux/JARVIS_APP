# config/settings.py
import os
import yaml
from pathlib import Path
from typing import Any, Optional, Dict
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class Settings:
    """Gerenciador de configurações do assistente."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa as configurações.

        Args:
            config_path: Caminho para o arquivo de configuração YAML
        """
        self.config_path = config_path or Path(__file__).parent / "default_config.yaml"
        self.config = self._load_config()
        self._env_cache = {}

    def _load_config(self) -> Dict:
        """Carrega configurações do arquivo YAML."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config or {}

        except FileNotFoundError:
            # Retorna configuração padrão se arquivo não existir
            return self._get_default_config()

        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão."""
        return {
            "assistant": {
                "name": "Jarvis",
                "language": "pt-BR",
                "debug": True,
            },

            "llm": {
                "provider": "ollama",
                "base_url": "http://localhost:11434",

                # Modelo principal para conversa
                "chat_model": "phi3:latest",

                # Modelo especializado para programação
                "code_model": "jarvis-coder",

                # Modelo para embeddings
                "embedding_model": "nomic-embed-text",

                "temperature": 0.7,
                "max_tokens": 4096,

                # Configurações para conversa
                "chat": {
                    "temperature": 0.8,
                    "max_tokens": 4096,
                },

                # Configurações para código
                "code": {
                    "temperature": 0.3,
                    "max_tokens": 8192,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                },

                # Configurações de embeddings
                "embeddings": {
                    "model": "nomic-embed-text",
                    "dimensions": 768,
                },
            },

            "weather": {
                "enabled": True,
            },

            "memory": {
                "short_term_size": 20,

                "embeddings": {
                    "enabled": True,
                    "similarity_threshold": 0.7,
                    "max_results": 5,
                },
            },
            "database": {
                "url": "",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor da configuração usando notação com pontos.

        Exemplo:
            settings.get("llm.chat_model")
        """

        # Verifica se é variável de ambiente
        env_key = key.upper().replace(".", "_")

        if env_key in os.environ:
            return os.environ[env_key]

        # Navega pela estrutura aninhada
        value = self.config

        for part in key.split("."):
            if isinstance(value, dict):
                value = value.get(part)

                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_model_config(self, model_type: str = "chat") -> Dict:
        """
        Retorna configuração específica para um tipo de modelo.

        Args:
            model_type: "chat", "code" ou "embeddings"
        """

        if model_type == "embeddings":
            return {
                "model": self.get(
                    "llm.embeddings.model",
                    "nomic-embed-text",
                ),
                "dimensions": self.get(
                    "llm.embeddings.dimensions",
                    768,
                ),
            }

        base_config = {
            "temperature": self.get(
                f"llm.{model_type}.temperature",
                self.get("llm.temperature", 0.7),
            ),

            "max_tokens": self.get(
                f"llm.{model_type}.max_tokens",
                self.get("llm.max_tokens", 4096),
            ),
        }

        # Configurações adicionais para modelo de código
        if model_type == "code":
            base_config.update({
                "top_k": self.get(
                    "llm.code.top_k",
                    40,
                ),

                "top_p": self.get(
                    "llm.code.top_p",
                    0.9,
                ),

                "repeat_penalty": self.get(
                    "llm.code.repeat_penalty",
                    1.1,
                ),
            })

        return base_config

    def get_all_models(self) -> Dict[str, str]:
        """Retorna todos os modelos configurados."""
        return {
            "chat": self.get(
                "llm.chat_model",
                "phi3:latest",
            ),

            "code": self.get(
                "llm.code_model",
                "jarvis-coder",
            ),

            "embeddings": self.get(
                "llm.embedding_model",
                "nomic-embed-text",
            ),
        }

    def is_embeddings_enabled(self) -> bool:
        """Verifica se embeddings estão habilitados."""
        return self.get(
            "memory.embeddings.enabled",
            True,
        )

    def get_embeddings_config(self) -> Dict:
        """Retorna configuração completa para embeddings."""
        return {
            "model": self.get(
                "llm.embedding_model",
                "nomic-embed-text",
            ),

            "dimensions": self.get(
                "llm.embeddings.dimensions",
                768,
            ),

            "similarity_threshold": self.get(
                "memory.embeddings.similarity_threshold",
                0.7,
            ),

            "max_results": self.get(
                "memory.embeddings.max_results",
                5,
            ),
        }

    def update(self, key: str, value: Any):
        """
        Atualiza uma configuração em tempo de execução.

        Args:
            key: Chave no formato "section.subsection.key"
            value: Novo valor
        """

        parts = key.split(".")
        target = self.config

        # Navega até o último nível
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}

            target = target[part]

        # Atualiza o valor
        target[parts[-1]] = value

    def reload(self):
        """Recarrega configurações do arquivo."""
        self.config = self._load_config()

    def to_dict(self) -> Dict:
        """Retorna todas as configurações como dicionário."""
        return self.config.copy()


# Instância global de configurações
settings = Settings()


# Função de conveniência para acesso rápido
def get_setting(key: str, default: Any = None) -> Any:
    """Função de conveniência para acessar configurações."""
    return settings.get(key, default)