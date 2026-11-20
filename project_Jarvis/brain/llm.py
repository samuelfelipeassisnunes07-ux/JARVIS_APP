# brain/llm.py
import requests
import json
import threading
from typing import Optional, List, Dict, Union, Any
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _normalize_ollama_model_name(model_name: Optional[str]) -> str:
    """Normaliza nomes do Ollama, tratando `nome` e `nome:latest` como o mesmo modelo."""
    if model_name is None:
        return ""
    model_name = str(model_name).strip()
    if not model_name:
        return ""
    if ":" in model_name:
        return model_name.rsplit(":", 1)[0]
    return model_name


class OllamaLLM:
    """Interface com modelos rodando via Ollama - Suporte a múltiplos modelos."""
    
    def __init__(self, chat_model: Optional[str] = None, code_model: Optional[str] = None, base_url: Optional[str] = None):
        # Modelos para diferentes propósitos
        self.chat_model = chat_model or settings.get("llm.chat_model", "phi3:mini")
        self.code_model = code_model or settings.get("llm.code_model", "jarvis-coder")
        self.base_url = base_url or settings.get("llm.base_url", "http://localhost:11434")
        
        # Configurações gerais
        self.temperature = settings.get("llm.temperature", 0.7)
        self.max_tokens = settings.get("llm.max_tokens", 2000)
        
        # Configurações específicas
        self.chat_config = settings.get("llm.chat", {})
        self.code_config = settings.get("llm.code", {})
        self._inference_slots = threading.Semaphore(
            int(settings.get("llm.max_concurrent_requests", 2))
        )
        
        # Verifica disponibilidade dos modelos
        self._check_models()
    
    def _check_models(self):
        """Verifica se os modelos existem localmente."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                available_models = [m["name"] for m in response.json().get("models", [])]
                available_model_names = {_normalize_ollama_model_name(name) for name in available_models}
                normalized_chat_model = _normalize_ollama_model_name(self.chat_model)
                normalized_code_model = _normalize_ollama_model_name(self.code_model)
                
                # Verifica modelo de chat
                if normalized_chat_model not in available_model_names:
                    logger.warning(f"Modelo de chat '{self.chat_model}' não encontrado.")
                    logger.info(f"Para instalar: ollama pull {self.chat_model}")
                else:
                    logger.info(f"✅ Modelo de chat '{self.chat_model}' disponível.")
                
                # Verifica modelo de código
                if normalized_code_model not in available_model_names:
                    logger.warning(f"Modelo de código '{self.code_model}' não encontrado.")
                    logger.info(f"Para instalar: ollama pull {self.code_model}")
                else:
                    logger.info(f"✅ Modelo de código '{self.code_model}' disponível.")
                
                # Mostra modelos disponíveis se algum estiver faltando
                if normalized_chat_model not in available_model_names or normalized_code_model not in available_model_names:
                    logger.info(f"Modelos disponíveis: {available_models}")
            else:
                logger.error(f"Erro ao conectar ao Ollama: {response.status_code}")
        except Exception as e:
            logger.error(f"Falha na conexão com Ollama: {e}")
    
    def _get_model_for_task(self, code_mode: bool = False) -> str:
        """Retorna o modelo apropriado baseado na tarefa."""
        return self.code_model if code_mode else self.chat_model
    
    def _get_config_for_task(self, code_mode: bool = False) -> Dict:
        """Retorna as configurações apropriadas para a tarefa."""
        if code_mode:
            return {
                "temperature": self.code_config.get("temperature", 0.3),
                "num_predict": self.code_config.get("max_tokens", 4096),
                "top_k": self.code_config.get("top_k", 40),
                "top_p": self.code_config.get("top_p", 0.9),
                "repeat_penalty": self.code_config.get("repeat_penalty", 1.1),
            }
        else:
            # Configuração especial para phi3:mini
            if "phi3" in self.chat_model:
                return {
                    "temperature": 0.7,
                    "num_predict": 250,  
                    "top_k": 20,
                    "top_p": 0.9,
                    "repeat_penalty": 1.2  # Evita repetições
                }
            
            # Outros modelos de conversa
            return {
                "temperature": self.chat_config.get("temperature", 0.8),
                "num_predict": self.chat_config.get("max_tokens", 1000),
                "top_k": 50,
                "top_p": 0.95,
                "repeat_penalty": self.chat_config.get("repeat_penalty", 1.1)
            }
    
    def _get_system_prompt_for_task(self, code_mode: bool = False) -> str:
        """Retorna o system prompt apropriado para a tarefa."""
        if code_mode:
            return """Você é JARVIS, o assistente pessoal do usuário.
