# memory/short_memory.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
import json

# Constantes para segurança
MAX_MESSAGE_LENGTH = 2000  # Limite de caracteres por mensagem

class ShortMemory:
    """Gerencia a memória de curto prazo (contexto da conversa)."""
    
    def __init__(self, max_size: int = 20):
        """
        Inicializa a memória curta.
        
        Args:
            max_size: Número máximo de mensagens a manter
        """
        self.max_size = max_size
        self.messages = deque(maxlen=max_size)
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "total_messages": 0,
            "code_messages": 0,
            "truncated_messages": 0  #  contar mensagens truncadas
        }
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Adiciona uma mensagem à memória.
        
        Args:
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
            metadata: Metadados adicionais (intenção, modelo usado, etc)
        """
        # 🚀 Truncar mensagens muito longas por segurança
        original_length = len(content)
        if original_length > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH] + "... [mensagem truncada por segurança]"
            self.metadata["truncated_messages"] += 1
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "original_length": original_length  #  registrar tamanho original
        }
        
        self.messages.append(message)
        self.metadata["total_messages"] += 1
        
        # Conta mensagens relacionadas a código
        if metadata and metadata.get("type") == "code":
            self.metadata["code_messages"] += 1
    
    def get_history(self, as_text: bool = False, last_n: Optional[int] = None) -> List:
        """
        Retorna o histórico de mensagens.
        
        Args:
            as_text: Se True, retorna como texto formatado
            last_n: Número de últimas mensagens (None = todas)
        """
        messages = list(self.messages)
        
        if last_n:
            messages = messages[-last_n:]
        
        if as_text:
            return self._format_as_text(messages)
        
        return messages
    
    def _format_as_text(self, messages: List[Dict]) -> str:
        """Formata as mensagens como texto para contexto."""
        formatted = []
        for msg in messages:
            role = "Usuário" if msg["role"] == "user" else "Assistente"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def get_last_message(self) -> Optional[Dict]:
        """Retorna a última mensagem."""
        if self.messages:
            return self.messages[-1]
        return None
    
    def get_conversation_context(self, max_messages: Optional[int] = None) -> List[Dict]:
        """
        Retorna contexto relevante para o LLM.
        Inclui apenas as últimas mensagens e filtra informações desnecessárias.
        
        Args:
            max_messages: Número máximo de mensagens (usa self.max_size se None)
        """
        # 🚀 MELHORIA: usa o valor configurado se não especificado
        n_messages = max_messages if max_messages is not None else self.max_size
        messages = list(self.messages)[-n_messages:]
        
        context = []
        for msg in messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context
    
    def get_conversation_context_safe(self, max_messages: Optional[int] = None, 
                                      max_total_length: int = 8000) -> List[Dict]:
        """
          Retorna contexto com limite de tamanho total por segurança.
        
        Args:
            max_messages: Número máximo de mensagens
            max_total_length: Tamanho máximo total do contexto em caracteres
        """
        n_messages = max_messages if max_messages is not None else self.max_size
        messages = list(self.messages)[-n_messages:]
        
        context = []
        total_length = 0
        
        for msg in reversed(messages):  # Começa das mais recentes
            msg_content = msg["content"]
            msg_length = len(msg_content)
            
            if total_length + msg_length > max_total_length:
                # Trunca a mensagem atual se necessário
                remaining = max_total_length - total_length
                if remaining > 100:  # Só adiciona se tiver espaço mínimo
                    truncated = msg_content[:remaining] + "..."
                    context.insert(0, {
                        "role": msg["role"],
                        "content": truncated
                    })
                break
            
            context.insert(0, {
                "role": msg["role"],
                "content": msg_content
            })
            total_length += msg_length
        
        return context
    
    def clear(self):
        """Limpa a memória curta."""
        self.messages.clear()
        self.metadata["cleared_at"] = datetime.now().isoformat()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas da memória."""
        return {
            "current_size": len(self.messages),
            "max_size": self.max_size,
            "total_messages": self.metadata["total_messages"],
            "code_messages": self.metadata.get("code_messages", 0),
            "truncated_messages": self.metadata.get("truncated_messages", 0),  
            "created_at": self.metadata["created_at"]
        }
    
    def search_by_content(self, keyword: str) -> List[Dict]:
        """Busca mensagens contendo uma palavra-chave."""
        results = []
        for msg in self.messages:
            if keyword.lower() in msg["content"].lower():
                results.append(msg)
        return results
    
    def get_code_context(self) -> List[Dict]:
        """Retorna apenas mensagens relacionadas a código."""
        code_messages = []
        for msg in self.messages:
            # ⚠️ CORRIGIDO: acesso seguro ao metadata
            if msg.get("metadata", {}).get("type") == "code":
                code_messages.append(msg)
        return code_messages
    
    def get_code_context_safe(self, max_messages: Optional[int] = None) -> List[Dict]:
        """
        Retorna contexto de código com limite de mensagens.
        
        Args:
            max_messages: Número máximo de mensagens de código
        """
        code_messages = self.get_code_context()
        if max_messages:
            code_messages = code_messages[-max_messages:]
        return code_messages
    
    def to_dict(self) -> Dict:
        """Converte para dicionário (para serialização)."""
        return {
            "messages": list(self.messages),
            "metadata": self.metadata,
            "max_size": self.max_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShortMemory':
        """Cria uma instância a partir de um dicionário."""
        memory = cls(max_size=data.get("max_size", 20))
        memory.messages = deque(data.get("messages", []), maxlen=memory.max_size)
        memory.metadata = data.get("metadata", memory.metadata)
        return memory
    
    def get_recent_code_interactions(self, n_last: int = 3) -> List[Dict]:
        """
         Retorna as últimas interações de código.
        Útil para contexto quando o usuário está programando.
        """
        code_messages = []
        for msg in reversed(list(self.messages)):  # Mais recentes primeiro
            if msg.get("metadata", {}).get("type") == "code":
                code_messages.append(msg)
                if len(code_messages) >= n_last:
                    break
        return code_messages
    
    def estimate_tokens(self) -> int:
        """
        Estimativa aproximada de tokens no contexto.
        (Aproximação: 1 token ~= 4 caracteres em português)
        """
        total_chars = sum(len(msg["content"]) for msg in self.messages)
        return total_chars // 4