Seu nome é JARVIS.
Nunca se identifique como Claude, ChatGPT, Qwen, Gemini, Grok ou qualquer outro assistente.
Se perguntarem seu nome, responda: "Sou JARVIS."
Forneça código limpo, bem documentado e eficiente.
Explique suas soluções de forma clara e didática.
Sempre inclua exemplos de uso quando relevante.
Responda em português do Brasil."""
        else:
            return """Você é JARVIS, o assistente pessoal do usuário.
Seu nome é JARVIS.
Nunca se identifique como Claude, ChatGPT, Qwen, Gemini, Grok ou qualquer outro assistente.
Se perguntarem seu nome, responda: "Sou JARVIS."
Responda em português do Brasil.
Responda de forma curta e objetiva.
Nunca repita a mesma frase duas vezes."""
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
            context: Optional[List[Dict[str, str]]] = None, 
            code_mode: bool = False) -> str:
        """
        Gera uma resposta usando o modelo apropriado.
        - code_mode: se True, usa modelo especializado em código
        """
        # Seleciona o modelo baseado na tarefa
        model = self._get_model_for_task(code_mode)
        config = self._get_config_for_task(code_mode)
        
        logger.info(f"🎯 Usando modelo: {model} (modo: {'código' if code_mode else 'conversa'})")
        
        messages = []
        
        # Define o system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": self._get_system_prompt_for_task(code_mode)})
        
        # Adiciona contexto se houver
        if context:
            for msg in context:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Adiciona a mensagem atual
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": config
        }
        
        try:
            logger.debug(f"Enviando requisição para {model}")
            with self._inference_slots:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=600
                )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "").strip()
                
                # Log do tipo de resposta
                if "```" in content:
                    logger.info("📝 Resposta contém bloco de código")
                
                #  Remove linhas duplicadas automaticamente
                lines = list(dict.fromkeys(content.split("\n")))
                content = "\n".join(lines)
                
                return content
            else:
                logger.error(f"Erro na API Ollama: {response.status_code}")
                return f"[Erro ao gerar resposta: código {response.status_code}]"
                
        except requests.exceptions.ConnectionError:
            logger.error("Não foi possível conectar ao Ollama.")
            return "[Erro: Ollama não está acessível. Execute 'ollama serve']"
        except Exception as e:
            logger.exception("Exceção inesperada:")
            return f"[Erro: {e}]"
    
    def generate_code(self, prompt: str, language: Optional[str] = None) -> str:
        """Método específico para geração de código (usa modelo de código)."""
        if language:
            prompt = f"Escreva código em {language} para: {prompt}"
        return self.generate(prompt, code_mode=True)
    
    def explain_code(self, code: str) -> str:
        """Explica um trecho de código (usa modelo de código)."""
        prompt = f"Explique este código em detalhes:\n\n{code}"
        return self.generate(prompt, code_mode=True)
    
    def review_code(self, code: str) -> str:
        """Revisa código e sugere melhorias (usa modelo de código)."""
        prompt = f"Revise este código e sugira melhorias:\n\n{code}"
        return self.generate(prompt, code_mode=True)
    
    def chat(self, prompt: str, context: Optional[List] = None, system_prompt: Optional[str] = None) -> str:
        """Método para conversas gerais (usa modelo de chat)."""
        return self.generate(
            prompt,
            system_prompt=system_prompt,
            context=context,
            code_mode=False,
        )
